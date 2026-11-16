# SPDX-FileCopyrightText: 2026 Rulemapping Group GmbH
# SPDX-License-Identifier: Apache-2.0
"""RUML models for internal use: dataclass "twins" of `ruml_parser.model.ruml`.

The Pydantic models in `ruml_parser.model.ruml` are generated from the JSON schema and
remain the public parsing API, but they inherit every limitation of the schema (itself
constrained by what is expressible in JSON Schema), the code generator, and of what a
single Pydantic model can express: capability entries whose payload type is not selected
by their id, `anyOf` workarounds rendered as `Actions1 | Actions2 | Actions3`, placeholder
names like `Type1`, optional collections that mean the same as empty ones, and so on.
This package is the hand-written twin that fixes those where it matters;
`ruml_parser.internal.mapping` translates a validated Pydantic document into it.

Conventions:

- Instances are only ever built from validated Pydantic models, so the dataclasses carry
  no validation and no constraints. Where the schema constrains a string (a pattern or a
  length), the docstring records it for the reader. The spec's cross-object rules, which
  no type can express, are checked by `ruml_parser.internal.validation` on the built
  document instead.
- Names are snake_case, and generated placeholder names get real ones (`Type1` →
  `DatapointType`).
- Collections *of entries* (children, tags, capability data maps, metadata) are never
  optional: an absent one is an empty one. Free-form *payload* objects (`content`,
  `source`, `config`, `default_value`) stay optional because absence is meaningful
  there. Fields with a schema default take that default instead of `None`.
- Instances are frozen. Sequences and maps are typed as `Sequence` and `Mapping` (built
  as lists and dicts) so they do not invite mutation either.
- Enums are reused from the generated module: they are plain `StrEnum`s whose members
  are the spec's to choose, so a copy would add nothing but a second place to edit.

Keeping in sync: every field of both sides is named in the mappers, so a field that the
regenerated `ruml.py` renames, retypes or removes fails type checking. A field the
schema *adds* is not flagged that way — after `make update-ruml-models`, diff `ruml.py`
for additions and decide whether this model should carry them.
"""

from ruml_parser.internal.ruml.actions.actions_capability_declaration import (
    ActionsCapabilityDeclaration,
)
from ruml_parser.internal.ruml.actions.actions_node_capability import (
    Action,
    ActionsNodeCapability,
)
from ruml_parser.internal.ruml.ai_query.ai_query_capability_declaration import (
    AiQueryCapabilityDeclaration,
    AiQueryDeclarationConfig,
)
from ruml_parser.internal.ruml.ai_query.ai_query_node_capability import (
    AiQueryNodeCapability,
    AiQueryNodeConfig,
    ContextInput,
    QueryInputs,
)
from ruml_parser.internal.ruml.aliases import (
    CapabilityId,
    CapabilityPayload,
    CapabilityRole,
    ContextCategory,
    ContextId,
    ContextRole,
    ContextType,
    DatapointId,
    DatapointType,
    DecisionMode,
    DerivationType,
    DocumentStatus,
    DocumentType,
    Effort,
    ExternalSourceType,
    Hash,
    LanguageCode,
    LegislativeStatus,
    LexId,
    OfficialCapabilityId,
    Operator,
    ProtocolLevel,
    SetId,
    TextAnchorType,
    TextId,
    TextType,
)
from ruml_parser.internal.ruml.capability.abstract_capability_declaration import (
    AbstractCapabilityDeclaration,
)
from ruml_parser.internal.ruml.capability.abstract_node_capability import (
    AbstractNodeCapability,
)
from ruml_parser.internal.ruml.capability.capability_declaration import (
    CapabilityDeclarationWithData,
    DraftCapabilityDeclaration,
    ExtensionCapabilityDeclaration,
)
from ruml_parser.internal.ruml.capability.capability_declarations import (
    CapabilityDeclarations,
)
from ruml_parser.internal.ruml.capability.extension_node_capability import (
    ExtensionNodeCapability,
)
from ruml_parser.internal.ruml.capability.node_capabilities import (
    NodeCapabilities,
    NodeCapability,
)
from ruml_parser.internal.ruml.capability.other_node_capability import (
    OtherNodeCapability,
)
from ruml_parser.internal.ruml.context.context import Context
from ruml_parser.internal.ruml.context.context_capability_declaration import (
    ContextCapabilityDeclaration,
)
from ruml_parser.internal.ruml.context.context_refs_node_capability import (
    ContextRefsNodeCapability,
)
from ruml_parser.internal.ruml.datapoints.datapoint import (
    Cardinality,
    Datapoint,
    ExternalBinding,
    InputBinding,
    Validation,
)
from ruml_parser.internal.ruml.datapoints.datapoint_set import DatapointSet
from ruml_parser.internal.ruml.datapoints.datapoints_capability_declaration import (
    DatapointsCapabilityDeclaration,
)
from ruml_parser.internal.ruml.datapoints.option import Option
from ruml_parser.internal.ruml.expression.expression_capability_declaration import (
    ExpressionCapabilityDeclaration,
)
from ruml_parser.internal.ruml.expression.expression_node_capability import (
    ExpressionNodeCapability,
)
from ruml_parser.internal.ruml.metadata import Author, DerivedFrom, Metadata
from ruml_parser.internal.ruml.nodes.abstract_node import AbstractNode
from ruml_parser.internal.ruml.nodes.branch_node import BranchNode
from ruml_parser.internal.ruml.nodes.leaf_node import LeafNode
from ruml_parser.internal.ruml.nodes.node import Node
from ruml_parser.internal.ruml.protocol.protocol_capability_declaration import (
    ProtocolCapabilityDeclaration,
    ProtocolConfig,
)
from ruml_parser.internal.ruml.query.query_capability_declaration import (
    QueryCapabilityDeclaration,
)
from ruml_parser.internal.ruml.query.query_node_capability import QueryNodeCapability
from ruml_parser.internal.ruml.ruml_document import RumlDocument
from ruml_parser.internal.ruml.text_reference.text import Text, TextSource
from ruml_parser.internal.ruml.text_reference.text_reference_capability_declaration import (
    TextReferenceCapabilityDeclaration,
)
from ruml_parser.internal.ruml.text_reference.text_refs_node_capability import (
    TextAnchor,
    TextRefsNodeCapability,
)
from ruml_parser.internal.ruml.tree.tree_capability_declarations import (
    TreeIncludeCapabilityDeclaration,
    TreeReferenceCapabilityDeclaration,
)

__all__ = [
    "AbstractCapabilityDeclaration",
    "AbstractNode",
    "AbstractNodeCapability",
    "Action",
    "ActionsCapabilityDeclaration",
    "ActionsNodeCapability",
    "AiQueryCapabilityDeclaration",
    "AiQueryDeclarationConfig",
    "AiQueryNodeCapability",
    "AiQueryNodeConfig",
    "Author",
    "BranchNode",
    "CapabilityDeclarationWithData",
    "CapabilityDeclarations",
    "CapabilityId",
    "CapabilityPayload",
    "CapabilityRole",
    "Cardinality",
    "Context",
    "ContextCapabilityDeclaration",
    "ContextCategory",
    "ContextId",
    "ContextInput",
    "ContextRefsNodeCapability",
    "ContextRole",
    "ContextType",
    "Datapoint",
    "DatapointId",
    "DatapointSet",
    "DatapointType",
    "DatapointsCapabilityDeclaration",
    "DecisionMode",
    "DerivationType",
    "DerivedFrom",
    "DocumentStatus",
    "DocumentType",
    "Effort",
    "DraftCapabilityDeclaration",
    "ExpressionCapabilityDeclaration",
    "ExpressionNodeCapability",
    "ExtensionCapabilityDeclaration",
    "ExtensionNodeCapability",
    "ExternalBinding",
    "ExternalSourceType",
    "Hash",
    "InputBinding",
    "LanguageCode",
    "LeafNode",
    "LegislativeStatus",
    "LexId",
    "Metadata",
    "Node",
    "NodeCapabilities",
    "NodeCapability",
    "OfficialCapabilityId",
    "Operator",
    "Option",
    "OtherNodeCapability",
    "ProtocolCapabilityDeclaration",
    "ProtocolConfig",
    "ProtocolLevel",
    "QueryCapabilityDeclaration",
    "QueryInputs",
    "QueryNodeCapability",
    "RumlDocument",
    "SetId",
    "Text",
    "TextAnchor",
    "TextAnchorType",
    "TextId",
    "TextReferenceCapabilityDeclaration",
    "TextRefsNodeCapability",
    "TextSource",
    "TextType",
    "TreeIncludeCapabilityDeclaration",
    "TreeReferenceCapabilityDeclaration",
    "Validation",
]
