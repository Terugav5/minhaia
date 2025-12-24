# discord_bot/views/config_view.py

import discord
from discord.ui import View, Button, Modal, TextInput
from database.database import get_db
from database.models import GuildConfig, Price
from sqlalchemy.orm import Session
from utils.modal_db_decorator import modal_db_session_decorator


class RolesModal(Modal, title="Configuração de Cargos"):
    def __init__(self, guild_id: int):
        super().__init__()
        self.guild_id = guild_id
        db: Session = next(get_db())
        guild_config = (
            db.query(GuildConfig).filter(GuildConfig.guild_id == self.guild_id).first()
        )
        if not guild_config:
            guild_config = GuildConfig(guild_id=self.guild_id)
            db.add(guild_config)
            db.commit()
            db.refresh(guild_config)

        self.analyst_role_input = TextInput(
            label="ID do Cargo de Analista",
            default=str(guild_config.analyst_role_id or ""),
            required=False,
        )
        self.mediator_role_input = TextInput(
            label="ID do Cargo de Mediador",
            default=str(guild_config.mediator_role_id or ""),
            required=False,
        )
        self.support_role_input = TextInput(
            label="ID do Cargo de Suporte",
            default=str(guild_config.support_role_id or ""),
            required=False,
        )

        self.add_item(self.analyst_role_input)
        self.add_item(self.mediator_role_input)
        self.add_item(self.support_role_input)
        db.close()

    @modal_db_session_decorator
    async def on_submit(self, interaction: discord.Interaction, db: Session):
        guild_config = (
            db.query(GuildConfig).filter(GuildConfig.guild_id == self.guild_id).first()
        )

        guild_config.analyst_role_id = (
            int(self.analyst_role_input.value)
            if self.analyst_role_input.value.isdigit()
            else None
        )
        guild_config.mediator_role_id = (
            int(self.mediator_role_input.value)
            if self.mediator_role_input.value.isdigit()
            else None
        )
        guild_config.support_role_id = (
            int(self.support_role_input.value)
            if self.support_role_input.value.isdigit()
            else None
        )

        db.commit()
        await interaction.response.send_message(
            "Cargos configurados com sucesso!", ephemeral=True
        )


class PricesModal(Modal, title="Configuração de Preços"):
    def __init__(self, guild_id: int):
        super().__init__()
        self.guild_id = guild_id
        # Campos para adicionar/remover preços
        self.add_price_type = TextInput(label="Tipo (e.g., 1v1, 2v2)", required=True)
        self.add_price_value = TextInput(label="Valor", required=False)
        self.remove_price_type = TextInput(
            label="Tipo para Remover (e.g., 1v1)", required=False
        )
        self.clear_prices = TextInput(
            label="Limpar Todos os Preços (digite 'sim')", required=False
        )
        self.add_item(self.add_price_type)
        self.add_item(self.add_price_value)
        self.add_item(self.remove_price_type)
        self.add_item(self.clear_prices)

    @modal_db_session_decorator
    async def on_submit(self, interaction: discord.Interaction, db: Session):
        try:
            # Lógica para limpar preços
            if self.clear_prices.value.lower() == "sim":
                db.query(Price).filter(Price.guild_id == self.guild_id).delete()
                await interaction.response.send_message(
                    "Todos os preços foram removidos.", ephemeral=True
                )
                db.commit()
                return

            # Lógica para adicionar preço
            if self.add_price_type.value and self.add_price_value.value:
                price_value = int(self.add_price_value.value)
                new_price = Price(
                    guild_id=self.guild_id,
                    match_type=self.add_price_type.value,
                    price=price_value,
                )
                db.add(new_price)

            # Lógica para remover preço
            if self.remove_price_type.value:
                price_to_remove = (
                    db.query(Price)
                    .filter(
                        Price.guild_id == self.guild_id,
                        Price.match_type == self.remove_price_type.value,
                    )
                    .first()
                )
                if price_to_remove:
                    db.delete(price_to_remove)

            db.commit()
            await interaction.response.send_message(
                "Preços atualizados com sucesso!", ephemeral=True
            )
        except ValueError:
            await interaction.response.send_message(
                "Valor do preço inválido.", ephemeral=True
            )


class LogsModal(Modal, title="Configuração de Canais de Logs"):
    def __init__(self, guild_id: int):
        super().__init__()
        self.guild_id = guild_id
        db: Session = next(get_db())
        guild_config = (
            db.query(GuildConfig).filter(GuildConfig.guild_id == self.guild_id).first()
        )
        if not guild_config:
            guild_config = GuildConfig(guild_id=self.guild_id)
            db.add(guild_config)
            db.commit()
            db.refresh(guild_config)

        self.general_log_channel = TextInput(
            label="ID do Canal de Logs Gerais",
            default=str(guild_config.general_log_channel_id or ""),
            required=False,
        )
        self.matches_log_channel = TextInput(
            label="ID do Canal de Logs de Partidas",
            default=str(guild_config.matches_log_channel_id or ""),
            required=False,
        )
        self.mediator_log_channel = TextInput(
            label="ID do Canal de Logs de Mediadores",
            default=str(guild_config.mediator_log_channel_id or ""),
            required=False,
        )
        self.add_item(self.general_log_channel)
        self.add_item(self.matches_log_channel)
        self.add_item(self.mediator_log_channel)
        db.close()

    @modal_db_session_decorator
    async def on_submit(self, interaction: discord.Interaction, db: Session):
        try:
            guild_config = (
                db.query(GuildConfig)
                .filter(GuildConfig.guild_id == self.guild_id)
                .first()
            )
            guild_config.general_log_channel_id = (
                int(self.general_log_channel.value)
                if self.general_log_channel.value.isdigit()
                else None
            )
            guild_config.matches_log_channel_id = (
                int(self.matches_log_channel.value)
                if self.matches_log_channel.value.isdigit()
                else None
            )
            guild_config.mediator_log_channel_id = (
                int(self.mediator_log_channel.value)
                if self.mediator_log_channel.value.isdigit()
                else None
            )
            db.commit()
            await interaction.response.send_message(
                "Canais de logs atualizados com sucesso!", ephemeral=True
            )


class ConfigView(View):
    def __init__(self, guild_id: int):
        super().__init__(timeout=None)
        self.guild_id = guild_id

    @discord.ui.button(label="Cargos", style=discord.ButtonStyle.primary, row=0)
    async def roles_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        modal = RolesModal(guild_id=self.guild_id)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Valores", style=discord.ButtonStyle.secondary, row=0)
    async def prices_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        modal = PricesModal(guild_id=self.guild_id)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Logs", style=discord.ButtonStyle.secondary, row=1)
    async def logs_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        modal = LogsModal(guild_id=self.guild_id)
        await interaction.response.send_modal(modal)

    @discord.ui.button(
        label="Painel Mediador", style=discord.ButtonStyle.secondary, row=1
    )
    async def mediator_panel_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.send_message(
            "Função em desenvolvimento.", ephemeral=True
        )

    @discord.ui.button(
        label="Embeds Partidas", style=discord.ButtonStyle.secondary, row=2
    )
    async def match_embeds_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.send_message(
            "Função em desenvolvimento.", ephemeral=True
        )

    @discord.ui.button(label="Ticket", style=discord.ButtonStyle.secondary, row=2)
    async def ticket_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.send_message(
            "Função em desenvolvimento.", ephemeral=True
        )

    @discord.ui.button(label="Ranking", style=discord.ButtonStyle.secondary, row=3)
    async def ranking_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.send_message(
            "Função em desenvolvimento.", ephemeral=True
        )
