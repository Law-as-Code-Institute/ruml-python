# SPDX-FileCopyrightText: 2026 Rulemapping Group GmbH
# SPDX-License-Identifier: Apache-2.0
"""The spec's rules on capability declarations.

"No implicit capabilities" (chapter 4.3, rule CAP-15), the uniqueness of capability
ids at the root (chapter 4.2, rule CAP-10) and on a node (chapter 4.3, rule CAP-06),
and the combiner's placement (chapter 3.6.4, rules OP-02 and CAP-08).
"""

from collections import Counter
from collections.abc import Sequence
from typing import assert_never

from ruml_parser.internal.ruml import (
    BranchNode,
    CapabilityId,
    CapabilityRole,
    LeafNode,
    OfficialCapabilityId,
    Operator,
    RumlDocument,
)
from ruml_parser.schema_validation import json_pointer
from ruml_parser.structural_error import RumlStructuralError, StructuralViolation

_OFFICIAL_IDS = frozenset(str(official.value) for official in OfficialCapabilityId)


def reject_undeclared_node_capabilities(document: RumlDocument) -> None:
    """Raise if a node uses a capability id the root does not declare.

    Every capability id a node uses must be declared in the root-level `capabilities`,
    whether the parser knows the capability or not (spec chapter 4.3, rule CAP-15: no
    implicit capabilities). The schema cannot relate a node's ids to the root's, so the
    rule is checked here; all offending nodes are reported at once.

    Raises:
        RumlStructuralError: With one CAP-15 violation per offending node, at the
            node's entries of each undeclared id.
    """
    declared = document.capabilities.ids
    violations = [
        StructuralViolation(
            rule="CAP-15",
            message=f"node {lex_id!r} uses capabilities the root does not declare: "
            + ", ".join(repr(capability_id) for capability_id in undeclared),
            paths=[
                json_pointer(("rulemap", "nodes", lex_id, "capabilities", index))
                for index, capability_id in enumerate(node.capabilities.ids)
                if capability_id not in declared
            ],
        )
        for lex_id, node in document.nodes.items()
        if (
            undeclared := list(
                dict.fromkeys(
                    capability_id
                    for capability_id in node.capabilities.ids
                    if capability_id not in declared
                )
            )
        )
    ]
    if violations:
        raise RumlStructuralError(violations)


def reject_duplicate_capability_ids(document: RumlDocument) -> None:
    """Raise if the root lists the same capability id more than once.

    Each capability id appears at most once in the root's `capabilities` list (spec
    chapter 4.2, rule CAP-10); the schema checks that for the official ids only, so
    the rule is checked here. The root's internal model keeps every listed id in
    `declaration_order`, so a duplicate is still visible although the root's fields can
    hold only one entry per id. A node's list may repeat some ids: see
    `reject_repeated_data_capabilities`.

    Raises:
        RumlStructuralError: With one CAP-10 violation per repeated id, at every
            entry of it after the first.
    """
    order = document.capabilities.declaration_order
    violations = [
        StructuralViolation(
            rule="CAP-10",
            message=f"the root declares the capability {capability_id!r} more than once",
            paths=[
                json_pointer(("capabilities", index))
                for index, declared in enumerate(order)
                if declared == capability_id
            ][1:],
        )
        for capability_id, count in Counter(order).items()
        if count > 1
    ]
    if violations:
        raise RumlStructuralError(violations)


def reject_repeated_data_capabilities(document: RumlDocument) -> None:
    """Raise if a node lists a capability with the `data` role more than once.

    On a node, ids with the `decision` or `reaction` role may repeat, but one entry
    carries all of a node's data for a `data` capability (spec chapter 4.3, rule
    CAP-06). The schema enforces this for the official `data` ids only, since it cannot
    see the role a root entry declares for any other. Ids the root does not declare are
    left to `reject_undeclared_node_capabilities`; the combiner role to
    `reject_invalid_number_of_combiners_per_node`.

    Raises:
        RumlStructuralError: With one CAP-06 violation per offending node, at the
            node's entries of each repeated id.
    """
    data_ids = {
        declaration.id
        for declaration in document.capabilities.get_by_role(CapabilityRole.data)
    }
    violations = [
        StructuralViolation(
            rule="CAP-06",
            message=f"node {lex_id!r} carries capabilities with the data role more"
            f" than once: {', '.join(repr(id) for id in repeated)}",
            paths=[
                json_pointer(("rulemap", "nodes", lex_id, "capabilities", index))
                for index, capability_id in enumerate(node.capabilities.ids)
                if capability_id in repeated
            ],
        )
        for lex_id, node in document.nodes.items()
        if (
            repeated := [
                capability_id
                for capability_id, count in Counter(node.capabilities.ids).items()
                if count > 1 and capability_id in data_ids
            ]
        )
    ]
    if violations:
        raise RumlStructuralError(violations)


def reject_invalid_number_of_combiners_per_node(document: RumlDocument) -> None:
    """Raise if a node's combiners break OP-02 or CAP-08.

    A `DELEGATED` node with children has exactly one combiner (OP-02). Without one,
    the node is reported, and with it the root entry of every non-official capability
    on the node: its role is the one declared there, and that is not `combiner`. With
    several, every combiner entry after the first is reported. Any other node has no
    combiner (CAP-08, reported at the node).

    Raises:
        RumlStructuralError: With one violation per offending node.
    """
    violations: list[StructuralViolation] = []
    combiner_cap_ids = {
        declaration.id
        for declaration in document.capabilities.get_by_role(CapabilityRole.combiner)
    }
    for lex_id, node in document.nodes.items():
        if violation := _detect_combiner_violation(
            lex_id, node, combiner_cap_ids, document.capabilities.declaration_order
        ):
            violations.append(violation)
    if violations:
        raise RumlStructuralError(violations)


def _detect_combiner_violation(
    lex_id: str,
    node: LeafNode | BranchNode,
    combiner_ids: set[CapabilityId],
    declaration_order: Sequence[CapabilityId],
) -> StructuralViolation | None:
    combiner_indices = [
        index
        for index, capability in enumerate(node.capabilities.entries)
        if capability.id in combiner_ids
    ]
    nr_combiners = len(combiner_indices)
    node_path = ("rulemap", "nodes", lex_id)
    match node:
        case LeafNode():
            if nr_combiners > 0:
                return StructuralViolation(
                    rule="CAP-08",
                    message=f"node {lex_id!r} has {nr_combiners} combiners"
                    " (a leaf node must not have any combiners)",
                    paths=[json_pointer(node_path)],
                )
        case BranchNode():
            if node.operator == Operator.DELEGATED:
                if nr_combiners == 0:
                    used = set(node.capabilities.ids) - _OFFICIAL_IDS
                    return StructuralViolation(
                        rule="OP-02",
                        message=f"node {lex_id!r} has 0 combiners"
                        " (chapter 3.6.4: a DELEGATED node needs exactly one combiner)",
                        paths=[
                            *(
                                json_pointer(("capabilities", index))
                                for index, declared in enumerate(declaration_order)
                                if declared in used
                            ),
                            json_pointer(node_path),
                        ],
                    )
                if nr_combiners > 1:
                    # The first combiner is the node's; every further one is extra.
                    return StructuralViolation(
                        rule="OP-02",
                        message=f"node {lex_id!r} has {nr_combiners} combiners"
                        " (chapter 3.6.4: a DELEGATED node needs exactly one combiner)",
                        paths=[
                            json_pointer((*node_path, "capabilities", index))
                            for index in combiner_indices[1:]
                        ],
                    )
            elif nr_combiners > 0:
                return StructuralViolation(
                    rule="CAP-08",
                    message=f"node {lex_id!r} has {nr_combiners} combiners"
                    " (a non DELEGATE branch node must not have any combiners)",
                    paths=[json_pointer(node_path)],
                )
        case _ as unreachable:
            assert_never(unreachable)
    return None
