# SPDX-FileCopyrightText: 2026 Rulemapping Group GmbH
# SPDX-License-Identifier: Apache-2.0
"""§4.9: every ai-query text input must name a declared text entry."""

import pytest

from ruml_parser.internal.mapping import to_internal
from ruml_parser.model.ruml import RumlRulemappingLogicFormat
from ruml_parser.tests.ruml_builders import (
    TIMESTAMP,
    capability,
    node,
    node_capability,
    ruml_document,
)
from ruml_parser.tests.ruml_dict import NodeDict, TextDict


def text_entry() -> TextDict:
    return {
        "title": "BGB § 823",
        "uri": "/akn/de/act/1896-08-18/bgb#sec_823",
        "timestamp": TIMESTAMP,
        "status": "inForce",
    }


def ai_query_node(*text_inputs: str) -> NodeDict:
    return node(
        capabilities=[
            node_capability(
                "ruml:ai-query",
                {"model": "llm", "inputs": {"texts": list(text_inputs)}},
            )
        ]
    )


def test_declared_text_inputs_pass() -> None:
    raw = ruml_document(
        capabilities=[
            capability("ruml:ai-query"),
            capability("ruml:text-reference", {"data": {"text_1": text_entry()}}),
        ],
        rulemap={"nodes": {"1": ai_query_node("text_1")}},
    )
    parsed = RumlRulemappingLogicFormat.model_validate(raw)

    to_internal(parsed)  # must not raise


def test_every_offending_reference_is_reported() -> None:
    # Arrange: node 2 names an undeclared id, node 3 another one
    raw = ruml_document(
        capabilities=[
            capability("ruml:ai-query"),
            capability("ruml:text-reference", {"data": {"text_1": text_entry()}}),
        ],
        rulemap={
            "nodes": {
                "1": ai_query_node("text_1"),
                "2": ai_query_node("text_1", "text_nope"),
                "3": ai_query_node("text_other"),
            }
        },
    )
    parsed = RumlRulemappingLogicFormat.model_validate(raw)

    # Act / Assert
    with pytest.raises(ValueError) as excinfo:
        to_internal(parsed)
    assert str(excinfo.value) == (
        "Some nodes reference undeclared texts: "
        "node '2' -> text_id 'text_nope'; "
        "node '3' -> text_id 'text_other' "
        "(spec chapter 4.9: text inputs name root-level text entries)"
    )


def test_without_a_root_texts_capability_every_input_is_undeclared() -> None:
    # Arrange
    raw = ruml_document(
        capabilities=[capability("ruml:ai-query")],
        rulemap={"nodes": {"1": ai_query_node("text_1")}},
    )
    parsed = RumlRulemappingLogicFormat.model_validate(raw)

    # Act / Assert
    with pytest.raises(
        ValueError,
        match=r"^Some nodes reference undeclared texts: node '1' -> text_id 'text_1' ",
    ):
        to_internal(parsed)
