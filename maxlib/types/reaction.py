"""
Reaction models and emoji definitions for MAX messenger.
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional
from .base import BaseObject

EMOJIS = Literal[
    '❤️','👍','👎','🤣','🔥','💯','😍','🎉','⚡',
    '🤩','🤘','😎','🙄','😐','😁','🤪','😉',
    '🤤','😇','😘','🥰','🥳','🌚','🌝','😴',
    '🫠','🤔','🫡','😳','🥱','🐈','🐶','💪',
    '🤞','👋','👏','🤝','👌','🙏','💋','👑',
    '⭐','🍷','🍑','🤷‍♀️','🤷‍♂️','👩‍❤️‍👨','🦄','👻',
    '🗿','👀','👁️','🖤','❤️‍🩹','🛑','⛄','❓',
    '❗️'
]


@dataclass(slots=True)
class ReactionCounter:
    reaction: str
    count: int


class ReactionInfo(BaseObject):
    """
    Detailed reactions statistics on a message.
    """
    def __init__(self, raw: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(raw=raw)
        info = raw or {}
        self.counters: List[ReactionCounter] = [
            ReactionCounter(reaction=c.get("reaction", ""), count=c.get("count", 0))
            for c in info.get("counters", [])
        ]
        self.your_reaction: Optional[str] = info.get("yourReaction")
        self.total_count: int = info.get("totalCount", 0)

    def has_my_reaction(self) -> bool:
        return bool(self.your_reaction)

    def get_count_for(self, emoji: str) -> int:
        for c in self.counters:
            if c.reaction == emoji:
                return c.count
        return 0


# Legacy alias
Reactions = ReactionInfo
Reaction = ReactionCounter
