# SPDX-FileCopyrightText: 2026 Rulemapping Group GmbH
# SPDX-License-Identifier: Apache-2.0
"""The spec's rule that context inputs name declared context entries (chapter 4.11)."""

from collections.abc import Iterator

from ruml_parser.internal.ruml import (
    AiQueryNodeCapability,
    ContextId,
    LexId,
    RumlDocument,
)


def reject_undeclared_context_inputs(document: RumlDocument) -> None:
    """Raise if an ai-query names a context id the root does not declare.

    Every id in the ``inputs.context`` of a node's ``ruml:ai-query`` must have an
    entry in the root-level ``ruml:context`` data (spec chapter 4.11). The schema
    cannot relate a node's ids to the root's, so the rule is checked here; all
    offending nodes are reported at once. Consumers of the parsed document (e.g.
    the evaluator's prompt and attachment builders) may assume every named id
    resolves.

    Raises:
        ValueError: Naming every offending node and the ids it names undeclared.
    """
    context = document.capabilities.context
    root_levels_context_ids = (
        context.data.keys() if context is not None else frozenset()
    )
    offences = [
        f"node {lex_id!r} -> context_id {context_id!r}"
        for lex_id, context_id in _context_inputs(document)
        if context_id not in root_levels_context_ids
    ]
    if offences:
        raise ValueError(
            "Some nodes reference undeclared contexts: "
            + "; ".join(offences)
            + " (spec chapter 4.11: context inputs name root-level context entries)"
        )


def _context_inputs(document: RumlDocument) -> Iterator[tuple[LexId, ContextId]]:
    """Yield every ``(lex_id, context id)`` an ai-query inputs, in document order."""
    for lex_id, ai_query in document.all_node_capabilities_of_type(
        AiQueryNodeCapability
    ):
        for context_input in ai_query.inputs.context:
            yield lex_id, context_input.id
