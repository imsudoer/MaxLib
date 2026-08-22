"""
Storage backends for FSM state management.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Union
from .state import State


class BaseStorage(ABC):
    @abstractmethod
    async def set_state(self, chat_id: int, user_id: int, state: Optional[Union[str, State]]) -> None:
        pass

    @abstractmethod
    async def get_state(self, chat_id: int, user_id: int) -> Optional[str]:
        pass

    @abstractmethod
    async def set_data(self, chat_id: int, user_id: int, data: Dict[str, Any]) -> None:
        pass

    @abstractmethod
    async def get_data(self, chat_id: int, user_id: int) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def update_data(self, chat_id: int, user_id: int, **kwargs: Any) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def clear(self, chat_id: int, user_id: int) -> None:
        pass


class MemoryStorage(BaseStorage):
    """
    In-memory FSM storage backend.
    """
    def __init__(self) -> None:
        self._states: Dict[str, Optional[str]] = {}
        self._data: Dict[str, Dict[str, Any]] = {}

    def _key(self, chat_id: int, user_id: int) -> str:
        return f"{chat_id}:{user_id}"

    async def set_state(self, chat_id: int, user_id: int, state: Optional[Union[str, State]]) -> None:
        key = self._key(chat_id, user_id)
        if state is None:
            self._states.pop(key, None)
        else:
            self._states[key] = str(state.state if isinstance(state, State) else state)

    async def get_state(self, chat_id: int, user_id: int) -> Optional[str]:
        return self._states.get(self._key(chat_id, user_id))

    async def set_data(self, chat_id: int, user_id: int, data: Dict[str, Any]) -> None:
        self._data[self._key(chat_id, user_id)] = data.copy()

    async def get_data(self, chat_id: int, user_id: int) -> Dict[str, Any]:
        return self._data.get(self._key(chat_id, user_id), {}).copy()

    async def update_data(self, chat_id: int, user_id: int, **kwargs: Any) -> Dict[str, Any]:
        key = self._key(chat_id, user_id)
        current = self._data.setdefault(key, {})
        current.update(kwargs)
        return current.copy()

    async def clear(self, chat_id: int, user_id: int) -> None:
        key = self._key(chat_id, user_id)
        self._states.pop(key, None)
        self._data.pop(key, None)
