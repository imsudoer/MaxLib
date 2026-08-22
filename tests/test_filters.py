"""
Unit tests for MaxLib filter combinators and factories.
"""
import unittest
import asyncio
from unittest.mock import MagicMock
from maxlib.dispatcher.filters import filters
from maxlib.types.message import Message


class TestFilters(unittest.IsolatedAsyncioTestCase):
    async def test_text_filter(self):
        client = MagicMock()
        msg = Message(chatId=123, text="Hello World")

        f_exact = filters.text("Hello World")
        self.assertTrue(await f_exact(client, msg))

        f_case_insens = filters.text("hello world")
        self.assertTrue(await f_case_insens(client, msg))

        f_wrong = filters.text("Goodbye")
        self.assertFalse(await f_wrong(client, msg))

    async def test_command_filter(self):
        client = MagicMock()
        msg1 = Message(chatId=123, text="/start")
        msg2 = Message(chatId=123, text=".ping 123")
        msg3 = Message(chatId=123, text="just regular text")

        f_start = filters.command("start")
        self.assertTrue(await f_start(client, msg1))
        self.assertFalse(await f_start(client, msg2))
        self.assertFalse(await f_start(client, msg3))

        f_ping = filters.command("ping", prefixes=".")
        self.assertTrue(await f_ping(client, msg2))

    async def test_combinators_and_or_not(self):
        client = MagicMock()
        client.me = MagicMock()
        client.me.id = 111

        my_msg = Message(chatId=10, sender=111, text="/help")
        other_msg = Message(chatId=10, sender=222, text="/help")

        f_my_help = filters.me & filters.command("help")
        self.assertTrue(await f_my_help(client, my_msg))
        self.assertFalse(await f_my_help(client, other_msg))

        f_not_me = ~filters.me
        self.assertFalse(await f_not_me(client, my_msg))
        self.assertTrue(await f_not_me(client, other_msg))

        f_or = filters.command("start") | filters.command("help")
        self.assertTrue(await f_or(client, my_msg))


if __name__ == "__main__":
    unittest.main()
