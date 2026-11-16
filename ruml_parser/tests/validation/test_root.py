# SPDX-FileCopyrightText: 2026 Rulemapping Group GmbH
# SPDX-License-Identifier: Apache-2.0
"""§3.5.1, NODE-05: the root node `"1"` must not appear in any `children` array."""

import pytest
from ruml_parser.ruml_parser import RumlParser
from ruml_parser.structural_error import RumlStructuralError
from ruml_parser.tests.ruml_builders import node, ruml_document

PARSER = RumlParser()

ROOT_ID = "0eb360a6-626a-406d-89a1-9f434ced141b"
BRANCH_ID = "1a5b7c3d-2e4f-4a6b-8c9d-0e1f2a3b4c5d"
LEAF_ID = "2b6c8d4e-3f5a-4b7c-9d0e-1f2a3b4c5d6e"


def test_a_root_listed_by_its_child_is_rejected() -> None:
    # Arrange
    ruml = ruml_document(
        rulemap={
            "nodes": {
                "1": node(id=ROOT_ID, operator="AND", children=["2"]),
                "2": node(id=BRANCH_ID, operator="XOR", children=["3", "1"]),
                "3": node(id=LEAF_ID),
            }
        }
    )

    # Act / Assert
    with pytest.raises(RumlStructuralError) as excinfo:
        PARSER.parse_dict(ruml)
    [violation] = excinfo.value.violations
    assert violation.rule == "NODE-05"
    assert violation.paths == ["/rulemap/nodes/2/children/1"]


def test_a_modular_root_must_not_recurse_either() -> None:
    # Arrange
    root = node(id=ROOT_ID, operator="XOR", children=["2", "1"])
    root["modular"] = True
    ruml = ruml_document(rulemap={"nodes": {"1": root, "2": node(id=LEAF_ID)}})

    # Act / Assert
    with pytest.raises(RumlStructuralError) as excinfo:
        PARSER.parse_dict(ruml)
    assert [violation.rule for violation in excinfo.value.violations] == ["NODE-05"]


def test_a_modular_node_below_the_root_may_recurse() -> None:
    # Arrange: MOD-02
    recursive = node(id=BRANCH_ID, operator="XOR", children=["3", "2"])
    recursive["modular"] = True
    ruml = ruml_document(
        rulemap={
            "nodes": {
                "1": node(id=ROOT_ID, operator="AND", children=["2"]),
                "2": recursive,
                "3": node(id=LEAF_ID),
            }
        }
    )

    # Act
    parsed = PARSER.parse_dict(ruml)

    # Assert
    assert parsed.nodes["2"].modular is True
