"""
Multi-Account userbot / bot pool management example.
"""
from maxlib import ClientPool, filters, Message

pool = ClientPool()

# Create accounts
pool.create("acc1", phone="+79991112233")
pool.create("acc2", phone="+79992223344")


@pool.on_message(filters.command("all_ping", prefixes="."))
async def handle_ping_for_all(client, message: Message):
    await message.reply(f"🏓 Pong from account **{client.me.name}** (ID: {client.me.id})")


if __name__ == "__main__":
    pool.run()
