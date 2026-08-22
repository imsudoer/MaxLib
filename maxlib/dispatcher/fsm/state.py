"""
Finite State Machine (FSM) states and states groups for MaxLib.
"""
from typing import Optional, Set


class State:
    """
    Represents a specific dialog step / state.
    """
    def __init__(self, state: Optional[str] = None, group_name: Optional[str] = None) -> None:
        self._state = state
        self._group_name = group_name

    @property
    def state(self) -> Optional[str]:
        if self._group_name and self._state:
            return f"{self._group_name}:{self._state}"
        return self._state

    def __str__(self) -> str:
        return self.state or ""

    def __repr__(self) -> str:
        return f"<State '{self.state}'>"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, State):
            return self.state == other.state
        if isinstance(other, str):
            return self.state == other
        return False

    def __hash__(self) -> int:
        return hash(self.state)


class StatesGroupMeta(type):
    def __new__(mcs, name, bases, namespace):
        cls = super().__new__(mcs, name, bases, namespace)
        states: Set[State] = set()
        for attr_name, val in namespace.items():
            if isinstance(val, State):
                val._state = attr_name
                val._group_name = name
                states.add(val)
        cls._states = states
        return cls


class StatesGroup(metaclass=StatesGroupMeta):
    """
    Base class for declaring grouped FSM states.

    Example:
    ```python
    class Registration(StatesGroup):
        name = State()
        age = State()
        confirm = State()
    ```
    """
    _states: Set[State] = set()

    @classmethod
    def get_all_states(cls) -> Set[State]:
        return cls._states
