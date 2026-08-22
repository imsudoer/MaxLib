# Bound Methods

In MaxLib, `Message`, `Chat`, `User`, and `Contact` models are bound to their originating client instance, providing object-oriented helper methods without requiring explicit client or chat ID arguments.

---

## 1. Message Object

The `Message` model is passed into `@client.on_message` and `@client.on_edited_message` handlers.

### Key Attributes

- `message.id` — unique message string identifier
- `message.chat_id` — ID of the chat containing the message
- `message.sender_id` — author user ID
- `message.text` — plain or formatted message text
- `message.time` — Unix timestamp in milliseconds
- `message.reply_to_message_id` — ID of the message being replied to (if any)
- `message.is_from_me` — True if sent by the current authenticated user
- `message.chat` — `Chat` instance bound to this message
- `message.photo` — `Photo` instance (or None)
- `message.video` — `Video` instance (or None)
- `message.audio` — `Audio` instance (or None)
- `message.voice` — `Voice` instance (or None)
- `message.document` — `Document` instance (or None)
- `message.sticker` — `Sticker` instance (or None)
- `message.poll` — `Poll` instance (or None)
- `message.reaction_info` — `ReactionInfo` instance containing reaction metrics

### Methods

```python
# 1. Reply to message with quote
sent_msg = await message.reply("Reply text")

# 2. Send message to same chat without quote
sent_msg = await message.answer("Plain chat message")

# 3. Reply with photo
await message.reply_photo("pic.jpg", caption="Photo caption")

# 4. Reply with document or file
await message.reply_document("file.pdf", caption="Document")

# 5. Edit message text
updated_msg = await message.edit("Updated content")

# 6. Delete message
await message.delete(for_me=False)  # for_me=True deletes only for current user

# 7. Add emoji reaction
reactions = await message.react("❤️")
print(f"Total reactions: {reactions.total_count}")

# 8. Remove reaction
await message.remove_reaction()

# 9. Forward message to another chat
await message.forward(to_chat_id=12345678)

# 10. Download attached media to disk
file_path = await message.download(destination="downloads/my_file.jpg")

# 11. Fetch sender profile
sender_user = await message.get_sender()
print(f"Sender name: {sender_user.name}")
```

---

## 2. Chat Object

The `Chat` model represents a 1-on-1 dialogue, group chat, or channel.

### Key Attributes

- `chat.id` — chat ID
- `chat.type` — chat type (`"DIALOG"`, `"CHAT"`, `"CHANNEL"`)
- `chat.title` — group or channel title
- `chat.owner_id` — chat creator user ID
- `chat.participants_count` — total member count
- `chat.is_dialog` — True for 1-on-1 private conversations
- `chat.is_group` — True for group chats
- `chat.is_channel` — True for broadcast channels
- `chat.link` — direct web URL to the chat

### Methods

```python
chat = message.chat

# 1. Send messages
await chat.send_message("Hello chat")
await chat.send_photo("banner.png", caption="Announcement")
await chat.send_document("archive.zip")

# 2. Fetch history
messages = await chat.get_history(limit=50)

# 3. Asynchronous generator iteration (pagination)
async for msg in chat.iter_history(limit=200):
    print(msg.text)

# 4. Pin and unpin chat in dialog list
await chat.pin()
await chat.unpin()

# 5. Leave group chat
await chat.leave()

# 6. Clear chat history
await chat.clear_history()

# 7. Update chat title
await chat.set_title("New Group Title")

# 8. Fetch member roster
members = await chat.get_members()
for m in members:
    print(f"User {m.user_id}, role: {m.role}")

# 9. Add and remove chat members
await chat.add_members([112233, 445566])
await chat.remove_member(112233)
```

---

## 3. User Object

Represents a user profile on MAX.

### Key Attributes

- `user.id` — user ID
- `user.name` — full display name
- `user.first_name` — first name
- `user.last_name` — last name
- `user.phone` — phone number (if visible)
- `user.avatar_url` — user avatar image URL

### Methods

```python
user = await client.get_user(id=123456)

# 1. Send direct message
await user.send_message("Hello in DM!")

# 2. Add to address book contacts
await user.add_contact()

# 3. Remove from contacts
await user.remove_contact()

# 4. Block and unblock user
await user.block()
await user.unblock()

# 5. Generate Markdown mention link
mention = user.mention()                # [Name](user:123456)
custom_mention = user.mention("Friend") # [Friend](user:123456)
```
