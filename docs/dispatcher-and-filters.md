# Dispatcher and Filters

The Dispatcher handles network frame routing and executes registered event handlers according to matching filters.

---

## 1. Registering Handlers

Handlers are registered using client decorators:

```python
# Incoming new messages
@client.on_message(filters.text)
async def message_handler(client, message):
    pass

# Message edits
@client.on_edited_message()
async def edit_handler(client, message):
    pass

# Message deletions
@client.on_deleted_message()
async def delete_handler(client, event):
    print(f"Deleted messages {event.message_ids} in chat {event.chat_id}")

# Message reactions
@client.on_reaction()
async def reaction_handler(client, event):
    print(f"Reaction in chat {event.chat_id} on message {event.message_id}")

# User typing indicator
@client.on_typing()
async def typing_handler(client, event):
    print(f"User {event.user_id} is typing in chat {event.chat_id}")

# Presence updates (online / offline)
@client.on_presence()
async def presence_handler(client, event):
    print(f"User {event.user_id} online: {event.is_online}")

# Raw protocol packets by opcode
@client.on_raw_packet(opcode=128)
async def raw_packet_handler(client, packet):
    pass
```

---

## 2. Filter Reference

All filters are accessible via the `filters` module:

```python
from maxlib import filters
```

### Basic Filters

| Filter | Description |
| :--- | :--- |
| `filters.all` / `filters.any` | Matches all messages unconditionally |
| `filters.me` | Matches messages sent by the authenticated client account |
| `filters.private` | Matches 1-on-1 private direct messages |
| `filters.group` | Matches group chat messages |
| `filters.channel` | Matches channel broadcast messages |
| `filters.reply` | Matches messages that reply to another message |

### Media Filters

| Filter | Description |
| :--- | :--- |
| `filters.media` | Matches messages with any media attachment |
| `filters.photo` | Matches messages with a photo |
| `filters.video` | Matches messages with a video |
| `filters.audio` | Matches messages with an audio track |
| `filters.voice` | Matches messages with a voice recording |
| `filters.document` | Matches messages with a file or document |
| `filters.sticker` | Matches messages with a sticker |
| `filters.poll` | Matches messages with a poll |

### Parametric Filters

```python
# Commands (defaults to prefixes '/' and '.')
filters.command("start")
filters.command(["start", "help"], prefixes=["/", "!", "."])

# Exact text matching (case-insensitive by default)
filters.text("hello")
filters.text(["hello", "hi", "hey"])

# Regular expressions
filters.regex(r"^/ban\s+(\d+)$")

# Sender user ID filter
filters.sender(41424820)
filters.sender([111111, 222222, 333333])

# Chat ID filter
filters.chat(12345678)
filters.chat([10001, 10002])

# FSM state filter
filters.state(RegistrationState.name)
```

---

## 3. Logical Operators

Combine filters using standard Python bitwise operators:

- `&` (AND) — both filters must return True
- `|` (OR) — at least one filter must return True
- `~` (NOT) — inverts filter condition
- `^` (XOR) — exactly one filter must return True

### Examples:

```python
# Command .mute sent only by myself in group chats
@client.on_message(filters.me & filters.group & filters.command("mute", prefixes="."))
async def mute_cmd(client, message):
    pass

# Photo or document in private chat from user with ID 12345
@client.on_message(filters.private & filters.sender(12345) & (filters.photo | filters.document))
async def media_from_user(client, message):
    pass
```

---

## 4. Custom Filters

Create a custom filter on the fly with `filters.create`:

```python
# Filter messages longer than 100 characters
long_text = filters.create(lambda message: len(message.text) > 100, name="long_text")


@client.on_message(long_text)
async def handle_long(client, message):
    await message.reply("Message is too long.")
```

Or subclass `Filter`:

```python
from maxlib import Filter


class KeywordFilter(Filter):
    def __init__(self, keyword: str):
        self.keyword = keyword.lower()
        super().__init__(name=f"keyword({keyword})")

    async def __call__(self, client, message) -> bool:
        return self.keyword in (message.text or "").lower()


@client.on_message(KeywordFilter("python"))
async def handle_keyword(client, message):
    await message.reply("You mentioned Python!")
```

---

## 5. Handler Groups and Priority

By default, all handlers are registered in group `0`. Within a single group, only the first matching handler executes.

To process an event through multiple independent functions, assign different group numbers:

```python
# Group 0: Audit logging
@client.on_message(filters.all, group=0)
async def logger_handler(client, message):
    print(f"[{message.chat_id}] {message.sender_id}: {message.text}")


# Group 1: Command dispatching
@client.on_message(filters.command("ping"), group=1)
async def ping_handler(client, message):
    await message.reply("pong")
```

To halt propagation across all subsequent groups, raise `StopPropagation`:

```python
from maxlib import StopPropagation


@client.on_message(filters.text("secret_passcode"), group=0)
async def secret_guard(client, message):
    await message.reply("Authorized.")
    raise StopPropagation
```

---

## 6. Middlewares

Middlewares allow executing logic before and after handler execution (logging, metrics, rate limiting):

```python
from maxlib import BaseMiddleware


class LoggingMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        print(f"Before handler: {type(event).__name__}")
        result = await handler(event, data)
        print("After handler execution")
        return result


client.dispatcher.middlewares.register(LoggingMiddleware())
```
