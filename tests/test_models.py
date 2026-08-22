"""
Unit tests for MaxLib Models and Bound Actions.
"""
import unittest
from unittest.mock import AsyncMock, MagicMock
from maxlib.types import Message, Chat, User, ReactionInfo


class TestModels(unittest.IsolatedAsyncioTestCase):
    async def test_message_bound_methods(self):
        client = MagicMock()
        client.send_message = AsyncMock()
        client.delete_messages = AsyncMock()
        client.set_reaction = AsyncMock()

        msg = Message(client=client, chatId=123, id="999", text="Hello", sender=456)
        self.assertEqual(msg.chat_id, 123)
        self.assertEqual(msg.id, "999")
        self.assertEqual(msg.text, "Hello")

        # Reply
        await msg.reply("Answer")
        client.send_message.assert_called_once_with(123, "Answer", reply_to="999")

        # Delete
        await msg.delete()
        client.delete_messages.assert_called_once_with(123, ["999"], for_me=False)

        # React
        await msg.react("🔥")
        client.set_reaction.assert_called_once_with(123, "999", "🔥")

    def test_reactions_info(self):
        raw = {
            "counters": [{"reaction": "❤️", "count": 5}, {"reaction": "👍", "count": 2}],
            "yourReaction": "❤️",
            "totalCount": 7
        }
        info = ReactionInfo(raw=raw)
        self.assertEqual(info.total_count, 7)
        self.assertEqual(info.your_reaction, "❤️")
        self.assertTrue(info.has_my_reaction())
        self.assertEqual(info.get_count_for("❤️"), 5)
        self.assertEqual(info.get_count_for("👍"), 2)
        self.assertEqual(info.get_count_for("🎉"), 0)


if __name__ == "__main__":
    unittest.main()
