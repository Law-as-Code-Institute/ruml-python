# SPDX-FileCopyrightText: 2026 Rulemapping Group GmbH
# SPDX-License-Identifier: Apache-2.0
"""§6.2, MOD-01: a node referenced more than once must be marked `modular`."""

import pytest
from ruml_parser.ruml_parser import RumlParser
from ruml_parser.structural_error import RumlStructuralError
from ruml_parser.tests.ruml_builders import node, ruml_document
from ruml_parser.tests.ruml_dict import NodeDict, RumlRulemappingLogicFormatDict

PARSER = RumlParser()

ROOT_ID = "0eb360a6-626a-406d-89a1-9f434ced141b"
BRANCH_ID = "1a5b7c3d-2e4f-4a6b-8c9d-0e1f2a3b4c5d"
SHARED_ID = "2b6c8d4e-3f5a-4b7c-9d0e-1f2a3b4c5d6e"


def shared_node(*, modular: bool | None, children: list[str] | None = None) -> NodeDict:
    shared = node(id=SHARED_ID, operator="AND" if children else None, children=children)
    if modular is not None:
        shared["modular"] = modular
    return shared


def document(nodes: dict[str, NodeDict]) -> RumlRulemappingLogicFormatDict:
    return ruml_document(rulemap={"nodes": nodes})


def two_parents(shared: NodeDict) -> RumlRulemappingLogicFormatDict:
    return document(
        {
            "1": node(id=ROOT_ID, operator="AND", children=["2", "3"]),
            "2": node(id=BRANCH_ID, operator="OR", children=["3"]),
            "3": shared,
        }
    )


@pytest.mark.parametrize("modular", [None, False])
def test_a_node_with_two_parents_must_be_modular(modular: bool | None) -> None:
    # Arrange
    ruml = two_parents(shared_node(modular=modular))

    # Act / Assert
    with pytest.raises(RumlStructuralError) as excinfo:
        PARSER.parse_dict(ruml)
    [violation] = excinfo.value.violations
    assert violation.rule == "MOD-01"
    assert violation.paths == ["/rulemap/nodes/3"]


def test_a_modular_node_may_have_two_parents() -> None:
    # Arrange
    ruml = two_parents(shared_node(modular=True))

    # Act
    parsed = PARSER.parse_dict(ruml)

    # Assert
    assert parsed.nodes["3"].modular is True


def test_a_self_reference_counts_as_a_reference() -> None:
    # Arrange: node 2 is a child of the root and of itself
    ruml = document(
        {
            "1": node(id=ROOT_ID, operator="AND", children=["2"]),
            "2": node(id=BRANCH_ID, operator="XOR", children=["3", "2"]),
            "3": shared_node(modular=None),
        }
    )

    # Act / Assert
    with pytest.raises(RumlStructuralError) as excinfo:
        PARSER.parse_dict(ruml)
    [violation] = excinfo.value.violations
    assert violation.rule == "MOD-01"
    assert violation.paths == ["/rulemap/nodes/2"]


def test_a_node_referenced_once_needs_no_flag() -> None:
    # Arrange
    ruml = document(
        {
            "1": node(id=ROOT_ID, operator="AND", children=["3"]),
            "3": shared_node(modular=None),
        }
    )

    # Act
    parsed = PARSER.parse_dict(ruml)

    # Assert
    assert parsed.nodes["3"].modular is None
