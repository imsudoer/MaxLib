# Media Handling

MaxLib provides an asynchronous interface for sending, uploading, and downloading media attachments: photos, documents, videos, audio tracks, voice notes, and stickers.

---

## 1. Sending Photos

`send_photo` (or `message.reply_photo`) accepts file paths, raw `bytes`, or `io.BytesIO` objects:

```python
# Send from local path
await client.send_photo(
    chat_id=123456,
    photo="photos/avatar.jpg",
    caption="New avatar"
)

# Send raw bytes from memory
with open("image.png", "rb") as f:
    raw_data = f.read()

await message.reply_photo(raw_data, caption="In-memory image")
```

---

## 2. Sending Documents and Files

For generic files (PDFs, archives, code files, spreadsheets), use `send_document`:

```python
await client.send_document(
    chat_id=123456,
    document="reports/stats.xlsx",
    caption="Monthly Report",
    filename="Summary_Report.xlsx"
)
```

---

## 3. Sending Voice Notes

```python
await client.send_voice(
    chat_id=123456,
    voice="audio/voice.ogg",
    duration=5  # Duration in seconds
)
```

---

## 4. Sending Stickers

Stickers are transmitted by numeric sticker ID:

```python
await client.send_sticker(chat_id=123456, sticker_id=11523)
```

---

## 5. Live Progress Tracking

For large transfers, pass a `progress_callback` function:

```python
from maxlib import MaxClient, UploadProgress, DownloadProgress

client = MaxClient("me")


def on_upload_progress(prog: UploadProgress):
    percent = prog.percentage
    speed_kb = prog.speed / 1024
    eta = prog.eta
    print(f"Uploading: {percent:.1f}% | {prog.current}/{prog.total} bytes | {speed_kb:.1f} KB/s | ETA: {eta:.0f}s")


def on_download_progress(prog: DownloadProgress):
    print(f"Downloading: {prog.percentage:.1f}%")


# Upload large archive with progress tracking
await client.send_document(
    chat_id=123456,
    document="big_archive.zip",
    progress_callback=on_upload_progress
)
```

---

## 6. Downloading Media

Download media files via `client.download_media()` or directly on the `Message` model using `message.download()`:

```python
@client.on_message(filters.photo | filters.document | filters.voice)
async def handle_download(client, message):
    # Save file to destination directory
    saved_path = await message.download(
        destination="downloads/",
        progress_callback=on_download_progress
    )
    print(f"File saved to: {saved_path}")
    await message.reply("File downloaded successfully.")
```
