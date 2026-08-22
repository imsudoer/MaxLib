# Text Formatting

In the MAX protocol, text styling is not transmitted as raw markup strings; instead, it is sent via an `elements` array containing entity types and their start/length offsets encoded in **UTF-16 code units**.

MaxLib handles this automatically: it parses Markdown V2 or HTML, calculates the exact UTF-16 code unit offsets, and constructs the required `elements` array for the server.

---

## 1. Markdown V2 (Default)

When sending messages via `send_message`, `reply`, or `edit`, `parse_mode="markdown"` is used by default.

### Supported Tags:

| Style | Syntax | Native Element Type |
| :--- | :--- | :--- |
| **Bold** | `**text**` or `*text*` | `STRONG` |
| _Italic_ | `_text_` | `EMPHASIS` |
| __Underline__ | `__text__` | `UNDERLINE` |
| ~~Strikethrough~~ | `~~text~~` | `STRIKETHROUGH` |
| `Monospace code` | `` `text` `` | `CODE` |
| Code block | ```` ```python\nprint(1)\n``` ```` | `CODE` |
| \|\|Spoiler\|\| | `\|\|text\|\|` | `SPOILER` |
| [Hyperlink](https://max.ru) | `[text](url)` | `LINK` |
| [Mention](user:123456) | `[Name](user:123456)` | `LINK` / `MENTION` |

### Example:

```python
await message.reply(
    "Hello **world**!\n"
    "This is _italic_, and this is __underlined__.\n"
    "Code: `x = 42`\n"
    "Secret: ||hidden spoiler||\n"
    "Official site: [MAX](https://max.ru)"
)
```

---

## 2. HTML

To use HTML formatting, specify `parse_mode="html"` or call `client.send_html()`:

### Supported HTML Tags:

- `<b>text</b>` or `<strong>text</strong>`
- `<i>text</i>` or `<em>text</em>`
- `<u>text</u>` or `<ins>text</ins>`
- `<s>text</s>` or `<strike>text</strike>` or `<del>text</del>`
- `<code>text</code>`
- `<pre>code block</pre>`
- `<tg-spoiler>spoiler</tg-spoiler>` or `<spoiler>spoiler</spoiler>`
- `<a href="https://example.com">link text</a>`

### Example:

```python
# Via send_html
await client.send_html(
    chat_id=123456,
    text="<b>Bold Title</b><br><i>Italic description</i> with <a href='https://max.ru'>link</a>"
)

# Via send_message with parse_mode
await message.reply(
    "<code>print('Hello World')</code>",
    parse_mode="html"
)
```

---

## 3. Disabling Formatting (Plain Text)

To send plain text without parsing special characters:

```python
await message.reply("Special characters **will not** be bolded", parse_mode="plain")
```

---

## 4. Standalone Parser Functions

You can invoke parser utilities directly in custom tools:

```python
from maxlib.utils import parse_markdown, parse_html

# Parse Markdown
clean_text, elements = parse_markdown("Hello, **friend**!")
print("Text:", clean_text)    # Hello, friend!
print("Elements:", elements)  # [{'type': 'STRONG', 'length': 6, 'from': 7}]

# Parse HTML
clean_text, elements = parse_html("Test <i>italic</i>")
print("Text:", clean_text)    # Test italic
```
