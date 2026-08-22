# Pagination and Iterators

In the MAX protocol, paginated lists (message history, dialog rosters) are returned in chunks according to timestamps or page markers.

MaxLib encapsulates this inside asynchronous generators (`async for`), automatically requesting subsequent pages in the background.

---

## 1. Chat History Iteration (`iter_history`)

```python
# Fetch the last 100 messages from chat
async for message in client.iter_history(chat_id=12345678, limit=100):
    print(f"[{message.time}] {message.sender_id}: {message.text}")

# Via Chat instance
chat = await client.get_chat(12345678)
async for message in chat.iter_history(limit=50):
    if message.photo:
        print(f"Found photo attachment ID: {message.photo.photo_id}")
```

### Parameters:
- `chat_id` (int | str) — target chat ID.
- `limit` (int, optional) — total message ceiling (None = all available history).
- `chunk_size` (int, default 40) — batch size per server request.

---

## 2. Dialogs List Iteration (`iter_dialogs`)

Iterate through private dialogues, groups, and channels:

```python
total_unread = 0

async for chat in client.iter_dialogs(limit=50):
    print(f"Chat ID: {chat.id} | Title: {chat.title or 'Private Dialog'} | Unread: {chat.new_messages}")
    total_unread += chat.new_messages

print(f"Total unread messages: {total_unread}")
```

---

## 3. Streaming Data Filters

Stream and process items in real time without loading the entire collection into memory:

```python
# Search for messages containing web links
async for msg in client.iter_history(chat_id=123456, limit=500):
    if "https://" in msg.text or "http://" in msg.text:
        print(f"Link found: {msg.text}")
```
