from abc import ABC, abstractmethod
from datetime import datetime, timezone
from enum import Enum
from typing import Self

from discord import Embed, Guild, Member

from bot.luna_api.color import LunaColors


class ActionType(Enum):
    WARN = 1
    TIMEOUT = 2
    KICK = 3
    BAN = 4


def get_embed_title(action_type: ActionType) -> str:
    """
    Returns a title for the embed depending on the ActionType.
    """
    match action_type:
        case ActionType.WARN:
            return "Warning"
        case ActionType.TIMEOUT:
            return "Timeout"
        case ActionType.KICK:
            return "Kick"
        case ActionType.BAN:
            return "Ban"


def get_action_verb(action_type: ActionType) -> str:
    """
    Returns a verb in the past tense for the given ActionType, to be used in embed descriptions.
    (ie.: 'has been [warned]', 'has been [timed out]', etc.)
    """
    match action_type:
        case ActionType.WARN:
            return "warned"
        case ActionType.TIMEOUT:
            return "timed out"
        case ActionType.KICK:
            return "kicked"
        case ActionType.BAN:
            return "banned"


class EmbedProvider(ABC):
    def __init__(self, actor: Member, target: Member, guild: Guild) -> None:
        self.actor = actor
        self.target = target
        self.guild = guild

    @classmethod
    @abstractmethod
    def with_context(cls, guild: Guild, actor: Member, target: Member) -> Self: ...

    @abstractmethod
    def get_feedback_embed(
        self,
        action_type: ActionType,
        message: str,
    ) -> Embed:
        """
        Returns a feedback embed, which is sent to the person running the command.
        """
        ...

    @abstractmethod
    def get_action_embed(self, action_type: ActionType, message: str) -> Embed:
        """
        Returns an action embed, which is sent to the person being acted upon. (usually through DMs)
        """
        ...

    @abstractmethod
    def get_log_embed(self, action_type: ActionType, message: str) -> Embed:
        """
        Returns a log embed, which is sent to the moderation logging channel
        """
        ...


class EmbedProviderImpl(EmbedProvider):
    def __init__(self, actor: Member, target: Member, guild: Guild) -> None:
        super().__init__(actor, target, guild)

    def _get_embed_base(self, action_type: ActionType) -> Embed:
        e = Embed(title=get_embed_title(action_type), color=LunaColors.PRIMARY)
        e.set_thumbnail(
            url=self.guild.icon.url if self.guild.icon is not None else None
        )
        e.timestamp = datetime.now(tz=timezone.utc)
        return e

    def get_feedback_embed(
        self,
        action_type: ActionType,
        message: str,
    ) -> Embed:
        e = self._get_embed_base(action_type)
        e.description = f"{self.actor.mention} has been {get_action_verb(action_type)} by {self.target.mention} in the guild {self.guild.name}."
        e.add_field(name="Reason", value=message)
        return e

    def get_action_embed(self, action_type: ActionType, message: str) -> Embed:
        e = self._get_embed_base(action_type)
        e.description = f"You have been {get_action_verb(action_type)} in the guild {self.guild.name}."
        e.add_field(name="Reason", value=message)
        return e

    def get_log_embed(
        self, action_type: ActionType, message: str, is_undoing: bool = False
    ) -> Embed:
        e = self._get_embed_base(action_type)
        e.description = f"{self.actor.mention} has {'un' if is_undoing else ''} {get_action_verb(action_type)} {self.target.mention}."
        e.add_field(name="Moderator", value=self.actor.mention)
        e.add_field(name="Target", value=self.target.mention)
        e.add_field(name="Reason", value=message)
        return e
    
    @classmethod
    def with_context(cls, guild: Guild, actor: Member, target: Member) -> Self:
        return cls(actor, target, guild)
