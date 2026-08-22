"""
Rich text formatting parser for MAX messenger (Markdown V2 and HTML -> native message elements).
"""
import html
import re
from typing import Any, Dict, List, Tuple


def _utf16_len(s: str) -> int:
    """Calculates string length in UTF-16 code units (as required by MAX messenger API)."""
    return len(s.encode("utf-16-le")) // 2


def parse_markdown(text: str) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Parses Markdown V2 formatted text and produces plain text with MAX elements list.

    Supported syntax:
    - **bold** or *bold*
    - _italic_
    - __underline__
    - ~~strikethrough~~
    - `inline code`
    - ```code block```
    - ||spoiler||
    - [text](url)
    """
    if not text:
        return "", []

    # Combined regex pattern for markdown elements
    # Pre / Code blocks: ```(?:([a-zA-Z0-9_-]+)\n)?([\s\S]*?)```
    # Inline code: `([^`\n]+)`
    # Underline: __([^_]+)__
    # Bold: \*\*([^\*]+)\*\*
    # Strikethrough: ~~([^~]+)~~
    # Spoiler: \|\|([^\|]+)\|\|
    # Italic: _([^_]+)_ or \*([^\*]+)\*
    # Links: \[([^\]]+)\]\(([^)]+)\)

    pattern = re.compile(
        r"(?P<pre>```(?:(?P<pre_lang>[a-zA-Z0-9_-]+)\n)?(?P<pre_text>[\s\S]*?)```)|"
        r"(?P<code>`(?P<code_text>[^`\n]+)`)|"
        r"(?P<underline>__(?P<underline_text>[^_]+)__)|"
        r"(?P<bold>\*\*(?P<bold_text>[^\*]+)\*\*)|"
        r"(?P<strike>~~(?P<strike_text>[^~]+)~~)|"
        r"(?P<spoiler>\|\|(?P<spoiler_text>[^\|]+)\|\|)|"
        r"(?P<italic>_(?P<italic_text1>[^_]+)_|\*(?P<italic_text2>[^\*]+)\*)|"
        r"(?P<link>\[(?P<link_text>[^\]]+)\]\((?P<link_url>[^)]+)\))"
    )

    out_text_parts: List[str] = []
    elements: List[Dict[str, Any]] = []
    current_utf16_offset = 0
    last_idx = 0

    for match in pattern.finditer(text):
        start_idx, end_idx = match.span()
        # Append preceding literal text
        if start_idx > last_idx:
            literal = text[last_idx:start_idx]
            out_text_parts.append(literal)
            current_utf16_offset += _utf16_len(literal)

        m_dict = match.groupdict()

        if m_dict["pre"]:
            content = m_dict["pre_text"]
            elem_type = "CODE"
            extra = {}
        elif m_dict["code"]:
            content = m_dict["code_text"]
            elem_type = "CODE"
            extra = {}
        elif m_dict["underline"]:
            content = m_dict["underline_text"]
            elem_type = "UNDERLINE"
            extra = {}
        elif m_dict["bold"]:
            content = m_dict["bold_text"]
            elem_type = "STRONG"
            extra = {}
        elif m_dict["strike"]:
            content = m_dict["strike_text"]
            elem_type = "STRIKETHROUGH"
            extra = {}
        elif m_dict["spoiler"]:
            content = m_dict["spoiler_text"]
            elem_type = "SPOILER"
            extra = {}
        elif m_dict["italic"]:
            content = m_dict["italic_text1"] or m_dict["italic_text2"]
            elem_type = "EMPHASIS"
            extra = {}
        elif m_dict["link"]:
            content = m_dict["link_text"]
            elem_type = "LINK"
            extra = {"url": m_dict["link_url"]}
        else:
            content = match.group(0)
            elem_type = None
            extra = {}

        content_utf16_len = _utf16_len(content)
        if elem_type:
            elem = {
                "type": elem_type,
                "length": content_utf16_len,
            }
            if current_utf16_offset > 0:
                elem["from"] = current_utf16_offset
            elem.update(extra)
            elements.append(elem)

        out_text_parts.append(content)
        current_utf16_offset += content_utf16_len
        last_idx = end_idx

    if last_idx < len(text):
        out_text_parts.append(text[last_idx:])

    return "".join(out_text_parts), elements


def parse_html(text: str) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Parses HTML formatted text and produces plain text with MAX elements list.

    Supported tags:
    - <b> or <strong> -> STRONG
    - <i> or <em> -> EMPHASIS
    - <u> or <ins> -> UNDERLINE
    - <s> or <strike> or <del> -> STRIKETHROUGH
    - <code> -> CODE
    - <pre> -> CODE
    - <spoiler> or <tg-spoiler> -> SPOILER
    - <a href="..."> -> LINK
    """
    if not text:
        return "", []

    tag_re = re.compile(r"<\s*(?P<closing>/)?\s*(?P<tag>[a-zA-Z0-9_\-]+)(?P<attrs>[^>]*)>", re.IGNORECASE)
    href_re = re.compile(r'href\s*=\s*["\']([^"\']+)["\']', re.IGNORECASE)

    TAG_MAPPING = {
        "b": "STRONG",
        "strong": "STRONG",
        "i": "EMPHASIS",
        "em": "EMPHASIS",
        "u": "UNDERLINE",
        "ins": "UNDERLINE",
        "s": "STRIKETHROUGH",
        "strike": "STRIKETHROUGH",
        "del": "STRIKETHROUGH",
        "code": "CODE",
        "pre": "CODE",
        "spoiler": "SPOILER",
        "tg-spoiler": "SPOILER",
        "a": "LINK",
    }

    out_text_parts: List[str] = []
    elements: List[Dict[str, Any]] = []
    stack: List[Tuple[str, int, Dict[str, Any]]] = []
    current_utf16_offset = 0
    last_idx = 0

    for match in tag_re.finditer(text):
        start_idx, end_idx = match.span()
        if start_idx > last_idx:
            chunk = html.unescape(text[last_idx:start_idx])
            out_text_parts.append(chunk)
            current_utf16_offset += _utf16_len(chunk)

        is_closing = bool(match.group("closing"))
        tag_name = match.group("tag").lower()
        elem_type = TAG_MAPPING.get(tag_name)

        if elem_type:
            if not is_closing:
                attrs = match.group("attrs") or ""
                extra = {}
                if elem_type == "LINK":
                    href_match = href_re.search(attrs)
                    if href_match:
                        extra["url"] = href_match.group(1)
                stack.append((elem_type, current_utf16_offset, extra))
            else:
                # Find matching opening tag on stack
                for i in range(len(stack) - 1, -1, -1):
                    if stack[i][0] == elem_type:
                        open_type, open_offset, extra = stack.pop(i)
                        length = current_utf16_offset - open_offset
                        if length > 0:
                            elem = {
                                "type": open_type,
                                "length": length,
                            }
                            if open_offset > 0:
                                elem["from"] = open_offset
                            elem.update(extra)
                            elements.append(elem)
                        break

        last_idx = end_idx

    if last_idx < len(text):
        chunk = html.unescape(text[last_idx:])
        out_text_parts.append(chunk)

    return "".join(out_text_parts), elements


def format_text(
    text: str,
    elements: List[Dict[str, Any]] = None,
    *,
    parse_mode: str = "markdown",
) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Helper to process text with chosen parse mode ('markdown', 'html', or 'plain').
    """
    if elements:
        return text, list(elements)

    if not text:
        return "", []

    mode = parse_mode.lower() if parse_mode else "plain"
    if mode in ("markdown", "md", "markdownv2"):
        return parse_markdown(text)
    elif mode == "html":
        return parse_html(text)
    else:
        return text, []
