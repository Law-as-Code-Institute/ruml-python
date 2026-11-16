# SPDX-FileCopyrightText: 2026 Rulemapping Group GmbH
# SPDX-License-Identifier: Apache-2.0
"""Tests of RUML Text: reading, writing the norm editor's way, the digest."""

from __future__ import annotations

import hashlib
from typing import Any

from ruml_parser.text import (
    Element,
    Row,
    derived_guid,
    digest,
    elements_by_guid,
    ruml_text,
    text_of,
)


def _act(content: Element) -> list[Element]:
    return content["content"][0]["content"]


def test_a_num_runs_into_what_follows_and_every_other_element_is_a_line():
    # Arrange
    article: dict[str, Any] = {
        "type": "article",
        "content": [
            {"type": "num", "content": ["§ 1"]},
            {"type": "heading", "content": ["Zweck"]},
            {
                "type": "paragraph",
                "content": [
                    {"type": "num", "content": []},
                    {
                        "type": "content",
                        "content": [{"type": "p", "content": ["Es ", "gilt."]}],
                    },
                ],
            },
        ],
    }

    # Act
    text = text_of(article)

    # Assert
    assert text == "§ 1 Zweck\nEs gilt."


def test_anything_but_an_element_or_a_string_reads_as_nothing():
    # Act
    texts = [text_of(None), text_of(1), text_of({"type": "p"})]

    # Assert
    assert texts == ["", "", ""]


def test_the_elements_are_indexed_by_guid_in_document_order():
    # Arrange
    content = ruml_text(
        "owner", [Row("a", "Zweck", "article", "§ 1"), Row("r", "(1) X")]
    )

    # Act
    index = elements_by_guid(content)

    # Assert
    assert list(index)[:3] == [
        derived_guid("owner", "body"),
        "a",
        derived_guid("a", "num"),
    ]
    assert index["r"]["type"] == "paragraph"


def test_free_rows_before_anything_are_the_preamble():
    # Act
    content = ruml_text("owner", [Row("r1", "Gesetz über das Angeln")])

    # Assert
    preamble, body = _act(content)
    assert preamble["attrs"]["GUID"] == derived_guid("owner", "preamble")
    assert preamble["content"] == [
        {"type": "p", "attrs": {"GUID": "r1"}, "content": ["Gesetz über das Angeln"]}
    ]
    assert body["content"] == []


def test_a_free_row_in_an_article_opens_an_implicit_paragraph():
    # Act
    content = ruml_text(
        "owner", [Row("a", "Zweck", "article", "§ 1"), Row("r1", "Text.")]
    )

    # Assert
    paragraph = elements_by_guid(content)[derived_guid("r1", "paragraph")]
    num, body = paragraph["content"]
    assert (num["type"], num["content"]) == ("num", [])
    assert body["content"] == [
        {"type": "p", "attrs": {"GUID": "r1"}, "content": ["Text."]}
    ]


def test_a_numbered_row_is_an_absatz_with_the_rows_guid():
    # Act
    content = ruml_text("owner", [Row("a", "", "article"), Row("r1", "(2) Satz.")])

    # Assert
    paragraph = elements_by_guid(content)["r1"]
    num, body = paragraph["content"]
    assert num["content"] == ["(2)"]
    assert body["content"][0]["attrs"]["GUID"] == derived_guid("r1", "p")
    assert body["content"][0]["content"] == ["Satz."]


def test_an_outline_unit_closes_the_units_of_its_rank_or_below():
    # Arrange
    rows = [
        Row("teil", "Allgemeines", "part", "Teil 1", 1),
        Row("abschnitt", "Begriffe", "section", "Abschnitt 1", 3),
        Row("a1", "Zweck", "article", "§ 1"),
        Row("teil2", "Verfahren", "part", "Teil 2", 1),
        Row("a2", "Antrag", "article", "§ 2"),
    ]

    # Act
    content = ruml_text("owner", rows)

    # Assert
    index = elements_by_guid(content)
    [teil, teil2] = _act(content)[0]["content"]
    assert (teil["attrs"]["GUID"], teil2["attrs"]["GUID"]) == ("teil", "teil2")
    assert index["abschnitt"]["content"][-1]["attrs"]["GUID"] == "a1"
    assert teil2["content"][-1]["attrs"]["GUID"] == "a2"


def test_the_digest_follows_rfc_8785_for_numbers_and_keys():
    # Arrange
    canonical = '{"a":1,"b":0.00005,"c":[true,null,"é"]}'

    # Act
    value = digest({"c": [True, None, "é"], "b": 5e-05, "a": 1.0})

    # Assert
    assert value == "sha3-256:" + hashlib.sha3_256(canonical.encode()).hexdigest()
