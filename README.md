# MaxLib

Асинхронный Python фреймворк для работы с мессенджером MAX (max.ru / OneMe).

Я начинал писать эту либу для себя, чтобы автоматизировать действия в MAX и писать ботов/юзерботов. Стиль API и структура намеренно сделаны максимально похожими на **Pyrogram**, чтобы любой, кто писал юзерботов для Телеграма, мог въехать за пару минут.

Внутри используется настоящий мобильный бинарный протокол приложения (TLS, MsgPack, сжатие LZ4/Zstandard), а не урезанный веб-сокет. Это дает доступ ко всем методам мессенджера и высокую скорость работы.

---

## Установка

Требуется Python 3.9 или выше.

```bash
pip install -U maxlib
```

Зависимости ставятся автоматически (`msgpack`, `lz4`, `aiohttp`, `websockets`).
Если хотите максимальную скорость сжатия, можно докинуть zstandard:

```bash
pip install zstandard
```

---

## Быстрый старт

### Простой эхо-бот

```python
from maxlib import MaxClient, filters, Message

client = MaxClient("my_bot")


@client.on_connect
async def on_connect():
    print(f"Бот запущен под аккаунтом: {client.me.name} (ID: {client.me.id})")


@client.on_message(filters.command("start"))
async def start_cmd(client: MaxClient, message: Message):
    await message.reply(
        "Привет! Я бот на MaxLib.\n"
        "Отправь мне текст, и я повторю его."
    )


@client.on_message(~filters.me & filters.text)
async def echo_handler(client: MaxClient, message: Message):
    await message.reply(f"Вы написали: {message.text}")


if __name__ == "__main__":
    client.run()
```

При первом запуске скрипт запросит номер телефона и SMS-код в консоли, после чего сохранит токен в файл `my_bot.session` и дальше будет входить автоматически.

---

## Авторизация и сессии

### Вход по номеру телефона
Если файла сессии еще нет, `client.run()` или `await client.start()` интерактивно запросят код в терминале:

```python
from maxlib import MaxClient

client = MaxClient("session_name")
client.run()
```

### Вход по готовому токену
Если у вас уже есть токен от профиля:

```python
client = MaxClient("session_name", token="ваш_auth_token")
client.run()
```

### Консольный логин через CLI
Можно авторизовать сессию заранее через терминал:

```bash
python -m maxlib login -s my_session -p +79991234567
```

Проверить профиль сохраненной сессии:

```bash
python -m maxlib info -s my_session
```

Запустить интерактивную консоль Python с готовым подключенным клиентом:

```bash
python -m maxlib shell -s my_session
```

---

## Обработка событий и фильтры

Диспетчер событий работает аналогично Pyrogram. Вешаете декоратор `@client.on_message(фильтр)` на асинхронную функцию:

```python
@client.on_message(filters.command("ping"))
async def handle_ping(client, message):
    await message.reply("pong")
```

### Доступные фильтры

- `filters.all` / `filters.any` — пропускает любые сообщения.
- `filters.me` — сообщения, отправленные текущим аккаунтом (для юзерботов).
- `filters.private` — сообщения из личных диалогов (1-на-1).
- `filters.group` — сообщения из групповых чатов.
- `filters.channel` — сообщения из каналов.
- `filters.reply` — сообщения, являющиеся ответом на другое сообщение.
- `filters.media` — сообщения с любым медиавложением.
- `filters.photo` — сообщения с фотографией.
- `filters.document` — сообщения с документом/файлом.
- `filters.voice` — голосовые сообщения.
- `filters.video` — видеозаписи.
- `filters.sticker` — стикеры.
- `filters.command("команда", prefixes=["/", "."])` — команды с префиксами.
- `filters.text("текст")` или `filters.text(["текст1", "текст2"])` — совпадение по тексту.
- `filters.regex(r"^тест\s+(\d+)$")` — регулярные выражения.
- `filters.sender(user_id)` — сообщения от конкретного пользователя.
- `filters.chat(chat_id)` — сообщения из конкретного чата.
- `filters.state(MyState)` — фильтр по шагу FSM диалога.

### Комбинирование фильтров

Фильтры можно объединять стандартными логическими операторами Python:
- `&` — логическое И (AND)
- `|` — логическое ИЛИ (OR)
- `~` — логическое НЕ (NOT)
- `^` — исключающее ИЛИ (XOR)

Пример:

```python
# Только мои сообщения с командой .ping
@client.on_message(filters.me & filters.command("ping", prefixes="."))
async def ping(client, message):
    await message.reply("Pong!")

# Чужие сообщения в ЛС, содержащие слово 'привет' или 'ку'
@client.on_message(~filters.me & filters.private & (filters.text("привет") | filters.text("ку")))
async def hello(client, message):
    await message.reply("Приветствую!")
```

---

## Методы моделей (Bound Methods)

Все объекты (`Message`, `Chat`, `User`) привязаны к клиенту, поэтому методы действий можно вызывать прямо из них, как в Pyrogram.

### Объект `Message`

```python
# Ответ на сообщение с цитатой
await message.reply("Текст ответа")

# Ответ в тот же чат без цитаты
await message.answer("Просто сообщение в чат")

# Ответ с фото
await message.reply_photo("path/to/pic.jpg", caption="Описание")

# Ответ с файлом
await message.reply_document("archive.zip")

# Редактирование своего сообщения
await message.edit("Обновленный текст")

# Удаление сообщения
await message.delete()

# Поставить реакцию на сообщение
await message.react("❤️")

# Убрать свою реакцию
await message.remove_reaction()

# Переслать в другой чат
await message.forward(to_chat_id=12345678)

# Скачать вложенный медиафайл (фото, голосовое, документ)
path = await message.download(destination="downloads/")
```

### Объект `Chat`

```python
chat = message.chat

# Отправка сообщений
await chat.send_message("Привет чату")
await chat.send_photo("image.png", caption="Фото")

# Закрепить/открепить чат в списке
await chat.pin()
await chat.unpin()

# История сообщений
history = await chat.get_history(limit=50)

# Выйти из чата
await chat.leave()

# Управление участниками
members = await chat.get_members()
await chat.add_members([11223344])
await chat.remove_member(11223344)

# Сменить название
await chat.set_title("Новое название группы")
```

### Объект `User`

```python
user = await message.get_sender()

print(user.name)        # Полное имя
print(user.first_name)  # Имя
print(user.phone)       # Телефон
print(user.id)          # ID пользователя

# Написать в ЛС пользователю
await user.send_message("Привет в личку!")

# Добавить / заблокировать контакт
await user.add_contact()
await user.block()
await user.unblock()

# Формирование кликабельного упоминания в Markdown
mention_link = user.mention()  # [Имя](user:123456)
```

---

## Форматирование текста (Markdown V2 и HTML)

MaxLib сам парсит разметку и превращает ее в нативные бинарные элементы MAX с расчетом UTF-16 смещений.

### Markdown V2 (по умолчанию)

```python
await message.reply(
    "**Жирный текст**\n"
    "_Курсив_\n"
    "__Подчеркнутый__\n"
    "~~Зачеркнутый~~\n"
    "`Моноширинный код`\n"
    "```python\nprint('Блок кода')\n```\n"
    "||Скрытый спойлер||\n"
    "[Ссылка на сайт](https://max.ru)"
)
```

### HTML

```python
await client.send_html(
    chat_id,
    "<b>Жирный</b>, <i>курсив</i>, <u>подчеркнутый</u>, <s>зачеркнутый</s>, "
    "<code>код</code>, <tg-spoiler>спойлер</tg-spoiler>, "
    "<a href='https://max.ru'>Ссылка</a>"
)
```

---

## Отправка и скачивание медиа

Для больших файлов есть поддержка отслеживания прогресса:

```python
from maxlib import MaxClient, UploadProgress, DownloadProgress

client = MaxClient("me")


def upload_cb(prog: UploadProgress):
    print(f"Загрузка: {prog.percentage:.1f}% | Скорость: {prog.speed / 1024:.1f} KB/s")


def download_cb(prog: DownloadProgress):
    print(f"Скачивание: {prog.percentage:.1f}%")


# Отправка фото
await client.send_photo(
    chat_id=123456,
    photo="photo.jpg",
    caption="Мое фото",
    progress_callback=upload_cb
)

# Отправка документа
await client.send_document(
    chat_id=123456,
    document="report.pdf",
    caption="Отчет",
    progress_callback=upload_cb
)

# Скачивание файла из полученного сообщения
@client.on_message(filters.media)
async def handle_media(client, message):
    file_path = await client.download_media(message, progress_callback=download_cb)
    print(f"Сохранено в: {file_path}")
```

---

## Асинхронные итераторы (Пагинация)

Чтобы не возиться со смещениями, маркерами времени и порциями данных вручную:

```python
# Итерация по истории сообщений в чате
async for msg in client.iter_history(chat_id=123456, limit=150):
    print(f"{msg.time}: {msg.text}")

# Итерация по списку диалогов
async for chat in client.iter_dialogs(limit=50):
    print(f"Чат: {chat.title or chat.id}")
```

---

## Пошаговые диалоги (FSM / Finite State Machine)

Если вам нужно сделать опрос, регистрацию или многошаговый диалог:

```python
from maxlib import MaxClient, filters, Message, State, StatesGroup

client = MaxClient("survey_bot")


class Form(StatesGroup):
    name = State()
    age = State()


@client.on_message(filters.command("start"))
async def cmd_start(client: MaxClient, message: Message):
    await client.fsm.set_state(message.chat_id, message.sender_id, Form.name)
    await message.reply("Привет! Как вас зовут?")


@client.on_message(filters.state(Form.name))
async def step_name(client: MaxClient, message: Message):
    await client.fsm.update_data(message.chat_id, message.sender_id, name=message.text)
    await client.fsm.set_state(message.chat_id, message.sender_id, Form.age)
    await message.reply(f"Приятно познакомиться, {message.text}! Сколько вам лет?")


@client.on_message(filters.state(Form.age))
async def step_age(client: MaxClient, message: Message):
    if not message.text.isdigit():
        return await message.reply("Пожалуйста, введите возраст числом.")

    data = await client.fsm.update_data(message.chat_id, message.sender_id, age=int(message.text))
    await client.fsm.clear(message.chat_id, message.sender_id)
    await message.reply(f"Анкета заполнена!\nИмя: {data['name']}\nВозраст: {data['age']}")


client.run()
```

---

## Мульти-аккаунты (`ClientPool`)

Если нужно держать много аккаунтов на одном сервере или запустить пул юзерботов:

```python
from maxlib import ClientPool, filters, Message

pool = ClientPool()
pool.create("acc1", phone="+79991112233")
pool.create("acc2", phone="+79992223344")


@pool.on_message(filters.command("ping", prefixes="."))
async def on_ping(client, message: Message):
    await message.reply(f"Pong от {client.me.name} (ID: {client.me.id})")


if __name__ == "__main__":
    pool.run()
```

---

## Лицензия

GNU General Public License v3.0 (GPL-3.0). Свободное использование и модификация.
