# Authentication and Sessions

MaxLib provides flexible authentication methods and session persistence.

---

## 1. Authentication Methods

### A. Interactive Phone Login
The simplest approach: create a client and call `client.run()` or `await client.start()`. If no session file is found, the library automatically prompts for phone number and verification code in the terminal:

```python
from maxlib import MaxClient

client = MaxClient("my_account")
client.run()
```

### B. Login with Existing Token
If you already possess a profile token (e.g. exported from a previous session):

```python
from maxlib import MaxClient

client = MaxClient("my_account", token="your_auth_token_here")
client.run()
```

### C. Programmatic Auth with Custom Code Callback
If you are integrating authentication into a web dashboard, Telegram bot, or UI:

```python
async def custom_code_provider() -> str:
    # Retrieve code from queue, database, or web frontend
    code = await fetch_code_from_user()
    return code


async def main():
    client = MaxClient("web_session")
    await client.start(phone="+79991234567", code_callback=custom_code_provider)
```

---

## 2. Session File Structure

Sessions are stored in JSON format (defaulting to `.session` or `.json` file extension).

Example session file content:
```json
{
  "token": "An_Sx6HQ9HDi...",
  "account_id": 41424820,
  "phone": "+79902394485",
  "device_id": "8c4598d1-9f22-4217-a169-7cbe60b0932c",
  "instance_id": "4b3df149-c183-4a1d-8449-3be99281db24",
  "client_session_id": 492048591,
  "device_type": "ANDROID",
  "app_version": "26.17.1",
  "build_number": 6712,
  "os_version": "Android 14",
  "timezone": "Europe/Moscow",
  "screen": "1080x2400 440dpi",
  "push_device_type": "GCM",
  "arch": "arm64-v8a",
  "locale": "ru",
  "device_name": "Xiaomi Redmi Note 13 Pro",
  "device_locale": "ru"
}
```

The library emulates an official Android device profile to match standard client network fingerprints.

> **Backward Compatibility**: If you have legacy `.session` files containing raw plaintext tokens from older MaxLib versions, MaxLib automatically parses, migrates, and upgrades them into the full JSON format upon first connection.

---

## 3. Ephemeral (In-Memory) Sessions

If you do not want to persist session data to disk (e.g. in stateless Docker containers or transient tests):

```python
from maxlib import MaxClient
from maxlib.session import MemorySession

session = MemorySession(token="auth_token_here")
client = MaxClient(session=session)
```

---

## 4. Command Line Interface (CLI)

MaxLib includes built-in terminal commands:

### Authorize session via terminal:
```bash
python -m maxlib login -s work_account -p +79991112233
```

### Inspect account profile:
```bash
python -m maxlib info -s work_account
```
Output:
```
========================================
 User ID:      41424820
 Full Name:    Ivan Ivanov
 Phone:        +79991112233
 Avatar URL:   https://i.oneme.ru/i?r=...
========================================
```

### Interactive Python REPL:
```bash
python -m maxlib shell -s work_account
```
Launches an interactive Python shell with an already initialized and connected `client` instance:
```python
>>> asyncio.run(client.send_message(123456, "Hello from shell!"))
```
