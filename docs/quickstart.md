# Quick Start

This guide will walk you through installing MaxLib and building your first working bot.

---

## 1. Installation

Requires Python 3.9 or higher.

```bash
pip install -U maxlib
```

The package automatically installs all necessary dependencies:
- `msgpack` — binary serialization
- `lz4` — packet payload compression and decompression
- `aiohttp` — asynchronous HTTP streaming for media upload and download
- `websockets` — WebSocket transport support (optional web fallback)

For optional Zstandard compression support:
```bash
pip install zstandard
```

---

## 2. First Script: Echo Bot

Create a file named `bot.py`:

```python
from maxlib import MaxClient, filters, Message

# Initialize a client instance with session name 'my_bot'
client = MaxClient("my_bot")


# Connection established event callback
@client.on_connect
async def on_connect():
    print(f"Connected successfully! Account: {client.me.name} (ID: {client.me.id})")


# Command handler for /start
@client.on_message(filters.command("start"))
async def handle_start(client: MaxClient, message: Message):
    await message.reply(
        "Hello! I am a bot built with MaxLib.\n"
        "Send me any text message and I will echo it back."
    )


# Message handler for incoming text messages (ignoring self-sent messages)
@client.on_message(~filters.me & filters.text)
async def handle_echo(client: MaxClient, message: Message):
    await message.reply(f"You said: {message.text}")


if __name__ == "__main__":
    # Start the event loop and client
    client.run()
```

---

## 3. Launch and Authentication

Run your script via the terminal:

```bash
python bot.py
```

On initial execution:
1. The client checks for an existing `my_bot.session` file.
2. If absent, it interactively prompts for your phone number:
   ```
   Enter phone number (+7...): +79991234567
   ```
3. The server sends an SMS or in-app verification code. Enter it:
   ```
   Enter SMS/Push Code: 123456
   ```
4. The client saves the authentication token and randomized device profile to `my_bot.session`.
5. On all subsequent runs, the client logs in automatically without manual code entry.
