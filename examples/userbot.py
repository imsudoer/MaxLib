"""
Modern Userbot example with formatting, reactions, and commands.
"""
import asyncio
from maxlib import MaxClient, filters, Message

client = MaxClient("me")


@client.on_message(filters.me & filters.command("ping", prefixes="."))
async def ping_handler(client: MaxClient, message: Message):
    msg = await message.reply("🏓 Pong!")
    await asyncio.sleep(1)
    await msg.edit("🔥 **MaxLib is blazing fast!**")
    await msg.react("🔥")


@client.on_message(filters.me & filters.command("format", prefixes="."))
async def format_demo(client: MaxClient, message: Message):
    text = (
        "✨ **Rich Formatting Demo:**\n"
        "• **Жирный текст** (`**bold**`)\n"
        "• _Курсив_ (`_italic_`)\n"
        "• __Подчеркнутый__ (`__underline__`)\n"
        "• ~~Зачеркнутый~~ (`~~strike~~`)\n"
        "• `Моноширинный код`\n"
        "• ||Спойлер скрытый|| (`||spoiler||`)\n"
        "• [Ссылка на MAX](https://max.ru)\n"
    )
    await message.reply(text)


@client.on_message(filters.me & filters.command("react", prefixes="."))
async def react_handler(client: MaxClient, message: Message):
    if message.reply_to_message_id:
        await client.set_reaction(message.chat_id, message.reply_to_message_id, "❤️")
        await message.delete()


if __name__ == "__main__":
    client.run()
