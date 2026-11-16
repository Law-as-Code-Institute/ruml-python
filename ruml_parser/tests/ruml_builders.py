# SPDX-FileCopyrightText: 2026 Rulemapping Group GmbH
# SPDX-License-Identifier: Apache-2.0
"""Builders for RUML documents as the JSON objects the parser accepts.

Typed with the generated TypedDicts of `ruml_dict`, so that a misspelled key or a wrong
enum value in a test document is a type error rather than a validation error at
runtime. Keyword arguments are named after the JSON keys they set.
"""

from typing import Any, Literal, cast

from ruml_parser.model.ruml import OfficialCapabilityId
from ruml_parser.tests.ruml_dict import (
    ActionsDict,
    AiQueryPayloadDict,
    CapabilitiesDict,
    CapabilityAiQueryNodeDict,
    CapabilityEntryDict,
    CapabilityQueryDict,
    ContextPayloadDict,
    ContextRefsDict,
    DatapointsPayloadDict,
    DecisionModeDict,
    MetadataDict,
    NodeCapabilitiesDict,
    NodeCapabilityEntryDict,
    NodeDict,
    OperatorDict,
    ProtocolPayloadDict,
    RulemapDict,
    RumlRulemappingLogicFormatDict,
    TextReferencePayloadDict,
    TextRefsDict,
)

NODE_ID = "71946db2-13e2-49df-9f7b-59369cff7679"
DOCUMENT_ID = "499d279c-694e-4bf8-a4ba-9b198ea5a224"
TIMESTAMP = "2026-08-20T12:00:00Z"

type RootPayloadDict = (
    DatapointsPayloadDict
    | TextReferencePayloadDict
    | ContextPayloadDict
    | AiQueryPayloadDict
    | ProtocolPayloadDict
)
"""The payload shapes `CapabilityEntryDict` admits for a root capability entry."""

type NodePayloadDict = (
    CapabilityQueryDict
    | ActionsDict
    | ContextRefsDict
    | CapabilityAiQueryNodeDict
    | TextRefsDict
)
"""The payload shapes `NodeCapabilityEntryDict` admits for a node capability entry."""


def ruml_document(
    *,
    metadata: MetadataDict | None = None,
    capabilities: CapabilitiesDict | None = None,
    rulemap: RulemapDict | None = None,
) -> RumlRulemappingLogicFormatDict:
    """A minimal valid RUML document with a single node, unless overridden."""
    document: RumlRulemappingLogicFormatDict = {
        "$format": "RUML",
        "$specVersion": "1.0",
        "metadata": minimal_metadata() if metadata is None else metadata,
        "rulemap": {"nodes": {"1": node()}} if rulemap is None else rulemap,
    }
    if capabilities is not None:
        document["capabilities"] = capabilities
    return document


def minimal_metadata() -> MetadataDict:
    return {
        "id": DOCUMENT_ID,
        "version": "1.0.0",
        "created": TIMESTAMP,
        "modified": TIMESTAMP,
        "status": "draft",
    }


def node(
    *,
    id: str = NODE_ID,
    label: str = "root",
    operator: OperatorDict | None = "undefined",
    children: list[str] | None = None,
    capabilities: NodeCapabilitiesDict | None = None,
    metadata: dict[str, Any] | None = None,
    decisionMode: DecisionModeDict | None = None,
) -> NodeDict:
    """A node. Pass `operator=None` for a leaf outside a draft, which has none (NODE-07)."""
    result: NodeDict = {"id": id, "label": label}
    if operator is not None:
        result["operator"] = operator
    if children is not None:
        result["children"] = children
    if capabilities is not None:
        result["capabilities"] = capabilities
    if metadata is not None:
        result["metadata"] = metadata
    if decisionMode is not None:
        result["decisionMode"] = decisionMode
    return result


def capability(
    capability_id: str,
    payload: RootPayloadDict | None = None,
    *,
    required: bool | None = None,
    role: Literal["data", "decision", "combiner", "reaction"] | None = None,
) -> CapabilityEntryDict:
    """A root capability entry `{id, payload, required, role}`."""
    entry: CapabilityEntryDict = {"id": capability_id}
    if payload is not None:
        entry["payload"] = payload
    if required is not None:
        entry["required"] = required
    if role is not None:
        entry["role"] = role
    return entry


def node_capability(
    capability_id: str, payload: NodePayloadDict
) -> NodeCapabilityEntryDict:
    """A node capability entry `{id, payload}`; both are required (CAP-17)."""
    return {"id": capability_id, "payload": payload}


def unchecked_capability(
    capability_id: str,
    payload: dict[str, Any],
    *,
    required: bool | None = None,
    role: Literal["data", "decision", "combiner", "reaction"] | None = None,
) -> CapabilityEntryDict:
    """A root capability entry with a payload the TypedDicts cannot vouch for.

    That is a third-party or draft capability's payload, whose shape the schema does
    not define, or one deliberately of the wrong shape for its id.
    """
    return capability(
        capability_id, cast(RootPayloadDict, payload), required=required, role=role
    )


def unchecked_node_capability(
    capability_id: str, payload: dict[str, Any]
) -> NodeCapabilityEntryDict:
    """A node capability entry with a payload the TypedDicts cannot vouch for.

    See `unchecked_capability`.
    """
    return node_capability(capability_id, cast(NodePayloadDict, payload))


def node_with_capabilities(
    *capabilities: NodeCapabilityEntryDict,
) -> RumlRulemappingLogicFormatDict:
    """A document whose single node carries `capabilities`, all declared at the root.

    A non-official id is declared with the `data` role, which it must declare (CAP-03).
    """
    return ruml_document(
        capabilities=[
            capability(entry["id"])
            if is_official(entry["id"])
            else capability(entry["id"], role="data")
            for entry in capabilities
        ],
        rulemap={"nodes": {"1": node(capabilities=list(capabilities))}},
    )


def is_official(capability_id: str) -> bool:
    """Whether ``capability_id`` is one of the spec's own ``ruml:`` ids."""
    return capability_id in {str(id) for id in OfficialCapabilityId}
