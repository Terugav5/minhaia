# discord_bot/views/queue_view.py

import discord
from discord.ext import commands
from sqlalchemy.orm import Session
from database.database import get_db
from database.models import Queue, QueuePlayer, User, Match, MatchTeamPlayer
import asyncio


def get_queue_buttons(queue_type: str) -> list[discord.ui.Button]:
    """Gera os botões corretos com base no tipo de fila."""
    buttons = []
    if "1v1" in queue_type:
        buttons.extend(
            [
                discord.ui.Button(
                    label="Gelo Infinito",
                    style=discord.ButtonStyle.primary,
                    custom_id=f"join_queue:ice",
                ),
                discord.ui.Button(
                    label="Gelo Normal",
                    style=discord.ButtonStyle.secondary,
                    custom_id=f"join_queue:normal",
                ),
            ]
        )
    elif "2v2" in queue_type or "3v3" in queue_type or "4v4" in queue_type:
        buttons.extend(
            [
                discord.ui.Button(
                    label="Entrar",
                    style=discord.ButtonStyle.success,
                    custom_id=f"join_queue:default",
                ),
                discord.ui.Button(
                    label="Full UMP XM8",
                    style=discord.ButtonStyle.blurple,
                    custom_id=f"join_queue:ump_xm8",
                ),
            ]
        )
    elif "Tático" in queue_type:
        buttons.append(
            discord.ui.Button(
                label="Entrar",
                style=discord.ButtonStyle.success,
                custom_id="join_queue:default",
            )
        )
    elif "Misto" in queue_type:
        if "2v2" in queue_type:
            buttons.append(
                discord.ui.Button(label="1 Emu", style=discord.ButtonStyle.primary, custom_id="join_queue:1_emu")
            )
        elif "3v3" in queue_type:
            buttons.extend([
                discord.ui.Button(label="1 Emu", style=discord.ButtonStyle.primary, custom_id="join_queue:1_emu"),
                discord.ui.Button(label="2 Emu", style=discord.ButtonStyle.secondary, custom_id="join_queue:2_emu")
            ])
        elif "4v4" in queue_type:
            buttons.extend([
                discord.ui.Button(label="1 Emu", style=discord.ButtonStyle.primary, custom_id="join_queue:1_emu"),
                discord.ui.Button(label="2 Emu", style=discord.ButtonStyle.secondary, custom_id="join_queue:2_emu"),
                discord.ui.Button(label="3 Emu", style=discord.ButtonStyle.blurple, custom_id="join_queue:3_emu")
            ])

    buttons.append(
        discord.ui.Button(
            label="Sair", style=discord.ButtonStyle.danger, custom_id="leave_queue"
        )
    )
    return buttons


def get_queue_size(queue_type: str) -> int:
    """Determina o tamanho da equipe com base no tipo de fila."""
    if "1v1" in queue_type:
        return 1
    if "2v2" in queue_type:
        return 2
    if "3v3" in queue_type:
        return 3
    if "4v4" in queue_type:
        return 4
    return 0


class QueueView(discord.ui.View):
    def __init__(self, bot: commands.Bot, queue_type: str):
        super().__init__(timeout=None)
        self.bot = bot
        self.queue_type = queue_type
        for button in get_queue_buttons(queue_type):
            self.add_item(button)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        # Deferir a resposta para evitar "A interação falhou"
        await interaction.response.defer(ephemeral=True)

        custom_id = interaction.data.get("custom_id")
        if custom_id and custom_id.startswith("join_queue"):
            await self.handle_join(interaction)
        elif custom_id == "leave_queue":
            await self.handle_leave(interaction)

        return False # Impede o processamento adicional

    async def on_timeout(self) -> None:
        # A view não terá timeout
        pass

    async def handle_join(self, interaction: discord.Interaction):
        db: Session = next(get_db())
        try:
            queue = (
                db.query(Queue)
                .filter(Queue.channel_id == interaction.channel.id)
                .first()
            )
            if not queue:
                await interaction.followup.send("Fila não encontrada.", ephemeral=True)
                return

            # Verificar se o usuário já está na fila
            existing_player = (
                db.query(QueuePlayer)
                .filter(
                    QueuePlayer.queue_id == queue.id,
                    QueuePlayer.user_id == interaction.user.id,
                )
                .first()
            )
            if existing_player:
                await interaction.followup.send(
                    "Você já está na fila.", ephemeral=True
                )
                return

            # Adicionar usuário à fila
            db_user = (
                db.query(User).filter(User.discord_id == interaction.user.id).first()
            )
            if not db_user:
                db_user = User(discord_id=interaction.user.id)
                db.add(db_user)
                db.commit()
                db.refresh(db_user)

            new_player = QueuePlayer(queue_id=queue.id, user_id=db_user.id)
            db.add(new_player)
            db.commit()

            await self.update_queue_embed(interaction, db)

        finally:
            db.close()

    async def handle_leave(self, interaction: discord.Interaction):
        db: Session = next(get_db())
        try:
            queue = (
                db.query(Queue)
                .filter(Queue.channel_id == interaction.channel.id)
                .first()
            )
            if not queue:
                await interaction.followup.send("Fila não encontrada.", ephemeral=True)
                return

            # Remover usuário da fila
            player_to_remove = (
                db.query(QueuePlayer)
                .join(User)
                .filter(
                    QueuePlayer.queue_id == queue.id,
                    User.discord_id == interaction.user.id,
                )
                .first()
            )

            if player_to_remove:
                db.delete(player_to_remove)
                db.commit()
                await self.update_queue_embed(interaction, db)
            else:
                await interaction.followup.send(
                    "Você não está na fila.", ephemeral=True
                )
        finally:
            db.close()

    async def update_queue_embed(
        self, interaction: discord.Interaction, db: Session
    ):
        queue = (
            db.query(Queue).filter(Queue.channel_id == interaction.channel.id).first()
        )
        if not queue:
            return

        players = (
            db.query(User)
            .join(QueuePlayer)
            .filter(QueuePlayer.queue_id == queue.id)
            .all()
        )
        mentions = [f"<@{user.discord_id}>" for user in players]
        queue_size = get_queue_size(self.queue_type)
        total_slots = queue_size * 2

        embed = discord.Embed(
            title=f"Fila para {self.queue_type}",
            description=(
                "**Jogadores na Fila:**\n"
                + ("\n".join(mentions) if mentions else "Ninguém na fila ainda.")
                + f"\n\n`{len(players)}/{total_slots}`"
            ),
            color=discord.Color.dark_purple(),
        )
        message = await interaction.channel.fetch_message(queue.message_id)
        await message.edit(embed=embed)

        if len(players) == total_slots:
            await self.start_match(interaction, db, players, queue)

    async def start_match(
        self,
        interaction: discord.Interaction,
        db: Session,
        players: list[User],
        queue: Queue,
    ):
        # Dividir jogadores em times
        team1_users = players[: len(players) // 2]
        team2_users = players[len(players) // 2 :]

        # Criar canal privado para a partida
        category = interaction.channel.category
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(
                read_messages=False
            ),
            **{
                interaction.guild.get_member(p.discord_id): discord.PermissionOverwrite(
                    read_messages=True
                )
                for p in players
            },
        }
        match_channel = await category.create_text_channel(
            name=f"partida-{queue.queue_type}", overwrites=overwrites
        )

        # Criar a partida no banco de dados
        new_match = Match(
            guild_id=interaction.guild.id,
            channel_id=match_channel.id,
            message_id=0,  # Será atualizado depois
            status="pending",
        )
        db.add(new_match)
        db.commit()
        db.refresh(new_match)

        # Adicionar jogadores à partida no banco de dados
        for user in team1_users:
            db.add(
                MatchTeamPlayer(
                    match_id=new_match.id, user_id=user.id, team_number=1
                )
            )
        for user in team2_users:
            db.add(
                MatchTeamPlayer(
                    match_id=new_match.id, user_id=user.id, team_number=2
                )
            )
        db.commit()

        # Enviar embed de confirmação
        team1_mentions = [f"<@{u.discord_id}>" for u in team1_users]
        team2_mentions = [f"<@{u.discord_id}>" for u in team2_users]
        embed = discord.Embed(
            title="Partida Pronta!",
            description=(
                "Ambos os times precisam confirmar para continuar.\n\n"
                f"**Time 1:** {', '.join(team1_mentions)}\n"
                f"**Time 2:** {', '.join(team2_mentions)}"
            ),
            color=discord.Color.blurple(),
        )
        confirmation_view = ConfirmationView(self.bot, new_match.id)
        message = await match_channel.send(
            content=f"{', '.join(team1_mentions)} vs {', '.join(team2_mentions)}",
            embed=embed,
            view=confirmation_view,
        )
        new_match.message_id = message.id
        db.commit()

        # Limpar a embed da fila original, resetando a view
        original_message = await interaction.channel.fetch_message(queue.message_id)
        embed = discord.Embed(
            title=f"Fila para {self.queue_type}",
            description="Clique em um dos botões para entrar na fila.",
            color=discord.Color.dark_purple(),
        )
        await original_message.edit(embed=embed, view=QueueView(self.bot, self.queue_type))

        # Limpar os jogadores da fila do banco de dados
        db.query(QueuePlayer).filter(QueuePlayer.queue_id == queue.id).delete(synchronize_session=False)
        db.commit()


class ConfirmationView(discord.ui.View):
    def __init__(self, bot: commands.Bot, match_id: int):
        super().__init__(timeout=300)
        self.bot = bot
        self.match_id = match_id

    @discord.ui.button(
        label="Confirmar", style=discord.ButtonStyle.success, custom_id="confirm_match"
    )
    async def confirm_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.defer()
        db: Session = next(get_db())
        try:
            player = (
                db.query(MatchTeamPlayer)
                .join(User)
                .filter(
                    MatchTeamPlayer.match_id == self.match_id,
                    User.discord_id == interaction.user.id,
                )
                .first()
            )
            if not player:
                await interaction.followup.send(
                    "Você não está nesta partida.", ephemeral=True
                )
                return

            player.confirmed = True
            db.commit()
            await interaction.followup.send(
                f"{interaction.user.mention} confirmou a partida!"
            )

            # Verificar se todos confirmaram
            all_players = (
                db.query(MatchTeamPlayer)
                .filter(MatchTeamPlayer.match_id == self.match_id)
                .all()
            )
            if all(p.confirmed for p in all_players):
                await self.on_both_confirmed(interaction, db)
        finally:
            db.close()

    @discord.ui.button(
        label="Encerrar", style=discord.ButtonStyle.danger, custom_id="cancel_match"
    )
    async def cancel_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.send_message(
            "Partida encerrada. O canal será deletado em 5 segundos."
        )
        await asyncio.sleep(5)
        await interaction.channel.delete()
        db: Session = next(get_db())
        try:
            match = db.query(Match).filter(Match.id == self.match_id).first()
            if match:
                db.delete(match)
                db.commit()
        finally:
            db.close()

    async def on_both_confirmed(self, interaction: discord.Interaction, db: Session):
        from utils.qr_generator import generate_qr_code
        from database.models import Mediator
        from sqlalchemy.sql.expression import func

        # Buscar PIX de um mediador aleatório
        mediator = db.query(Mediator).order_by(func.random()).first()
        if not mediator or not mediator.pix_key:
            await interaction.followup.send(
                "Nenhum mediador com chave PIX encontrada para gerar o pagamento."
            )
            return

        # Gerar QR Code
        # A lógica para gerar a payload do QR Code (BR Code) é complexa.
        # Por simplicidade, usaremos apenas a chave PIX.
        qr_buffer = generate_qr_code(mediator.pix_key)
        qr_file = discord.File(qr_buffer, filename="pix_qr_code.png")

        embed = discord.Embed(
            title="Pagamento via PIX",
            description="Realize o pagamento escaneando o QR Code abaixo.",
            color=discord.Color.gold(),
        )
        embed.set_image(url="attachment://pix_qr_code.png")
        await interaction.followup.send(embed=embed, file=qr_file)
