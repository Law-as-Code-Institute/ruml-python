# SPDX-FileCopyrightText: 2026 Rulemapping Group GmbH
# SPDX-License-Identifier: Apache-2.0
"""The spec's rule that nothing contains the root node (chapter 3.5.1)."""

from ruml_parser.internal.ruml import BranchNode, RumlDocument
from ruml_parser.schema_validation import json_pointer
from ruml_parser.structural_error import RumlStructuralError, StructuralViolation

ROOT_LEX_ID = "1"


def reject_root_as_child(document: RumlDocument) -> None:
    """Raise if the root node `"1"` appears in a `children` array (rule NODE-05).

    This holds for a modular root as well: recursion (MOD-02) is open to any other node.

    Raises:
        RumlStructuralError: With one NODE-05 violation, at every such entry.
    """
    paths = [
        json_pointer(("rulemap", "nodes", lex_id, "children", index))
        for lex_id, node in document.nodes.items()
        if isinstance(node, BranchNode)
        for index, child in enumerate(node.children)
        if child == ROOT_LEX_ID
    ]
    if paths:
        raise RumlStructuralError(
            [
                StructuralViolation(
                    rule="NODE-05",
                    message="the root node '1' is listed as a child",
                    paths=paths,
                )
            ]
        )
