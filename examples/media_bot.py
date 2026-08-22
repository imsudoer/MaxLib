"""
Media sending and downloading example with progress callbacks.
"""
from maxlib import MaxClient, filters, Message, DownloadProgress, UploadProgress

client = MaxClient("media_bot")


def upload_progress(progress: UploadProgress):
    print(f"Uploading: {progress.percentage:.1f}% ({progress.speed / 1024:.1f} KB/s)")


def download_progress(progress: DownloadProgress):
    print(f"Downloading: {progress.percentage:.1f}% ({progress.speed / 1024:.1f} KB/s)")


@client.on_message(filters.command("send_pic"))
async def send_pic_handler(client: MaxClient, message: Message):
    await message.reply_photo(
        "pic.jpg",
        caption="🖼️ **Отправлено через MaxLib!**",
        progress_callback=upload_progress,
    )


@client.on_message(filters.photo | filters.document)
async def download_handler(client: MaxClient, message: Message):
    path = await client.download_media(message, progress_callback=download_progress)
    await message.reply(f"✅ Файл успешно скачан в `{path}`")


if __name__ == "__main__":
    client.run()
