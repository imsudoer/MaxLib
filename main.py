"""
Main entry script for MaxLib userbot / bot.
"""
import asyncio
import logging
from maxlib import MaxClient, Message, filters

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

client = MaxClient("me")


@client.on_connect
async def on_connect_handler():
    if client.me:
        print("=" * 50)
        print(f"[*] MaxLib connected successfully!")
        print(f"[*] Account: {client.me.name} (ID: {client.me.id})")
        print(f"[*] Phone:   {client.me.phone}")
        print("=" * 50)


@client.on_message(filters.command("ping", prefixes=(".", "/")))
async def on_ping(client: MaxClient, message: Message):
    msg = await message.reply("🏓 **Pong!**")
    await asyncio.sleep(1)
    await msg.edit("🔥 **MaxLib 3.1.0 — faster, smarter, cooler than vkmax!**")
    await msg.react("🔥")


@client.on_message(filters.command("wtf", prefixes=(".", "/")))
async def on_wtf(client: MaxClient, message: Message):
    m = await client.send_message(message.chat_id, "Этого сообщения скоро не станет... // MaxLib")
    await asyncio.sleep(1)
    m2 = await m.reply("Ответ на исчезающее сообщение")
    await asyncio.sleep(1)
    await m.delete()
    await message.reply("✨ Сообщение удалено, но ответ остался!")


@client.on_message(filters.text(["макс", "max"]))
async def on_max_mention(client: MaxClient, message: Message):
    await message.react("👍")
    await message.reply("👋 Привет! Я работаю на **MaxLib v3.1.0** 🚀")


if __name__ == "__main__":
    client.run()