# MaxLib

Asynchronous Python framework for the MAX messenger (max.ru / OneMe).

I started writing this library for my own automation scripts and userbots in MAX. The API design and structure are heavily inspired by **Pyrogram**, so anyone familiar with building Telegram userbots can pick it up in minutes.

Under the hood, MaxLib connects directly to the official mobile binary protocol (`api.oneme.ru:443`, TLS, MsgPack, LZ4/Zstandard compression) rather than the limited web WebSocket API. This grants access to all messenger methods, real-time push events, and superior network performance.

---

## Installation

Requires Python 3.9 or higher.

```bash
pip install -U maxlib
```

Core dependencies (`msgpack`, `lz4`, `aiohttp`, `websockets`) are installed automatically.
For optional Zstandard compression support:

```bash
pip install zstandard
```

---

## Quick Start

### Simple Echo Bot

```python
from maxlib import MaxClient, filters, Message

client = MaxClient("my_bot")


@client.on_connect
async def on_connect():
    print(f"Logged in as: {client.me.name} (ID: {client.me.id})")


@client.on_message(filters.command("start"))
async def start_handler(client: MaxClient, message: Message):
    await message.reply(
        "Hello! I am a bot powered by MaxLib.\n"
        "Send me any text, and I will repeat it."
    )


@client.on_message(~filters.me & filters.text)
async def echo_handler(client: MaxClient, message: Message):
    await message.reply(f"You said: {message.text}")


if __name__ == "__main__":
    client.run()
```

On first run, the script will prompt for your phone number and SMS verification code in the terminal. The session credentials and device profile will be saved to `my_bot.session` for automatic login on subsequent runs.

---

## Authentication and Sessions

### Login via Phone Number
If no session file exists, `client.run()` or `await client.start()` will automatically start the interactive console login flow:

```python
from maxlib import MaxClient

client = MaxClient("session_name")
client.run()
```

### Login with Pre-existing Token
If you already possess a valid profile auth token:

```python
client = MaxClient("session_name", token="your_auth_token_here")
client.run()
```

### CLI Terminal Tools
You can authenticate and inspect sessions directly from your terminal:

```bash
# Interactive login and session creation
python -m maxlib login -s my_session -p +79991234567

# Display account profile information
python -m maxlib info -s my_session

# Launch an interactive Python REPL with connected client
python -m maxlib shell -s my_session
```

---

## Event Handling and Filters

Event routing works identically to Pyrogram. Attach the `@client.on_message(filter)` decorator to your async function:

```python
@client.on_message(filters.command("ping"))
async def ping_handler(client, message):
    await message.reply("pong")
```

### Available Filters

- `filters.all` / `filters.any` — matches all incoming messages.
- `filters.me` — messages sent by the authenticated account (useful for userbots).
- `filters.private` — 1-on-1 private direct messages.
- `filters.group` — group chat messages.
- `filters.channel` — channel messages.
- `filters.reply` — messages that reply to another message.
- `filters.media` — messages containing any media attachment.
- `filters.photo` — photo messages.
- `filters.document` — document/file messages.
- `filters.voice` — voice notes.
- `filters.video` — video messages.
- `filters.sticker` — stickers.
- `filters.command("cmd", prefixes=["/", "."])` — command trigger with prefixes.
- `filters.text("text")` or `filters.text(["text1", "text2"])` — exact string matching.
- `filters.regex(r"^test\s+(\d+)$")` — regex pattern matching.
- `filters.sender(user_id)` — messages from specific user IDs.
- `filters.chat(chat_id)` — messages from specific chat IDs.
- `filters.state(MyState)` — FSM conversation state filter.

### Combining Filters

Combine filters using standard Python bitwise logical operators:
- `&` — AND
- `|` — OR
- `~` — NOT
- `^` — XOR

```python
# Match userbot command .ping sent only by yourself in group chats
@client.on_message(filters.me & filters.group & filters.command("ping", prefixes="."))
async def handle_ping(client, message):
    await message.reply("Pong!")

# Match incoming private messages with greeting
@client.on_message(~filters.me & filters.private & (filters.text("hello") | filters.text("hi")))
async def handle_hello(client, message):
    await message.reply("Hello there!")
```

---

## Bound Methods

All models (`Message`, `Chat`, `User`) are bound to the client instance, allowing direct action calls:

### Message Object

```python
# Reply with quote
await message.reply("Reply text")

# Send message to same chat without quote
await message.answer("Chat message")

# Reply with photo or document
await message.reply_photo("path/to/pic.jpg", caption="Photo description")
await message.reply_document("report.pdf")

# Edit sent message
await message.edit("Updated text")

# Delete message
await message.delete()

# Add emoji reaction
await message.react("❤️")

# Remove reaction
await message.remove_reaction()

# Forward message to another chat
await message.forward(to_chat_id=12345678)

# Download media attachment
path = await message.download(destination="downloads/")
```

### Chat Object

```python
chat = message.chat

# Send messages to chat
await chat.send_message("Hello chat")
await chat.send_photo("banner.png", caption="Announcement")

# Pin / Unpin chat
await chat.pin()
await chat.unpin()

# Message history
history = await chat.get_history(limit=50)

# Leave chat
await chat.leave()

# Chat membership
members = await chat.get_members()
await chat.add_members([11223344])
await chat.remove_member(11223344)

# Update title
await chat.set_title("New Group Title")
```

### User Object

```python
user = await message.get_sender()

print(user.name)        # Full display name
print(user.first_name)  # First name
print(user.phone)       # Phone number
print(user.id)          # User ID

# Send direct message
await user.send_message("Direct message text")

# Manage contact
await user.add_contact()
await user.block()
await user.unblock()

# Markdown mention link
mention = user.mention()  # [Name](user:123456)
```

---

## Text Formatting (Markdown V2 and HTML)

MaxLib automatically parses Markdown V2 or HTML syntax into native binary MAX elements with accurate UTF-16 offset calculations:

### Markdown V2 (default)

```python
await message.reply(
    "**Bold text**\n"
    "_Italic text_\n"
    "__Underlined text__\n"
    "~~Strikethrough~~\n"
    "`Inline code`\n"
    "```python\nprint('Code block')\n```\n"
    "||Hidden spoiler||\n"
    "[MAX Website](https://max.ru)"
)
```

### HTML

```python
await client.send_html(
    chat_id,
    "<b>Bold</b>, <i>italic</i>, <u>underline</u>, <s>strike</s>, "
    "<code>code</code>, <tg-spoiler>spoiler</tg-spoiler>, "
    "<a href='https://max.ru'>Link</a>"
)
```

---

## Media Upload and Download

Chunked streaming with real-time transfer progress callbacks:

```python
from maxlib import MaxClient, UploadProgress, DownloadProgress

client = MaxClient("me")


def upload_cb(prog: UploadProgress):
    print(f"Uploading: {prog.percentage:.1f}% | Speed: {prog.speed / 1024:.1f} KB/s")


def download_cb(prog: DownloadProgress):
    print(f"Downloading: {prog.percentage:.1f}%")


# Send photo
await client.send_photo(
    chat_id=123456,
    photo="photo.jpg",
    caption="My photo",
    progress_callback=upload_cb
)

# Download attachment from message
@client.on_message(filters.media)
async def handle_media(client, message):
    file_path = await client.download_media(message, progress_callback=download_cb)
    print(f"Saved to: {file_path}")
```

---

## Asynchronous Iterators (Pagination)

Iterate through long histories and dialog lists effortlessly:

```python
# Iterate through chat history
async for msg in client.iter_history(chat_id=123456, limit=150):
    print(f"{msg.time}: {msg.text}")

# Iterate through all dialogs
async for chat in client.iter_dialogs(limit=50):
    print(f"Chat: {chat.title or chat.id}")
```

---

## Finite State Machine (FSM / Multi-Step Dialogs)

Construct step-by-step surveys and conversation flows:

```python
from maxlib import MaxClient, filters, Message, State, StatesGroup

client = MaxClient("survey_bot")


class Form(StatesGroup):
    name = State()
    age = State()


@client.on_message(filters.command("start"))
async def cmd_start(client: MaxClient, message: Message):
    await client.fsm.set_state(message.chat_id, message.sender_id, Form.name)
    await message.reply("Hello! What is your name?")


@client.on_message(filters.state(Form.name))
async def step_name(client: MaxClient, message: Message):
    await client.fsm.update_data(message.chat_id, message.sender_id, name=message.text)
    await client.fsm.set_state(message.chat_id, message.sender_id, Form.age)
    await message.reply(f"Nice to meet you, {message.text}! How old are you?")


@client.on_message(filters.state(Form.age))
async def step_age(client: MaxClient, message: Message):
    if not message.text.isdigit():
        return await message.reply("Please enter your age as a number.")

    data = await client.fsm.update_data(message.chat_id, message.sender_id, age=int(message.text))
    await client.fsm.clear(message.chat_id, message.sender_id)
    await message.reply(f"Form completed!\nName: {data['name']}\nAge: {data['age']}")


client.run()
```

---

## Multi-Account Management (`ClientPool`)

Manage multiple client accounts concurrently in a single process:

```python
from maxlib import ClientPool, filters, Message

pool = ClientPool()
pool.create("acc1", phone="+79991112233")
pool.create("acc2", phone="+79992223344")


@pool.on_message(filters.command("ping", prefixes="."))
async def on_ping(client, message: Message):
    await message.reply(f"Pong from {client.me.name} (ID: {client.me.id})")


if __name__ == "__main__":
    pool.run()
```

---

## Detailed Documentation

Complete guide files are available in the [docs/](docs/) directory:
- [Quick Start](docs/quickstart.md)
- [Authentication and Sessions](docs/authentication.md)
- [Dispatcher and Filters](docs/dispatcher-and-filters.md)
- [Bound Methods](docs/bound-methods.md)
- [Text Formatting](docs/formatting.md)
- [Media](docs/media.md)
- [FSM (State Machine)](docs/fsm.md)
- [Pagination and Iterators](docs/pagination.md)
- [Multi-Account (ClientPool)](docs/multi-account.md)
- [Protocol Internals](docs/protocol-internals.md)
- [Opcodes Reference](docs/opcodes-reference.md)

---

## License

GNU General Public License v3.0 (GPL-3.0). Free for use, extension, and modification.
