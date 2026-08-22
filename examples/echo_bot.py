"""
Simple Echo Bot example using MaxLib.
"""
from maxlib import MaxClient, filters, Message

client = MaxClient("my_bot")


@client.on_message(filters.command("start"))
async def start_handler(client: MaxClient, message: Message):
    await message.reply(
        "👋 **Привет! Я бот на MaxLib.**\n"
        "Отправь мне любое сообщение, и я повторю его!"
    )


@client.on_message(~filters.me)
async def echo_handler(client: MaxClient, message: Message):
    await message.reply(f"Вы написали: {message.text}")


if __name__ == "__main__":
    client.run()
