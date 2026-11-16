# SPDX-FileCopyrightText: 2026 Rulemapping Group GmbH
# SPDX-License-Identifier: Apache-2.0
"""The spec's rules on how a node may recurse safely (chapter 6.4)."""

import logging
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from enum import StrEnum

from ruml_parser.internal.ruml import BranchNode, LexId, Node, Operator, RumlDocument
from ruml_parser.schema_validation import json_pointer
from ruml_parser.structural_error import RumlStructuralError, StructuralViolation

logger = logging.getLogger(__name__)

UNSAFE_RECURSION_OPERATORS = frozenset(
    {Operator.AND, Operator.NOT_AND, Operator.OR, Operator.NOT_OR}
)
"""The operators §6.4 says a recursive node should not use.

Safe recursion needs an operator that stops as soon as a child becomes `true`, so
that an exit condition before the self-reference can end the recursion. Only
`XOR`/`NOT_XOR` do; under the other four the recursion cannot resolve.
"""


class RecursionFlag(StrEnum):
    """What a rulemap's recursions are flagged for.

    One member per §6.4 rule about a recursive node. The chapter's one remaining
    statement — that such a node `SHOULD NOT` use one of
    `UNSAFE_RECURSION_OPERATORS` — is the same condition as `unsafe_operator`,
    phrased as a recommendation rather than as the warning that member carries,
    so it needs none of its own.

    Declaration order is the order one node's findings are reported in.
    """

    unsafe_operator = "unsafeOperator"
    """A node lists its own lexId among its children and combines them with one of
    `UNSAFE_RECURSION_OPERATORS`. §6.4 requires a warning about it: the evaluation
    is semantically blocked, since no child can end the recursion."""

    self_reference_first = "selfReferenceFirst"
    """The self-reference is the node's first child. §6.4: it `MUST NOT` sit at
    position 0, because an exit condition can only end the recursion if it is
    evaluated before the node re-enters itself."""

    no_exit_condition = "noExitCondition"
    """Every child of the node is the self-reference. §6.4: a recursive node
    `MUST` have at least one non-recursive child, or nothing can ever end it.
    This one implies `self_reference_first`: if every child is the
    self-reference, so is the first."""


class Severity(StrEnum):
    """What §6.4 asks an implementation to do about a flag."""

    warning = "warning"
    """§6.4 asks for a warning and nothing else: the document is legal RUML, and
    whether to evaluate it anyway is the caller's decision."""

    violation = "violation"
    """§6.4 states the rule as `MUST` or `MUST NOT`: the document breaks the spec."""


_SEVERITY: dict[RecursionFlag, Severity] = {
    RecursionFlag.unsafe_operator: Severity.warning,
    RecursionFlag.self_reference_first: Severity.violation,
    RecursionFlag.no_exit_condition: Severity.violation,
}
"""The force §6.4 gives each rule. A member missing here raises `KeyError` on the
first finding that carries it, rather than defaulting to the lenient answer."""


@dataclass(frozen=True)
class RecursionFinding:
    """One flag raised by one node."""

    flag: RecursionFlag
    lex_id: LexId
    """The node the flag is about."""
    operator: Operator
    """That node's operator, so a caller can report it without a second lookup."""

    @property
    def severity(self) -> Severity:
        """What §6.4 asks of this finding.

        Derived from `flag` rather than stored: the normative force belongs to the
        rule, not to the occurrence, so a finding cannot contradict it — and it
        stays out of the dataclass's equality, where it would only repeat what the
        flag already says.
        """
        return _SEVERITY[self.flag]


_VIOLATED_RULE: dict[RecursionFlag, tuple[str, str]] = {
    RecursionFlag.self_reference_first: (
        "MOD-04",
        "the self-reference must not be a recursive node's first child",
    ),
    RecursionFlag.no_exit_condition: (
        "MOD-05",
        "a recursive node must have at least one non-recursive child",
    ),
}
"""The spec rule each violation-severity flag breaks, and what it says.

Only violations appear here: `unsafe_operator` carries no rule code because §6.4
asks for a warning, not a rejection.
"""


def reject_forbidden_recursion(document: RumlDocument) -> None:
    """Act on every §6.4 recursion flag the document's nodes raise (MOD-03 to MOD-05).

    The chapter does not treat its rules alike, so neither does this. A recursion
    under an operator that cannot end it is only logged as a warning: the document
    is legal RUML and is evaluated as usual, the evaluator's depth cap being what
    stops the walk. The other two rules are stated as `MUST`/`MUST NOT`, so a
    document breaking them is rejected.

    Raises:
        RumlStructuralError: With one MOD-04 violation per node whose first child is
            the self-reference, at that child, and one MOD-05 violation per node with
            no other child, at its `children`.
    """
    violations: list[StructuralViolation] = []
    for finding in check_recursion(document.nodes):
        if finding.severity is Severity.violation:
            rule, text = _VIOLATED_RULE[finding.flag]
            path = json_pointer(("rulemap", "nodes", finding.lex_id, "children"))
            if finding.flag is RecursionFlag.self_reference_first:
                path += "/0"
            violations.append(
                StructuralViolation(
                    rule=rule,
                    message=f"node {finding.lex_id!r}: {finding.flag.value}: {text}",
                    paths=[path],
                )
            )
            continue
        logger.warning(
            "Rulemap %s: recursion flagged on node %r (operator %s): %s",
            document.metadata.id,
            finding.lex_id,
            finding.operator.value,
            finding.flag.value,
        )
    if violations:
        raise RumlStructuralError(violations)


def check_recursion(nodes: Mapping[LexId, Node]) -> list[RecursionFinding]:
    """Report every §6.4 recursion flag the nodes raise.

    A diagnostic that never raises; `reject_forbidden_recursion` is the validation
    built on it, splitting the findings into the warnings §6.4 asks for and the
    `MUST`/`MUST NOT` breaches it rejects. A caller wanting the raw findings —
    a linter, say — calls this directly.

    Takes the nodes mapping rather than a `RumlDocument` because the rule reads
    nothing but each node's `operator` and `children`.

    The `modular` flag is deliberately not consulted. §6.4 describes recursion on
    modular nodes, but a self-reference resolves — and blocks — the same way
    without the marker, and the evaluator does not read it either.

    Returns:
        The findings in the order `nodes` iterates and, within one node, in
        `RecursionFlag` declaration order — one node can raise more than one.
    """
    return [
        RecursionFinding(flag=flag, lex_id=lex_id, operator=node.operator)
        for lex_id, node in nodes.items()
        if isinstance(node, BranchNode) and lex_id in node.children
        for flag in _flags_for(lex_id, node)
    ]


def _flags_for(lex_id: LexId, node: Node) -> Iterator[RecursionFlag]:
    """Every flag the recursive `node` raises, in declaration order.

    Args:
        lex_id: The node's own lexId.
        node: The node to check. Must list `lex_id` among its children.
    """
    if not isinstance(node, BranchNode):
        return
    if node.operator in UNSAFE_RECURSION_OPERATORS:
        yield RecursionFlag.unsafe_operator
    # Safe to index: `node` lists `lex_id` among its children, so it has at least one.
    if node.children[0] == lex_id:
        yield RecursionFlag.self_reference_first
    if all(child == lex_id for child in node.children):
        yield RecursionFlag.no_exit_condition
