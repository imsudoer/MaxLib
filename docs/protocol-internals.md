# Protocol Internals

Unlike the web version of MAX which exchanges JSON over WebSockets, the official mobile applications (Android/iOS) communicate via a binary protocol over raw TLS TCP sockets (`api.oneme.ru:443`).

MaxLib uses this mobile protocol by default.

---

## 1. Packet Wire Frame (Header & Body)

Each network packet consists of:
1. **Fixed-size Header (10 bytes)**
2. **Variable-size Body**

### Header Struct Layout (`>BBHHI`, big-endian):

```
+------------+------------+------------+------------+------------------------+
|  ver (1B)  |  cmd (1B)  |  seq (2B)  | opcode(2B) |     packed_len (4B)    |
+------------+------------+------------+------------+------------------------+
|   uint8    |   uint8    |   uint16   |   uint16   | flag (1B) | length (3B)|
+------------+------------+------------+------------+------------------------+
```

- **ver** (1 byte): API protocol version (current version is `11`).
- **cmd** (1 byte): Command code:
  - `0` — Request (client to server) or Push notification (server to client).
  - `1` — OK (successful response).
  - `2` — Not Found (requested entity does not exist).
  - `3` — Error (operation failed).
- **seq** (2 bytes, uint16): Sequence number for request-response correlation.
- **opcode** (2 bytes, uint16): Numeric operation identifier (e.g. `64` = send message, `19` = login).
- **packed_len** (4 bytes, uint32):
  - High byte (8 bits) — compression ratio flag (0 = uncompressed, >0 = LZ4 compressed).
  - Low 3 bytes (24 bits) — length of payload body in bytes.

---

## 2. Serialization and Compression (MsgPack + LZ4)

- Payload bodies are serialized into binary **MessagePack**.
- If the serialized length exceeds 32 bytes, the body is compressed using **LZ4 Block Compression**.
- This yields 3-5x bandwidth reduction compared to JSON WebSockets and speeds up large data synchronization.

---

## 3. Sequence Multiplexing Table

When invoking an API method (such as `await client.send_message(...)`):
1. The `seq` generator increments the sequence ID.
2. An `asyncio.Future` is stored in `_pending[seq]`.
3. The frame is packed and written to the TLS stream writer.
4. Background `_read_loop()` reads incoming frames.
5. When a matching response frame arrives, its corresponding Future is resolved.
6. When a push notification arrives (`cmd=0`, such as Opcode 128 for incoming messages), it is immediately routed to the event dispatcher without blocking request pipelines.
