"""
HTML sanitisation utilities for the Europass-to-resume converter:

- Decode HTML entities before sanitising.
- If input contains no HTML tags, convert non-empty lines to paragraphs.
- Preserve only a narrow semantic HTML subset:
  p, br, ul, ol, li, strong, em, u, a.
- Preserve a[href] only for http, https, mailto, and tel links.
- Strip all unknown attributes.
- Delete dangerous tags with their content.
- Unwrap span and unsupported layout tags.
- Convert simple plain-text div blocks to p.
- Convert headings h1-h6 to p > strong.
- Convert b to strong and i to em.
- Remove empty paragraphs and empty list items.
- Simplify li > p structures.
- Preserve Unicode text; do not transliterate.
"""


from __future__ import annotations

import html as html_lib
import re
from typing import Any

import bleach
from bs4 import BeautifulSoup, Comment, NavigableString, Tag


ALLOWED_TAGS: frozenset[str] = frozenset(
    {
        "p",
        "br",
        "ul",
        "ol",
        "li",
        "strong",
        "em",
        "u",
        "a",
    }
)

ALLOWED_ATTRIBUTES: dict[str, list[str]] = {
    "a": ["href"],
}

ALLOWED_PROTOCOLS: frozenset[str] = frozenset(
    {
        "http",
        "https",
        "mailto",
        "tel",
    }
)

DANGEROUS_TAGS: frozenset[str] = frozenset(
    {
        "script",
        "style",
        "iframe",
        "object",
        "embed",
        "applet",
        "base",
        "form",
        "input",
        "button",
        "textarea",
        "select",
        "option",
        "svg",
        "math",
        "canvas",
        "video",
        "audio",
        "source",
        "track",
        "link",
        "meta",
        "noscript",
    }
)

TABLE_TAGS: frozenset[str] = frozenset(
    {
        "table",
        "thead",
        "tbody",
        "tfoot",
        "tr",
        "td",
        "th",
        "caption",
        "colgroup",
        "col",
    }
)

HEADING_TAGS: frozenset[str] = frozenset(
    {
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
    }
)

HTML_TAG_RE = re.compile(r"</?[a-zA-Z][^>]*>")


def sanitize_html(value: Any) -> str:
    """
    Sanitise a text or HTML fragment for insertion into the target resume JSON.

    Args:
        value:
            Raw text, escaped HTML, or HTML fragment.

    Returns:
        A safe HTML fragment, or an empty string for missing/empty input.
    """

    if value is None:
        return ""

    text = str(value).strip()
    if not text:
        return ""

    decoded = html_lib.unescape(text).strip()
    if not decoded:
        return ""

    if not contains_html_tags(decoded):
        return plain_text_to_html(decoded)

    soup = BeautifulSoup(decoded, "html.parser")

    _remove_comments(soup)
    _delete_dangerous_tags(soup)
    _normalise_semantic_tags(soup)
    _normalise_headings(soup)
    _normalise_divs(soup)
    _soft_unwrap_tables(soup)
    _unwrap_known_layout_tags(soup)
    _simplify_list_item_paragraphs(soup)
    _normalise_text_nodes(soup)
    _remove_empty_tags(soup)

    precleaned = _serialise_fragment(soup)

    cleaned = bleach.clean(
        precleaned,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        protocols=ALLOWED_PROTOCOLS,
        strip=True,
        strip_comments=True,
    )

    cleaned_soup = BeautifulSoup(cleaned, "html.parser")

    _simplify_list_item_paragraphs(cleaned_soup)
    _normalise_text_nodes(cleaned_soup)
    _remove_empty_tags(cleaned_soup)

    result = _serialise_fragment(cleaned_soup)
    result = _tidy_output(result)

    return result


def contains_html_tags(value: str) -> bool:
    """
    Return True if the string appears to contain HTML tags.

    This intentionally detects only plausible tag names, so plain comparisons
    such as '2 < 3' are not treated as HTML.
    """

    return HTML_TAG_RE.search(value) is not None


def plain_text_to_html(value: Any) -> str:
    """
    Convert plain text into paragraph HTML.

    Non-empty lines become separate paragraphs. Empty lines are ignored.
    """

    if value is None:
        return ""

    text = html_lib.unescape(str(value)).strip()
    if not text:
        return ""

    paragraphs: list[str] = []

    for line in text.splitlines():
        normalised = _collapse_text(line).strip()
        if not normalised:
            continue

        escaped = html_lib.escape(normalised, quote=False)
        paragraphs.append(f"<p>{escaped}</p>")

    return "".join(paragraphs)


def _remove_comments(soup: BeautifulSoup) -> None:
    for comment in soup.find_all(string=lambda node: isinstance(node, Comment)):
        comment.extract()


def _delete_dangerous_tags(soup: BeautifulSoup) -> None:
    for tag in soup.find_all(DANGEROUS_TAGS):
        tag.decompose()


def _normalise_semantic_tags(soup: BeautifulSoup) -> None:
    for tag in soup.find_all("b"):
        tag.name = "strong"

    for tag in soup.find_all("i"):
        tag.name = "em"


def _normalise_headings(soup: BeautifulSoup) -> None:
    for heading in soup.find_all(HEADING_TAGS):
        paragraph = soup.new_tag("p")
        strong = soup.new_tag("strong")

        while heading.contents:
            strong.append(heading.contents[0].extract())

        paragraph.append(strong)
        heading.replace_with(paragraph)


def _normalise_divs(soup: BeautifulSoup) -> None:
    for div in soup.find_all("div"):
        if _contains_only_plain_text(div):
            div.name = "p"
        else:
            div.unwrap()


def _contains_only_plain_text(tag: Tag) -> bool:
    """
    Return True when a tag has no child tags and contains text only.
    """

    return not tag.find(True)


def _soft_unwrap_tables(soup: BeautifulSoup) -> None:
    """
    Remove table structure while keeping its textual content.

    The first version of the converter does not preserve tables. This function
    inserts light separators before unwrapping cells and rows to avoid merging
    unrelated text too aggressively.
    """

    for cell in soup.find_all(["td", "th"]):
        if cell.get_text(strip=True):
            cell.append(" ")

    for row in soup.find_all("tr"):
        if row.get_text(strip=True):
            row.append(soup.new_tag("br"))

    for tag in soup.find_all(TABLE_TAGS):
        tag.unwrap()


def _unwrap_known_layout_tags(soup: BeautifulSoup) -> None:
    for tag in soup.find_all("span"):
        tag.unwrap()


def _simplify_list_item_paragraphs(soup: BeautifulSoup) -> None:
    """
    Convert <li><p>Text</p></li> into <li>Text</li>.

    This also unwraps direct paragraph children inside list items while keeping
    inline formatting and links.
    """

    for list_item in soup.find_all("li"):
        for paragraph in list_item.find_all("p", recursive=False):
            paragraph.unwrap()


def _normalise_text_nodes(soup: BeautifulSoup) -> None:
    for node in soup.find_all(string=True):
        if isinstance(node, Comment):
            continue

        parent = node.parent
        if isinstance(parent, Tag) and parent.name in {"script", "style"}:
            continue

        original = str(node)
        collapsed = _collapse_text_preserving_edge_spaces(original)

        if collapsed == "":
            node.extract()
        else:
            node.replace_with(NavigableString(collapsed))


def _collapse_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.replace("\xa0", " "))


def _collapse_text_preserving_edge_spaces(value: str) -> str:
    value = value.replace("\xa0", " ")

    if not value:
        return ""

    has_leading_space = value[0].isspace()
    has_trailing_space = value[-1].isspace()

    collapsed_inner = _collapse_text(value.strip())

    if not collapsed_inner:
        return " " if has_leading_space or has_trailing_space else ""

    if has_leading_space:
        collapsed_inner = " " + collapsed_inner

    if has_trailing_space:
        collapsed_inner += " "

    return collapsed_inner


def _remove_empty_tags(soup: BeautifulSoup) -> None:
    """
    Remove empty p and li tags, then remove empty ul/ol containers.

    Standalone br tags are preserved.
    """

    changed = True

    while changed:
        changed = False

        for tag in list(soup.find_all(["p", "li"])):
            if _is_empty_block(tag):
                tag.decompose()
                changed = True

        for tag in list(soup.find_all(["ul", "ol"])):
            if not tag.find("li"):
                tag.decompose()
                changed = True


def _is_empty_block(tag: Tag) -> bool:
    if tag.find("br"):
        return False

    if tag.name == "li" and tag.find(["ul", "ol"]):
        return False

    return tag.get_text(strip=True) == ""


def _serialise_fragment(soup: BeautifulSoup) -> str:
    """
    Serialise a BeautifulSoup document as an HTML fragment rather than a full
    document.
    """

    body = soup.find("body")
    container: Tag | BeautifulSoup = body if body is not None else soup

    return "".join(str(child) for child in container.contents)


def _tidy_output(value: str) -> str:
    value = value.strip()

    if not value:
        return ""

    value = re.sub(r"\s+", " ", value)

    # Remove whitespace immediately inside common tags.
    value = re.sub(
        r"(<(?:p|li|strong|em|u|a)(?:\s+href=\"[^\"]*\")?>)\s+",
        r"\1",
        value,
    )
    value = re.sub(
        r"\s+(</(?:p|li|strong|em|u|a)>)",
        r"\1",
        value,
    )

    # Remove whitespace between block-level tags, while leaving inline spacing
    # inside text mostly intact.
    value = re.sub(
        r"(</(?:p|ul|ol|li)>)\s+(<(?:(?:p|ul|ol|li)\b|br\s*/?>))",
        r"\1\2",
        value,
    )

    # Normalise BeautifulSoup's self-closing br serialisation.
    value = value.replace("<br/>", "<br>")

    # Remove empty paragraphs/list items that may have appeared after final
    # whitespace tidying.
    value = re.sub(r"<p>\s*</p>", "", value)
    value = re.sub(r"<li>\s*</li>", "", value)

    return value.strip()


__all__ = [
    "ALLOWED_TAGS",
    "ALLOWED_ATTRIBUTES",
    "ALLOWED_PROTOCOLS",
    "sanitize_html",
    "contains_html_tags",
    "plain_text_to_html",
]