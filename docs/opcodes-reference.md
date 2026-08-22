# Opcodes Reference

Complete reference table of MAX protocol operation codes (Opcodes).

---

## System & Connection

| Opcode | Enum Name | Description |
| :--- | :--- | :--- |
| `1` | `PING` | Heartbeat keep-alive ping |
| `2` | `DEBUG` | Server debug ping |
| `3` | `RECONNECT` | Reconnection signal |
| `5` | `LOG` | Client telemetry log |
| `6` | `SESSION_INIT` | Handshake with device metadata |

---

## Authentication & Account

| Opcode | Enum Name | Description |
| :--- | :--- | :--- |
| `16` | `PROFILE` | Update user profile and bio |
| `17` | `AUTH_START` | Initiate SMS/Push login |
| `18` | `AUTH_CHECK_CODE` | Submit verification code |
| `19` | `LOGIN` | Log in with session token |
| `20` | `LOGOUT` | Terminate active session |
| `21` | `SYNC` | Sync chats, presence, and contacts |
| `22` | `CONFIG` | Update client settings (e.g. pinned chats) |
| `25` | `PRESET_AVATARS` | Fetch MAX preset avatars catalog |

---

## Contacts

| Opcode | Enum Name | Description |
| :--- | :--- | :--- |
| `32` | `CONTACT_INFO` | Fetch contact details by user ID |
| `33` | `CONTACT_ADD` | Add user to address book |
| `34` | `CONTACT_UPDATE` | Contact action (ADD, REMOVE, BLOCK, UNBLOCK) |
| `35` | `CONTACT_PRESENCE` | Fetch online / last seen status |
| `36` | `CONTACT_LIST` | Fetch user address book roster |
| `37` | `CONTACT_SEARCH` | Search contacts |
| `38` | `CONTACT_MUTUAL` | Fetch mutual contacts |
| `46` | `CONTACT_INFO_BY_PHONE` | Look up user by phone number |

---

## Chats & Messaging

| Opcode | Enum Name | Description |
| :--- | :--- | :--- |
| `48` | `CHAT_INFO` | Fetch chat metadata |
| `49` | `CHAT_HISTORY` | Fetch message history in chat |
| `50` | `CHAT_MARK` | Mark messages as read |
| `51` | `CHAT_MEDIA` | Fetch shared media gallery |
| `52` | `CHAT_DELETE` | Delete chat |
| `53` | `CHATS_LIST` | Fetch user dialogs list |
| `54` | `CHAT_CLEAR` | Clear chat message history |
| `55` | `CHAT_UPDATE` | Update chat title / icon |
| `57` | `CHAT_JOIN` | Join chat via link |
| `58` | `CHAT_LEAVE` | Leave chat |
| `59` | `CHAT_MEMBERS` | Fetch chat member list |
| `60` | `PUBLIC_SEARCH` | Global public search (users/channels) |
| `63` | `CHAT_CREATE` | Create group chat or channel |
| `64` | `MSG_SEND` | Send message |
| `65` | `MSG_TYPING` | Send typing status |
| `66` | `MSG_DELETE` | Delete messages |
| `67` | `MSG_EDIT` | Edit message text/elements |
| `75` | `CHAT_SUBSCRIBE` | Subscribe to channel |
| `77` | `CHAT_MEMBERS_UPDATE` | Add or kick members |

---

## Media Uploads

| Opcode | Enum Name | Description |
| :--- | :--- | :--- |
| `80` | `PHOTO_UPLOAD` | Request photo upload endpoint |
| `81` | `STICKER_UPLOAD` | Request sticker upload endpoint |
| `82` | `VIDEO_UPLOAD` | Request video upload endpoint |
| `83` | `AUDIO_UPLOAD` | Request audio/voice upload endpoint |
| `84` | `FILE_UPLOAD` | Request document/file upload endpoint |

---

## Real-Time Push Events (Server -> Client)

| Opcode | Enum Name | Dispatched Model / Event |
| :--- | :--- | :--- |
| `128` | `PUSH_NEW_MESSAGE` | `MessageEvent` / `Message` |
| `129` | `PUSH_TYPING` | `TypingEvent` |
| `130` | `PUSH_MESSAGE_EDIT` | `MessageEditedEvent` / `Message` |
| `131` | `PUSH_MESSAGE_DELETE` | `MessageDeletedEvent` |
| `132` | `PUSH_CHAT_UPDATE` | Chat metadata update |
| `133` | `PUSH_PRESENCE` | `PresenceEvent` |
| `134` | `PUSH_REACTION` | `ReactionEvent` |
| `135` | `PUSH_CALL` | Call signaling update |

---

## Reactions

| Opcode | Enum Name | Description |
| :--- | :--- | :--- |
| `178` | `SET_REACTION` | Set emoji reaction |
| `179` | `REMOVE_REACTION` | Remove emoji reaction |
| `180` | `GET_REACTIONS` | Get reaction details |
