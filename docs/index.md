# MaxLib Documentation

MaxLib is an asynchronous Python framework for interacting with the MAX messenger (max.ru / OneMe).

The library is designed in the style of **Pyrogram** to provide developers with a familiar, ergonomic, and high-performance interface for building bots, userbots, and automation scripts.

---

## Documentation Sections

1. [Quick Start](quickstart.md) — installation, your first echo bot, and fundamental concepts.
2. [Authentication and Sessions](authentication.md) — login methods (phone, code, token), CLI tools, and session file structure.
3. [Dispatcher and Filters](dispatcher-and-filters.md) — handler registration, complete filter list, logical operators, and middlewares.
4. [Bound Methods](bound-methods.md) — Message, Chat, and User object actions and helper methods.
5. [Text Formatting](formatting.md) — Markdown V2, HTML, escaping, and UTF-16 code unit offset calculation.
6. [Media](media.md) — uploading, sending, and downloading photos, documents, voice notes with live progress callbacks.
7. [FSM (Finite State Machine)](fsm.md) — State, StatesGroup, and storage backends for multi-step conversation flows.
8. [Pagination and Iterators](pagination.md) — asynchronous generators for chat history, dialog lists, and member rosters.
9. [Multi-Account (ClientPool)](multi-account.md) — running dozens of client accounts concurrently in a single process.
10. [Protocol Internals](protocol-internals.md) — mobile binary protocol, MsgPack, LZ4/ZSTD compression, and network frame headers.
11. [Opcodes Reference](opcodes-reference.md) — complete lookup table of known MAX protocol opcodes.
