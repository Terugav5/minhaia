# discord_bot/views/config_view.py

import discord
from discord.ui import View, Button, Modal, TextInput, Select
from sqlalchemy.orm import Session
from ..database.database import get_db
from ..database.models import GuildConfig, Price, EmbedConfig, TicketOption
from ..utils.modal_db_decorator import modal_db_session_decorator

# --- MODAL GENÉRICO PARA CONSTRUIR EMBEDS ---

class EmbedBuilderModal(Modal, title="Construtor de Embed"):
    """Um modal genérico para criar ou editar embeds."""
    def __init__(self, db: Session, guild_id: int, embed_type: str):
        super().__init__()
        self.db = db
        self.guild_id = guild_id
        self.embed_type = embed_type  # Ex: "mediator_panel", "Mobile_1v1"

        # Carrega a configuração existente, se houver
        self.existing_config = self.db.query(EmbedConfig).filter_by(
            guild_id=self.guild_id, queue_type=self.embed_type
        ).first()

        self.embed_title = TextInput(
            label="Título da Embed",
            default=self.existing_config.title if self.existing_config else "",
            required=False,
            max_length=256
        )
        self.embed_description = TextInput(
            label="Descrição",
            style=discord.TextStyle.paragraph,
            default=self.existing_config.description if self.existing_config else "",
            required=False,
            max_length=4000
        )
        self.embed_footer = TextInput(
            label="Texto do Rodapé",
            default=self.existing_config.footer if self.existing_config else "",
            required=False,
            max_length=2048
        )
        self.embed_color = TextInput(
            label="Cor (Hex, ex: #00ff00)",
            default=self.existing_config.color if self.existing_config else "",
            required=False
        )
        self.embed_image_url = TextInput(
            label="URL da Imagem Principal",
            default=self.existing_config.image_url if self.existing_config else "",
            required=False
        )

        self.add_item(self.embed_title)
        self.add_item(self.embed_description)
        self.add_item(self.embed_footer)
        self.add_item(self.embed_color)
        self.add_item(self.embed_image_url)

    async def on_submit(self, interaction: discord.Interaction):
        # A lógica de salvar no DB será tratada na view que chama este modal.
        # Aqui, apenas validamos e preparamos os dados.
        color_value = self.embed_color.value
        if color_value and not color_value.startswith("#"):
            color_value = f"#{color_value}"
        try:
            discord.Color.from_str(color_value)
        except ValueError:
            await interaction.response.send_message("O formato da cor hexadecimal é inválido. Use #RRGGBB.", ephemeral=True)
            return

        # Passa os dados de volta para a view. A view que chamou o modal precisa implementar `on_modal_submit`.
        await self.callback(interaction, {
            "title": self.embed_title.value,
            "description": self.embed_description.value,
            "footer": self.embed_footer.value,
            "color": color_value,
            "image_url": self.embed_image_url.value
        })

# --- MODAIS E VIEWS PARA CONFIGURAÇÕES ESPECÍFICAS ---

class RolesModal(Modal, title="Configuração de Cargos"):
    # (código inalterado)
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
    # (código inalterado)
    def __init__(self, guild_id: int):
        super().__init__()
        self.guild_id = guild_id
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
            if self.clear_prices.value.lower() == "sim":
                db.query(Price).filter(Price.guild_id == self.guild_id).delete()
                await interaction.response.send_message(
                    "Todos os preços foram removidos.", ephemeral=True
                )
                db.commit()
                return

            if self.add_price_type.value and self.add_price_value.value:
                price_value = int(self.add_price_value.value)
                new_price = Price(
                    guild_id=self.guild_id,
                    match_type=self.add_price_type.value,
                    price=price_value,
                )
                db.add(new_price)

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
    # (código inalterado)
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

class RankingModal(Modal, title="Configuração do Ranking"):
    def __init__(self, guild_id: int):
        super().__init__()
        self.guild_id = guild_id
        db: Session = next(get_db())
        guild_config = db.query(GuildConfig).filter(GuildConfig.guild_id == self.guild_id).first()
        db.close()

        self.ranking_channel_id = TextInput(
            label="ID do Canal do Ranking",
            default=str(guild_config.ranking_channel_id or ""),
            required=True
        )
        self.add_item(self.ranking_channel_id)

    @modal_db_session_decorator
    async def on_submit(self, interaction: discord.Interaction, db: Session):
        guild_config = db.query(GuildConfig).filter(GuildConfig.guild_id == self.guild_id).first()
        try:
            guild_config.ranking_channel_id = int(self.ranking_channel_id.value)
            db.commit()
            await interaction.response.send_message("Canal de ranking configurado!", ephemeral=True)
        except (ValueError, TypeError):
            await interaction.response.send_message("ID do canal inválido.", ephemeral=True)

class TicketModal(Modal, title="Configuração de Tickets"):
    def __init__(self, guild_id: int):
        super().__init__()
        self.guild_id = guild_id
        db: Session = next(get_db())
        guild_config = db.query(GuildConfig).filter(GuildConfig.guild_id == self.guild_id).first()
        db.close()

        self.ticket_category_id = TextInput(
            label="ID da Categoria para abrir Tickets",
            default=str(guild_config.ticket_category_id or ""),
            required=True,
        )
        self.ticket_channel_id = TextInput(
            label="ID do Canal para postar a embed",
            default=str(guild_config.ticket_channel_id or ""),
            required=True,
        )
        self.ticket_options = TextInput(
            label="Opções do Menu (separadas por vírgula)",
            style=discord.TextStyle.paragraph,
            placeholder="Parcerias, Suporte, Virar Influencer",
            required=True,
        )

        self.add_item(self.ticket_category_id)
        self.add_item(self.ticket_channel_id)
        self.add_item(self.ticket_options)

    @modal_db_session_decorator
    async def on_submit(self, interaction: discord.Interaction, db: Session):
        guild_config = db.query(GuildConfig).filter(GuildConfig.guild_id == self.guild_id).first()
        try:
            guild_config.ticket_category_id = int(self.ticket_category_id.value)
            guild_config.ticket_channel_id = int(self.ticket_channel_id.value)

            # Limpa as opções antigas e adiciona as novas
            db.query(TicketOption).filter(TicketOption.guild_id == self.guild_id).delete()
            options = [opt.strip() for opt in self.ticket_options.value.split(",")]
            for option_label in options:
                if option_label:
                    db.add(TicketOption(guild_id=self.guild_id, label=option_label))

            db.commit()
            await interaction.response.send_message("Configuração de tickets salva!", ephemeral=True)
        except (ValueError, TypeError):
            await interaction.response.send_message("IDs de canal ou categoria inválidos.", ephemeral=True)


# --- VIEW PRINCIPAL DE CONFIGURAÇÃO ---

class ConfigView(View):
    def __init__(self, guild_id: int):
        super().__init__(timeout=None)
        self.guild_id = guild_id
        self.db = next(get_db())

    async def on_modal_submit(self, interaction: discord.Interaction, data: dict):
        """Callback genérico para o EmbedBuilderModal."""
        embed_type = self.current_embed_type

        config = self.db.query(EmbedConfig).filter_by(
            guild_id=self.guild_id, queue_type=embed_type
        ).first()

        if not config:
            config = EmbedConfig(guild_id=self.guild_id, queue_type=embed_type)
            self.db.add(config)

        config.title = data['title']
        config.description = data['description']
        config.footer = data['footer']
        config.color = data['color']
        config.image_url = data['image_url']

        self.db.commit()
        await interaction.response.send_message(f"Embed para '{embed_type}' salva com sucesso!", ephemeral=True)

    @discord.ui.button(label="Cargos", style=discord.ButtonStyle.primary, row=0)
    async def roles_button(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(RolesModal(guild_id=self.guild_id))

    @discord.ui.button(label="Valores", style=discord.ButtonStyle.secondary, row=0)
    async def prices_button(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(PricesModal(guild_id=self.guild_id))

    @discord.ui.button(label="Logs", style=discord.ButtonStyle.secondary, row=1)
    async def logs_button(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(LogsModal(guild_id=self.guild_id))

    @discord.ui.button(label="Painel Mediador", style=discord.ButtonStyle.secondary, row=1)
    async def mediator_panel_button(self, interaction: discord.Interaction, button: Button):
        self.current_embed_type = "mediator_panel"
        modal = EmbedBuilderModal(db=self.db, guild_id=self.guild_id, embed_type=self.current_embed_type)
        modal.callback = self.on_modal_submit
        await interaction.response.send_modal(modal)

    @discord.ui.select(
        placeholder="Selecione o tipo de embed de partida...",
        options=[
            discord.SelectOption(label="Mobile 1v1", value="Mobile_1v1"),
            discord.SelectOption(label="Mobile Times", value="Mobile_Team"),
            discord.SelectOption(label="Emulador 1v1", value="Emulator_1v1"),
            discord.SelectOption(label="Emulador Times", value="Emulator_Team"),
            discord.SelectOption(label="Tático", value="Tactic"),
            discord.SelectOption(label="Misto", value="Mixed"),
        ],
        row=2
    )
    async def match_embeds_select(self, interaction: discord.Interaction, select: Select):
        self.current_embed_type = select.values[0]
        modal = EmbedBuilderModal(db=self.db, guild_id=self.guild_id, embed_type=self.current_embed_type)
        modal.callback = self.on_modal_submit
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Ticket", style=discord.ButtonStyle.secondary, row=3)
    async def ticket_button(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(TicketModal(guild_id=self.guild_id))

    @discord.ui.button(label="Ranking", style=discord.ButtonStyle.secondary, row=3)
    async def ranking_button(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(RankingModal(guild_id=self.guild_id))

    def __del__(self):
        # Garante que a sessão do banco de dados seja fechada quando a view for destruída.
        self.db.close()
