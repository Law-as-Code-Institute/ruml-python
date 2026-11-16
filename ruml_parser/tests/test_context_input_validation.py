# SPDX-FileCopyrightText: 2026 Rulemapping Group GmbH
# SPDX-License-Identifier: Apache-2.0
"""§4.11: every ai-query context input must name a declared context entry."""

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
from ruml_parser.tests.ruml_dict import ContextDict, ContextDict1, NodeDict


def context_entry() -> ContextDict:
    return {"title": "Ruling", "category": "courtDecision", "timestamp": TIMESTAMP}


def ai_query_node(*context_inputs: str | ContextDict1) -> NodeDict:
    return node(
        capabilities=[
            node_capability(
                "ruml:ai-query",
                {"model": "llm", "inputs": {"context": list(context_inputs)}},
            )
        ]
    )


def test_declared_context_inputs_pass() -> None:
    raw = ruml_document(
        capabilities=[
            capability("ruml:ai-query"),
            capability("ruml:context", {"data": {"ctx_1": context_entry()}}),
        ],
        rulemap={
            "nodes": {"1": ai_query_node("ctx_1", {"id": "ctx_1", "role": "subject"})}
        },
    )
    parsed = RumlRulemappingLogicFormat.model_validate(raw)

    to_internal(parsed)  # must not raise


def test_every_offending_reference_is_reported() -> None:
    # Arrange: node 2 names an undeclared id (in object form), node 3 another one
    raw = ruml_document(
        capabilities=[
            capability("ruml:ai-query"),
            capability("ruml:context", {"data": {"ctx_1": context_entry()}}),
        ],
        rulemap={
            "nodes": {
                "1": ai_query_node("ctx_1"),
                "2": ai_query_node("ctx_1", {"id": "ctx_nope", "role": "subject"}),
                "3": ai_query_node("ctx_1", "ctx_other"),
            }
        },
    )
    parsed = RumlRulemappingLogicFormat.model_validate(raw)

    # Act / Assert
    with pytest.raises(ValueError) as excinfo:
        to_internal(parsed)
    assert str(excinfo.value) == (
        "Some nodes reference undeclared contexts: "
        "node '2' -> context_id 'ctx_nope'; "
        "node '3' -> context_id 'ctx_other' "
        "(spec chapter 4.11: context inputs name root-level context entries)"
    )


def test_without_a_root_context_capability_every_input_is_undeclared() -> None:
    raw = ruml_document(
        capabilities=[capability("ruml:ai-query")],
        rulemap={"nodes": {"1": ai_query_node("ctx_1")}},
    )
    parsed = RumlRulemappingLogicFormat.model_validate(raw)

    with pytest.raises(
        ValueError,
        match=r"^Some nodes reference undeclared contexts: node '1' -> context_id 'ctx_1' ",
    ):
        to_internal(parsed)
