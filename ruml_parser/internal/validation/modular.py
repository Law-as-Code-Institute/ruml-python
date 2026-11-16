# SPDX-FileCopyrightText: 2026 Rulemapping Group GmbH
# SPDX-License-Identifier: Apache-2.0
"""The spec's rule on which nodes must be marked as modular (chapter 6.2)."""

from collections import Counter

from ruml_parser.internal.ruml import BranchNode, RumlDocument
from ruml_parser.schema_validation import json_pointer
from ruml_parser.structural_error import RumlStructuralError, StructuralViolation


def reject_unmarked_modular_nodes(document: RumlDocument) -> None:
    """Raise if a node is referenced more than once without being `modular`.

    A node whose LexID appears more than once in the `children` arrays of the rulemap
    must have `modular: true` (spec chapter 6.2, rule MOD-01). Every appearance counts:
    in two parents, twice in one parent, and a node's reference to itself. The schema
    cannot count across nodes, so the rule is checked here.

    Raises:
        RumlStructuralError: With one MOD-01 violation per offending node, at the node.
    """
    references = Counter(
        child
        for node in document.nodes.values()
        if isinstance(node, BranchNode)
        for child in node.children
    )
    violations = [
        StructuralViolation(
            rule="MOD-01",
            message=f"node {lex_id!r} is referenced {count} times as a child"
            " but is not marked `modular: true`",
            paths=[json_pointer(("rulemap", "nodes", lex_id))],
        )
        for lex_id, count in references.items()
        if count > 1
        and (node := document.nodes.get(lex_id)) is not None
        and node.modular is not True
    ]
    if violations:
        raise RumlStructuralError(violations)
