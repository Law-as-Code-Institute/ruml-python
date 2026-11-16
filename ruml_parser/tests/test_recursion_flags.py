# SPDX-FileCopyrightText: 2026 Rulemapping Group GmbH
# SPDX-License-Identifier: Apache-2.0
"""§6.4: which recursions `check_recursion` flags, and which it leaves alone —
and how `to_internal` enforces the findings (warnings logged, violations rejected)."""

import logging
from uuid import UUID

import pytest

from ruml_parser.internal.mapping import to_internal
from ruml_parser.internal.ruml import BranchNode, LexId, Node, Operator
from ruml_parser.internal.validation.recursion import (
    RecursionFinding,
    RecursionFlag,
    Severity,
    check_recursion,
)
from ruml_parser.model.ruml import RumlRulemappingLogicFormat
from ruml_parser.ruml_parser import RumlParser
from ruml_parser.structural_error import RumlStructuralError
from ruml_parser.tests.ruml_builders import DOCUMENT_ID, NODE_ID, ruml_document
from ruml_parser.tests.ruml_builders import node as node_dict
from ruml_parser.tests.ruml_dict import NodeDict, OperatorDict

UNSAFE_OPERATORS = [Operator.AND, Operator.NOT_AND, Operator.OR, Operator.NOT_OR]
SAFE_OPERATORS = [Operator.XOR, Operator.NOT_XOR]


def node(
    operator: Operator, children: list[LexId], modular: bool | None = True
) -> Node:
    return BranchNode(
        id=UUID(NODE_ID),
        operator=operator,
        label="Verhandlungsrunde",
        children=children,
        modular=modular,
    )


@pytest.mark.parametrize("operator", UNSAFE_OPERATORS)
def test_flags_a_self_reference_under_an_unresolvable_operator(
    operator: Operator,
) -> None:
    # Arrange: the §6.4 negotiation round, but under an operator that cannot exit it.
    nodes = {"1": node(operator, ["2", "3", "1"])}

    # Act
    findings = check_recursion(nodes)

    # Assert
    assert findings == [
        RecursionFinding(
            flag=RecursionFlag.unsafe_operator, lex_id="1", operator=operator
        )
    ]


@pytest.mark.parametrize("operator", SAFE_OPERATORS)
def test_does_not_flag_a_self_reference_under_xor(operator: Operator) -> None:
    """§6.4's safe recursion: XOR/NOT_XOR stop at the first true child."""
    nodes = {"1": node(operator, ["2", "3", "1"])}

    assert check_recursion(nodes) == []


@pytest.mark.parametrize("operator", UNSAFE_OPERATORS + SAFE_OPERATORS)
def test_does_not_flag_a_node_that_does_not_reference_itself(
    operator: Operator,
) -> None:
    """The operator alone is not a finding — only a self-reference under it is."""
    nodes = {"1": node(operator, ["2", "3"])}

    assert check_recursion(nodes) == []


def test_flags_a_self_reference_on_a_node_not_marked_modular() -> None:
    """`modular` is not consulted: the evaluation is blocked with or without it."""
    nodes = {"1": node(Operator.AND, ["2", "1"], modular=None)}

    assert [finding.lex_id for finding in check_recursion(nodes)] == ["1"]


def test_reports_every_offending_node_in_document_order() -> None:
    """A caller that fixes one offender should not be surprised by the next."""
    nodes = {
        "1": node(Operator.XOR, ["2", "3", "1"]),
        "2": node(Operator.OR, ["4", "2"]),
        "3": node(Operator.NOT_AND, ["5", "3"]),
    }

    findings = check_recursion(nodes)

    assert [(finding.lex_id, finding.operator) for finding in findings] == [
        ("2", Operator.OR),
        ("3", Operator.NOT_AND),
    ]


def test_has_no_findings_for_a_rulemap_without_recursion() -> None:
    nodes = {"1": node(Operator.AND, ["2"]), "2": node(Operator.XOR, [])}

    assert check_recursion(nodes) == []


def test_flags_a_self_reference_in_first_position() -> None:
    """§6.4: the self-reference MUST NOT be at position 0.

    Under `XOR` the operator itself is fine, so this isolates the position rule.
    """
    nodes = {"1": node(Operator.XOR, ["1", "2"])}

    assert [finding.flag for finding in check_recursion(nodes)] == [
        RecursionFlag.self_reference_first
    ]


def test_flags_a_recursion_with_no_non_recursive_child() -> None:
    """§6.4: a recursive node MUST have at least one child that can end it.

    A node whose every child is the self-reference raises the position flag too —
    if all children are the self-reference, the first one is as well.
    """
    nodes = {"1": node(Operator.XOR, ["1"])}

    assert [finding.flag for finding in check_recursion(nodes)] == [
        RecursionFlag.self_reference_first,
        RecursionFlag.no_exit_condition,
    ]


def test_reports_a_node_breaking_every_rule_in_declaration_order() -> None:
    """One node can raise several flags at once; their order is the enum's."""
    nodes = {"1": node(Operator.AND, ["1"])}

    assert [finding.flag for finding in check_recursion(nodes)] == [
        RecursionFlag.unsafe_operator,
        RecursionFlag.self_reference_first,
        RecursionFlag.no_exit_condition,
    ]


def test_has_no_findings_for_a_safe_recursion() -> None:
    """§6.4's safe recursion: XOR, self-reference last, with an exit before it."""
    nodes = {"1": node(Operator.XOR, ["2", "1"]), "2": node(Operator.XOR, [])}

    assert check_recursion(nodes) == []


@pytest.mark.parametrize("flag", list(RecursionFlag))
def test_every_flag_carries_a_severity(flag: RecursionFlag) -> None:
    """A new member without an entry must fail here, not default to lenient."""
    finding = RecursionFinding(flag=flag, lex_id="1", operator=Operator.AND)

    assert finding.severity in Severity


def test_severity_follows_the_normative_force_of_each_rule() -> None:
    """§6.4 asks for a warning about the operator; the other two it states as MUST."""
    findings = check_recursion({"1": node(Operator.AND, ["1"])})

    assert {finding.flag: finding.severity for finding in findings} == {
        RecursionFlag.unsafe_operator: Severity.warning,
        RecursionFlag.self_reference_first: Severity.violation,
        RecursionFlag.no_exit_condition: Severity.violation,
    }


def test_severity_stays_out_of_equality() -> None:
    """It is derived, so it cannot make two findings of the same flag differ."""
    findings = check_recursion({"1": node(Operator.XOR, ["1", "2"])})

    assert findings == [
        RecursionFinding(
            flag=RecursionFlag.self_reference_first, lex_id="1", operator=Operator.XOR
        )
    ]


# --- Enforcement: `to_internal` runs `reject_forbidden_recursion` ---

RECURSION_LOGGER = "ruml_parser.internal.validation.recursion"


def document_with(nodes: dict[str, NodeDict]) -> RumlRulemappingLogicFormat:
    return RumlRulemappingLogicFormat.model_validate(
        ruml_document(rulemap={"nodes": nodes})
    )


def leaf(label: str) -> NodeDict:
    return node_dict(label=label)


def recursion_below_the_root(
    operator: OperatorDict, children: list[str]
) -> RumlRulemappingLogicFormat:
    """A document whose node `"2"` recurses (the root may not, NODE-05), `"3"` a leaf."""
    recursive = node_dict(operator=operator, children=children)
    recursive["modular"] = True
    return document_with(
        {
            "1": node_dict(operator="AND", children=["2"]),
            "2": recursive,
            "3": leaf("Angebot angenommen"),
        }
    )


def test_to_internal_rejects_a_self_reference_in_first_position() -> None:
    """§6.4 MUST NOT (MOD-04): the exit condition has to come before the re-entry.

    `XOR` is a safe operator, so the position is the only thing wrong here —
    which isolates the refusal from the operator flag, the one §6.4 only asks
    a warning about.
    """
    document = recursion_below_the_root("XOR", ["2", "3"])

    with pytest.raises(RumlStructuralError) as excinfo:
        to_internal(document)

    [violation] = excinfo.value.violations
    assert (violation.rule, violation.paths) == (
        "MOD-04",
        ["/rulemap/nodes/2/children/0"],
    )


def test_to_internal_rejects_a_recursion_without_exit(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """§6.4 MUST (MOD-05): rejected, not warned about — no child can ever end it."""
    document = recursion_below_the_root("XOR", ["2"])

    with (
        caplog.at_level(logging.WARNING, logger=RECURSION_LOGGER),
        pytest.raises(RumlStructuralError) as excinfo,
    ):
        to_internal(document)

    # Its only child is the self-reference, so it is the first one as well.
    assert [(v.rule, v.paths) for v in excinfo.value.violations] == [
        ("MOD-04", ["/rulemap/nodes/2/children/0"]),
        ("MOD-05", ["/rulemap/nodes/2/children"]),
    ]
    # Refused, not warned about: the warning channel is for the operator rule.
    assert caplog.records == []


def test_the_parser_rejects_a_module_referencing_itself_first() -> None:
    """MOD-04 as a legacy XML import yields it: `<module refid>` to its own node, first."""
    document = ruml_document(
        rulemap={
            "nodes": {
                "1": node_dict(operator="AND", children=["2"]),
                "2": {
                    **node_dict(operator="AND", children=["2", "3"]),
                    "modular": True,
                },
                "3": leaf("Angebot angenommen"),
            }
        }
    )

    with pytest.raises(RumlStructuralError) as excinfo:
        RumlParser().parse_dict(document)

    assert [(v.rule, v.paths) for v in excinfo.value.violations] == [
        ("MOD-04", ["/rulemap/nodes/2/children/0"])
    ]


def test_to_internal_warns_about_an_unresolvable_recursion(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """§6.4 requires the warning — and requires the document to stay accepted.

    `AND` never stops at a true child, so no exit condition can end the
    recursion; the depth cap at evaluation time is what stops the walk.
    """
    document = recursion_below_the_root("AND", ["3", "2"])

    with caplog.at_level(logging.WARNING, logger=RECURSION_LOGGER):
        result = to_internal(document)

    assert "2" in result.nodes
    [record] = caplog.records
    for expected in (DOCUMENT_ID, "'2'", "AND", "unsafeOperator"):
        assert expected in record.getMessage()


def test_to_internal_does_not_warn_about_a_safe_recursion(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """§6.4's safe recursion: `XOR` ends as soon as a child becomes true."""
    document = recursion_below_the_root("XOR", ["3", "2"])

    with caplog.at_level(logging.WARNING, logger=RECURSION_LOGGER):
        to_internal(document)

    assert caplog.records == []
