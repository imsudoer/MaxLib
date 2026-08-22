"""
Advanced composable filter system for MAX messenger event handling.
"""
import re
from typing import Any, Callable, Iterable, List, Optional, Pattern, Set, Union, TYPE_CHECKING
from .fsm.state import State, StatesGroup

if TYPE_CHECKING:
    from ..client.client import MaxClient
    from ..types.message import Message


FilterCallable = Callable[..., Any]


class Filter:
    """
    Base filter class supporting logical operators:
    - & (AND)
    - | (OR)
    - ~ (NOT)
    - ^ (XOR)
    """
    def __init__(self, func: Optional[FilterCallable] = None, name: str = "") -> None:
        self.func = func
        self.name = name or (func.__name__ if hasattr(func, "__name__") else self.__class__.__name__)

    async def __call__(self, client: "MaxClient", update: Any) -> bool:
        if self.func is None:
            return True
        try:
            # Handle functions taking (update) or (client, update)
            res = self.func(client, update) if self._takes_two_args(self.func) else self.func(update)
            if hasattr(res, "__await__"):
                res = await res
            return bool(res)
        except Exception:
            return False

    @staticmethod
    def _takes_two_args(fn: Callable[..., Any]) -> bool:
        import inspect
        try:
            sig = inspect.signature(fn)
            params = [p for p in sig.parameters.values() if p.kind in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD)]
            return len(params) >= 2
        except Exception:
            return False

    def __and__(self, other: "Filter") -> "AndFilter":
        return AndFilter(self, other)

    def __or__(self, other: "Filter") -> "OrFilter":
        return OrFilter(self, other)

    def __invert__(self) -> "NotFilter":
        return NotFilter(self)

    def __xor__(self, other: "Filter") -> "XorFilter":
        return XorFilter(self, other)

    def __repr__(self) -> str:
        return f"Filter({self.name})"


class AndFilter(Filter):
    def __init__(self, *filters: Filter) -> None:
        self.filters = list(filters)
        super().__init__(name=f"({' & '.join(f.name for f in self.filters)})")

    async def __call__(self, client: "MaxClient", update: Any) -> bool:
        for f in self.filters:
            if not await f(client, update):
                return False
        return True


class OrFilter(Filter):
    def __init__(self, *filters: Filter) -> None:
        self.filters = list(filters)
        super().__init__(name=f"({' | '.join(f.name for f in self.filters)})")

    async def __call__(self, client: "MaxClient", update: Any) -> bool:
        for f in self.filters:
            if await f(client, update):
                return True
        return False


class NotFilter(Filter):
    def __init__(self, target_filter: Filter) -> None:
        self.target_filter = target_filter
        super().__init__(name=f"(~{target_filter.name})")

    async def __call__(self, client: "MaxClient", update: Any) -> bool:
        return not await self.target_filter(client, update)


class XorFilter(Filter):
    def __init__(self, filter1: Filter, filter2: Filter) -> None:
        self.f1 = filter1
        self.f2 = filter2
        super().__init__(name=f"({filter1.name} ^ {filter2.name})")

    async def __call__(self, client: "MaxClient", update: Any) -> bool:
        r1 = await self.f1(client, update)
        r2 = await self.f2(client, update)
        return r1 != r2


def create(func: FilterCallable, name: str = "") -> Filter:
    """Helper to create a custom filter from a function or lambda."""
    return Filter(func, name=name or "<custom>")


# --- Built-in Filter Definitions ---

class _AllFilter(Filter):
    def __init__(self) -> None:
        super().__init__(name="all")

    async def __call__(self, client: "MaxClient", update: Any) -> bool:
        return True


class _MeFilter(Filter):
    def __init__(self) -> None:
        super().__init__(name="me")

    async def __call__(self, client: "MaxClient", update: Any) -> bool:
        sender_id = getattr(update, "sender_id", getattr(update, "sender", None))
        if sender_id is not None and client.me:
            return sender_id == client.me.id
        return False


class _PrivateFilter(Filter):
    def __init__(self) -> None:
        super().__init__(name="private")

    async def __call__(self, client: "MaxClient", update: Any) -> bool:
        chat = getattr(update, "chat", None)
        if chat:
            return chat.type == "DIALOG"
        return False


class _GroupFilter(Filter):
    def __init__(self) -> None:
        super().__init__(name="group")

    async def __call__(self, client: "MaxClient", update: Any) -> bool:
        chat = getattr(update, "chat", None)
        if chat:
            return chat.type == "CHAT"
        return False


class _ChannelFilter(Filter):
    def __init__(self) -> None:
        super().__init__(name="channel")

    async def __call__(self, client: "MaxClient", update: Any) -> bool:
        chat = getattr(update, "chat", None)
        if chat:
            return getattr(chat, "is_channel", False)
        return False


class _ReplyFilter(Filter):
    def __init__(self) -> None:
        super().__init__(name="reply")

    async def __call__(self, client: "MaxClient", update: Any) -> bool:
        return bool(getattr(update, "reply_to_message_id", None))


class _MediaFilter(Filter):
    def __init__(self) -> None:
        super().__init__(name="media")

    async def __call__(self, client: "MaxClient", update: Any) -> bool:
        attaches = getattr(update, "attaches", None)
        return bool(attaches)


class _PhotoFilter(Filter):
    def __init__(self) -> None:
        super().__init__(name="photo")

    async def __call__(self, client: "MaxClient", update: Any) -> bool:
        return getattr(update, "photo", None) is not None


class _VideoFilter(Filter):
    def __init__(self) -> None:
        super().__init__(name="video")

    async def __call__(self, client: "MaxClient", update: Any) -> bool:
        return getattr(update, "video", None) is not None


class _AudioFilter(Filter):
    def __init__(self) -> None:
        super().__init__(name="audio")

    async def __call__(self, client: "MaxClient", update: Any) -> bool:
        return getattr(update, "audio", None) is not None


class _VoiceFilter(Filter):
    def __init__(self) -> None:
        super().__init__(name="voice")

    async def __call__(self, client: "MaxClient", update: Any) -> bool:
        return getattr(update, "voice", None) is not None


class _DocumentFilter(Filter):
    def __init__(self) -> None:
        super().__init__(name="document")

    async def __call__(self, client: "MaxClient", update: Any) -> bool:
        return getattr(update, "document", None) is not None


class _StickerFilter(Filter):
    def __init__(self) -> None:
        super().__init__(name="sticker")

    async def __call__(self, client: "MaxClient", update: Any) -> bool:
        return getattr(update, "sticker", None) is not None


class _PollFilter(Filter):
    def __init__(self) -> None:
        super().__init__(name="poll")

    async def __call__(self, client: "MaxClient", update: Any) -> bool:
        return getattr(update, "poll", None) is not None


class command(Filter):
    """
    Matches command messages with configurable prefixes (e.g. /start or .ping).
    """
    def __init__(
        self,
        commands: Union[str, Iterable[str]],
        prefixes: Union[str, Iterable[str]] = ("/", "."),
        case_sensitive: bool = False,
    ) -> None:
        self.commands = [commands] if isinstance(commands, str) else list(commands)
        self.prefixes = [prefixes] if isinstance(prefixes, str) else list(prefixes)
        self.case_sensitive = case_sensitive

        if not case_sensitive:
            self.commands = [c.lower() for c in self.commands]

        super().__init__(name=f"command({self.commands})")

    async def __call__(self, client: "MaxClient", update: Any) -> bool:
        text = getattr(update, "text", None)
        if not text:
            return False

        first_word = text.strip().split()[0] if text.strip() else ""
        for prefix in self.prefixes:
            if first_word.startswith(prefix):
                cmd_name = first_word[len(prefix):]
                if not self.case_sensitive:
                    cmd_name = cmd_name.lower()
                if cmd_name in self.commands:
                    return True
        return False


class text(Filter):
    """Matches messages containing exact text strings or lists of texts."""
    def __init__(self, texts: Union[str, Iterable[str]], case_sensitive: bool = False) -> None:
        self.texts = [texts] if isinstance(texts, str) else list(texts)
        self.case_sensitive = case_sensitive
        if not case_sensitive:
            self.texts = [t.lower() for t in self.texts]
        super().__init__(name=f"text({self.texts})")

    async def __call__(self, client: "MaxClient", update: Any) -> bool:
        msg_text = getattr(update, "text", None)
        if not msg_text:
            return False
        compare = msg_text if self.case_sensitive else msg_text.lower()
        return any(t == compare for t in self.texts)


class regex(Filter):
    """Matches message text using regular expressions."""
    def __init__(self, pattern: Union[str, Pattern], flags: int = 0) -> None:
        self.pattern: Pattern = re.compile(pattern, flags) if isinstance(pattern, str) else pattern
        super().__init__(name=f"regex({self.pattern.pattern})")

    async def __call__(self, client: "MaxClient", update: Any) -> bool:
        msg_text = getattr(update, "text", None)
        if not msg_text:
            return False
        match = self.pattern.search(msg_text)
        return match is not None


class sender(Filter):
    """Matches messages from specific user IDs."""
    def __init__(self, user_ids: Union[int, Iterable[int]]) -> None:
        self.user_ids: Set[int] = {user_ids} if isinstance(user_ids, int) else set(user_ids)
        super().__init__(name=f"sender({self.user_ids})")

    async def __call__(self, client: "MaxClient", update: Any) -> bool:
        s_id = getattr(update, "sender_id", getattr(update, "sender", None))
        return s_id in self.user_ids if s_id is not None else False


# Alias for sender filter
user_id = sender


class chat(Filter):
    """Matches messages from specific chat IDs."""
    def __init__(self, chat_ids: Union[int, Iterable[int]]) -> None:
        self.chat_ids: Set[int] = {chat_ids} if isinstance(chat_ids, int) else set(chat_ids)
        super().__init__(name=f"chat({self.chat_ids})")

    async def __call__(self, client: "MaxClient", update: Any) -> bool:
        c_id = getattr(update, "chat_id", None)
        return c_id in self.chat_ids if c_id is not None else False


class state(Filter):
    """Matches messages when the conversation is in a specific FSM state."""
    def __init__(self, target_state: Union[State, StatesGroup, str, None]) -> None:
        self.target_state = target_state
        super().__init__(name=f"state({target_state})")

    async def __call__(self, client: "MaxClient", update: Any) -> bool:
        chat_id = getattr(update, "chat_id", 0)
        user_id = getattr(update, "sender_id", getattr(update, "sender", 0))
        current_state = await client.fsm.get_state(chat_id, user_id)

        if self.target_state is None:
            return current_state is None

        if isinstance(self.target_state, StatesGroup):
            all_group_states = {s.state for s in self.target_state.get_all_states()}
            return current_state in all_group_states

        target_str = self.target_state.state if isinstance(self.target_state, State) else str(self.target_state)
        return current_state == target_str


class FiltersContainer:
    """Namespace container providing all filters in Pyrogram/Aiogram style."""
    all = _AllFilter()
    any = _AllFilter()
    me = _MeFilter()
    private = _PrivateFilter()
    group = _GroupFilter()
    channel = _ChannelFilter()
    reply = _ReplyFilter()
    media = _MediaFilter()
    photo = _PhotoFilter()
    video = _VideoFilter()
    audio = _AudioFilter()
    voice = _VoiceFilter()
    document = _DocumentFilter()
    sticker = _StickerFilter()
    poll = _PollFilter()

    # Factory filters
    command = command
    text = text
    regex = regex
    sender = sender
    user_id = user_id
    chat = chat
    state = state
    create = staticmethod(create)


filters = FiltersContainer()
