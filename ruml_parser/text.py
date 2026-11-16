# SPDX-FileCopyrightText: 2026 Rulemapping Group GmbH
# SPDX-License-Identifier: Apache-2.0
"""RUML Text (§4.12) in its JSON form: `{type, attrs?, content?}` elements and strings.

Reading inserts the whitespace the builder does not write: a `num` runs into what
follows with a space, every other element is a line of its own. Writing follows
the builder's norm editor: rows go in, `akomaNtoso > act > (preamble,) body` comes
out, an element carries its row's id as `GUID` and its parts derive theirs from it.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

LDML_NAMESPACE = "http://Inhaltsdaten.LegalDocML.de/1.8.2/"
"""Default namespace of the texts written here; it names their dialect (§4.12)."""
GUID_ATTR = "GUID"

Element = dict[str, Any]

_PARAGRAPH_NUM = re.compile(r"^\((\d+[a-z]?)\)\s*")


def _separator(previous: Any, current: Any) -> str:
    if isinstance(previous, str) and isinstance(current, str):
        return ""
    if isinstance(previous, dict) and previous.get("type") == "num":
        return " "
    return "\n"


def text_of(tree: Any) -> str:
    """Return the readable text of a RUML Text element."""
    if isinstance(tree, str):
        return tree
    if not isinstance(tree, dict):
        return ""
    text = ""
    previous: Any = None
    for child in tree.get("content") or ():
        child_text = text_of(child)
        # an empty element (an unnumbered paragraph's `num`) takes no space
        if not child_text and isinstance(child, dict):
            continue
        text += ("" if previous is None else _separator(previous, child)) + child_text
        previous = child
    return text


def elements_by_guid(tree: Any) -> dict[str, Element]:
    """Return the elements of `tree` keyed by their GUID, in document order."""
    index: dict[str, Element] = {}

    def walk(node: Any) -> None:
        if not isinstance(node, dict):
            return
        guid = (node.get("attrs") or {}).get(GUID_ATTR)
        if isinstance(guid, str):
            index[guid] = node
        for child in node.get("content") or ():
            walk(child)

    walk(tree)
    return index


def derived_guid(owner: str, role: str) -> str:
    """Return the GUID of an element's `role` under `owner`, stable across runs.

    The same derivation as the builder's `derivedGuid`.
    """
    digest = bytearray(hashlib.sha256(f"{owner}/{role}".encode()).digest()[:16])
    digest[6] = (digest[6] & 0x0F) | 0x80
    digest[8] = (digest[8] & 0x3F) | 0x80
    hex_ = digest.hex()
    return f"{hex_[:8]}-{hex_[8:12]}-{hex_[12:16]}-{hex_[16:20]}-{hex_[20:]}"


def _number(value: float) -> str:
    """Return `value` as ECMAScript's Number::toString writes it, as RFC 8785 asks."""
    if value == 0:
        return "0"
    sign = "-" if value < 0 else ""
    _, digit_tuple, exponent = Decimal(repr(abs(value))).normalize().as_tuple()
    digits = "".join(map(str, digit_tuple))
    point = int(exponent) + len(digits)
    if len(digits) <= point <= 21:
        return sign + digits + "0" * (point - len(digits))
    if 0 < point <= 21:
        return sign + digits[:point] + "." + digits[point:]
    if -6 < point <= 0:
        return sign + "0." + "0" * -point + digits
    mantissa = digits[0] + ("." + digits[1:] if len(digits) > 1 else "")
    return f"{sign}{mantissa}e{'+' if point > 0 else '-'}{abs(point - 1)}"


def _utf16(key: str) -> bytes:
    return key.encode("utf-16-be")


def _canonical(value: Any) -> str:
    if isinstance(value, dict):
        keys = sorted(value, key=_utf16)
        members = (f"{_canonical(k)}:{_canonical(value[k])}" for k in keys)
        return "{" + ",".join(members) + "}"
    if isinstance(value, list):
        return "[" + ",".join(_canonical(item) for item in value) + "]"
    if isinstance(value, float):
        return _number(value)
    return json.dumps(value, ensure_ascii=False)


def digest(value: Any) -> str:
    """Return the SHA3-256 digest of `value` in RFC 8785 form."""
    return "sha3-256:" + hashlib.sha3_256(_canonical(value).encode()).hexdigest()


@dataclass(frozen=True)
class Row:
    """One line of a text; with a `unit` ("article", "chapter", …) a heading."""

    id: str
    text: str
    unit: str | None = None
    num: str = ""
    level: int = 0
    """Rank of an outline unit; it closes the open units of its rank or below."""


def _element(type_: str, guid: str, content: list[Any]) -> Element:
    return {"type": type_, "attrs": {GUID_ATTR: guid}, "content": content}


def _leaf(type_: str, guid: str, text: str) -> Element:
    return _element(type_, guid, [text] if text else [])


def _heading(row: Row) -> Element:
    content = [_leaf("num", derived_guid(row.id, "num"), row.num)]
    if row.text:
        content.append(_leaf("heading", derived_guid(row.id, "heading"), row.text))
    return _element(row.unit or "article", row.id, content)


def _paragraph(guid: str, num: str) -> Element:
    return _element(
        "paragraph",
        guid,
        [
            _leaf("num", derived_guid(guid, "num"), num),
            _element("content", derived_guid(guid, "content"), []),
        ],
    )


def ruml_text(owner: str, rows: Iterable[Row]) -> Element:
    """Return `rows` as a RUML Text document whose own GUIDs derive from `owner`.

    An outline unit nests by level, an article opens on its heading row, a `(1)`
    row opens a numbered paragraph, and a free row joins the open paragraph, an
    implicit one, or the preamble before anything else.
    """
    body = _element("body", derived_guid(owner, "body"), [])
    preamble: Element | None = None
    outline: list[tuple[int, Element]] = []
    article: Element | None = None
    paragraph: Element | None = None

    def container() -> Element:
        return outline[-1][1] if outline else body

    def open_paragraph(node: Element) -> Element:
        (article or container())["content"].append(node)
        return node

    for row in rows:
        if row.unit == "article":
            article, paragraph = _heading(row), None
            container()["content"].append(article)
        elif row.unit:
            while outline and outline[-1][0] >= row.level:
                outline.pop()
            node = _heading(row)
            container()["content"].append(node)
            outline.append((row.level, node))
            article = paragraph = None
        elif not row.text:
            continue
        elif match := _PARAGRAPH_NUM.match(row.text):
            paragraph = open_paragraph(_paragraph(row.id, f"({match.group(1)})"))
            text = row.text[match.end() :]
            paragraph["content"][1]["content"].append(
                _leaf("p", derived_guid(row.id, "p"), text)
            )
        elif article is None and paragraph is None and not body["content"]:
            preamble = preamble or _element(
                "preamble", derived_guid(owner, "preamble"), []
            )
            preamble["content"].append(_leaf("p", row.id, row.text))
        else:
            if paragraph is None:
                paragraph = open_paragraph(
                    _paragraph(derived_guid(row.id, "paragraph"), "")
                )
            paragraph["content"][1]["content"].append(_leaf("p", row.id, row.text))

    act = [preamble, body] if preamble else [body]
    return {
        "type": "akomaNtoso",
        "attrs": {"xmlns": LDML_NAMESPACE},
        "content": [
            {"type": "act", "attrs": {"name": "regelungstext"}, "content": act}
        ],
    }
