# SPDX-FileCopyrightText: 2026 Rulemapping Group GmbH
# SPDX-License-Identifier: Apache-2.0
"""The spec's rules on ``ruml:text-reference`` and references to them."""

from collections.abc import Iterator

from ruml_parser.internal.ruml import (
    AiQueryNodeCapability,
    LexId,
    RumlDocument,
    TextId,
)


def reject_undeclared_text_inputs(document: RumlDocument) -> None:
    """Raise if an ai-query names a text id the root does not declare.

    Every id in the ``inputs.texts`` of a node's ``ruml:ai-query`` must have an entry
    in the root-level ``ruml:text-reference`` data (spec chapter 4.9). The schema
    cannot relate a node's ids to the root's, so the rule is checked here. Consumers of
    documents that passed this check may assume every named id resolves.

    Raises:
        ValueError: If one or more referenced texts are undeclared. Names every
            offending node and its undeclared ids.
    """
    text_reference = document.capabilities.text_reference
    root_level_text_ids = (
        text_reference.data.keys() if text_reference is not None else frozenset()
    )
    offences = [
        f"node {lex_id!r} -> text_id {text_id!r}"
        for lex_id, text_id in _text_inputs(document)
        if text_id not in root_level_text_ids
    ]
    if offences:
        raise ValueError(
            "Some nodes reference undeclared texts: "
            + "; ".join(offences)
            + " (spec chapter 4.9: text inputs name root-level text entries)"
        )


def _text_inputs(document: RumlDocument) -> Iterator[tuple[LexId, TextId]]:
    """Yield nodes' ai-query text inputs as ``(lex_id, text id)``, in document order."""
    for lex_id, ai_query in document.all_node_capabilities_of_type(
        AiQueryNodeCapability
    ):
        for text_id in ai_query.inputs.texts:
            yield lex_id, text_id
