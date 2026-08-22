"""
Unit tests for Finite State Machine (FSM).
"""
import unittest
from maxlib.dispatcher.fsm import State, StatesGroup, MemoryStorage


class Form(StatesGroup):
    name = State()
    age = State()


class TestFSM(unittest.IsolatedAsyncioTestCase):
    async def test_states_group(self):
        self.assertEqual(Form.name.state, "Form:name")
        self.assertEqual(Form.age.state, "Form:age")
        self.assertIn(Form.name, Form.get_all_states())

    async def test_memory_storage(self):
        storage = MemoryStorage()
        chat_id = 100
        user_id = 200

        # Initial state is None
        self.assertIsNone(await storage.get_state(chat_id, user_id))

        # Set state
        await storage.set_state(chat_id, user_id, Form.name)
        self.assertEqual(await storage.get_state(chat_id, user_id), "Form:name")

        # Set data
        await storage.set_data(chat_id, user_id, {"temp": 123})
        await storage.update_data(chat_id, user_id, name="Ivan")
        data = await storage.get_data(chat_id, user_id)
        self.assertEqual(data["name"], "Ivan")
        self.assertEqual(data["temp"], 123)

        # Clear
        await storage.clear(chat_id, user_id)
        self.assertIsNone(await storage.get_state(chat_id, user_id))
        self.assertEqual(await storage.get_data(chat_id, user_id), {})


if __name__ == "__main__":
    unittest.main()
