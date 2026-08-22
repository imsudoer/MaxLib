# Multi-Account Management (ClientPool)

When managing userbot fleets, scraping clusters, or multi-tenant bots within a single Python process, use `ClientPool`.

---

## 1. Basic Pool Setup

```python
from maxlib import ClientPool, filters, Message

pool = ClientPool()

# Initialize multiple client instances
pool.create("account_1", phone="+79991112233")
pool.create("account_2", phone="+79994445566")
pool.create("account_3", token="pre_existing_token_here")


# Register handler across ALL clients in the pool
@pool.on_message(filters.command("ping", prefixes="."))
async def handle_ping_all(client, message: Message):
    await message.reply(
        f"Pong!\n"
        f"Account: {client.me.name}\n"
        f"ID: {client.me.id}"
    )


if __name__ == "__main__":
    # Start all accounts concurrently within one event loop
    pool.run()
```

---

## 2. Separate Handlers for Specific Accounts

Access and configure specific accounts by name:

```python
pool = ClientPool()
bot = pool.create("bot_acc")
userbot = pool.create("user_acc")

# Bot-specific handler
@bot.on_message(filters.command("help"))
async def bot_help(client, message):
    await message.reply("Bot Help Documentation")

# Userbot-specific handler
@userbot.on_message(filters.me & filters.command("status", prefixes="."))
async def user_status(client, message):
    await message.reply("Userbot active")

pool.run()
```
