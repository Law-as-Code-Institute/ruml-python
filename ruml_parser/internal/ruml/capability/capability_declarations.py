# SPDX-FileCopyrightText: 2026 Rulemapping Group GmbH
# SPDX-License-Identifier: Apache-2.0
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

from more_itertools import only

from ruml_parser.internal.ruml.actions.actions_capability_declaration import (
    ActionsCapabilityDeclaration,
)
from ruml_parser.internal.ruml.ai_query.ai_query_capability_declaration import (
    AiQueryCapabilityDeclaration,
)
from ruml_parser.internal.ruml.aliases import CapabilityId, CapabilityRole
from ruml_parser.internal.ruml.capability.abstract_capability_declaration import (
    AbstractCapabilityDeclaration,
)
from ruml_parser.internal.ruml.capability.capability_declaration import (
    CapabilityDeclarationWithData,
    DraftCapabilityDeclaration,
    ExtensionCapabilityDeclaration,
)
from ruml_parser.internal.ruml.context.context_capability_declaration import (
    ContextCapabilityDeclaration,
)
from ruml_parser.internal.ruml.datapoints.datapoints_capability_declaration import (
    DatapointsCapabilityDeclaration,
)
from ruml_parser.internal.ruml.expression.expression_capability_declaration import (
    ExpressionCapabilityDeclaration,
)
from ruml_parser.internal.ruml.protocol.protocol_capability_declaration import (
    ProtocolCapabilityDeclaration,
)
from ruml_parser.internal.ruml.query.query_capability_declaration import (
    QueryCapabilityDeclaration,
)
from ruml_parser.internal.ruml.text_reference.text_reference_capability_declaration import (
    TextReferenceCapabilityDeclaration,
)
from ruml_parser.internal.ruml.tree.tree_capability_declarations import (
    TreeIncludeCapabilityDeclaration,
    TreeReferenceCapabilityDeclaration,
)
from ruml_parser.model import ruml as model

#
# The schema declares a capability as an entry `{id, required, payload}` whose payload
# schema depends on the id. The classes here merge entry and payload into one object
# per capability: `required` sits next to the payload's fields, and the id is the
# `CapabilityDeclarations` field (or key) the object is held under.
#
# Every declaration is an `AbstractCapabilityDeclaration`, which knows its `id` and the
# `role` it plays (§4.1). Draft and third-party ids must declare theirs (CAP-03). An
# official id's role is fixed by its chapter, and its entry must not declare one
# (CAP-05); an extension fixes its capability's role, and the entry must declare the
# same (CAP-04).
# `CapabilityDeclarations.get_by_id()` answers for any declared id.


@dataclass(frozen=True, slots=True, kw_only=True)
class CapabilityDeclarations:
    """Root-level capability declarations.

    Replaces the generated `list[CapabilityEntry]`, whose payload is a free-form object
    whatever the entry's id: here each official capability is a field of the type the
    schema prescribes for it, and the draft and third-party ones are grouped by kind,
    each keyed by its id.
    """

    datapoints: DatapointsCapabilityDeclaration | None = None
    """`ruml:datapoints`"""
    text_reference: TextReferenceCapabilityDeclaration | None = None
    """`ruml:text-reference`"""
    tree_reference: TreeReferenceCapabilityDeclaration | None = None
    """`ruml:tree-reference`"""
    tree_include: TreeIncludeCapabilityDeclaration | None = None
    """`ruml:tree-include`"""
    context: ContextCapabilityDeclaration | None = None
    """`ruml:context`"""
    query: QueryCapabilityDeclaration | None = None
    """`ruml:query`"""
    ai_query: AiQueryCapabilityDeclaration | None = None
    """`ruml:ai-query`"""
    expression: ExpressionCapabilityDeclaration | None = None
    """`ruml:expression`"""
    actions: ActionsCapabilityDeclaration | None = None
    """`ruml:actions`"""
    protocol: ProtocolCapabilityDeclaration | None = None
    """`ruml:protocol`"""
    draft: Mapping[CapabilityId, DraftCapabilityDeclaration] = field(
        default_factory=dict
    )
    """Draft capabilities (`ruml:draft/...`), keyed by id"""
    third_party: Mapping[CapabilityId, CapabilityDeclarationWithData] = field(
        default_factory=dict
    )
    """Third-party capabilities (`com.example/...`), keyed by id"""
    extensions: Mapping[CapabilityId, ExtensionCapabilityDeclaration] = field(
        default_factory=dict
    )
    """Draft or third-party capabilities modeled by an extension, keyed by id; these
    are in neither ``draft`` nor ``third_party``"""
    declaration_order: Sequence[CapabilityId] = field(default_factory=list)
    """Every id declared, in the order the document declares the capabilities in.

    The fields above cannot keep that order, which the spec makes significant (§4.2).
    When left empty, it is derived from the fields (in field order, ``draft``,
    ``third_party`` and ``extensions`` keys last), so hand-built instances need not
    spell it out.
    """

    def __post_init__(self) -> None:
        if self.declaration_order:
            return
        official = {
            model.OfficialCapabilityId.ruml_datapoints: self.datapoints,
            model.OfficialCapabilityId.ruml_text_reference: self.text_reference,
            model.OfficialCapabilityId.ruml_tree_reference: self.tree_reference,
            model.OfficialCapabilityId.ruml_tree_include: self.tree_include,
            model.OfficialCapabilityId.ruml_context: self.context,
            model.OfficialCapabilityId.ruml_query: self.query,
            model.OfficialCapabilityId.ruml_ai_query: self.ai_query,
            model.OfficialCapabilityId.ruml_expression: self.expression,
            model.OfficialCapabilityId.ruml_actions: self.actions,
            model.OfficialCapabilityId.ruml_protocol: self.protocol,
        }
        derived = [
            *(str(id) for id, value in official.items() if value is not None),
            *self.draft,
            *self.third_party,
            *self.extensions,
        ]
        object.__setattr__(self, "declaration_order", derived)  # frozen

    @property
    def ids(self) -> frozenset[CapabilityId]:
        """Every declared capability id, official or not."""
        return frozenset(self.declaration_order)

    def extension[T: ExtensionCapabilityDeclaration](self, kind: type[T]) -> T | None:
        """Return the declaration of type ``kind`` in ``extensions``, or ``None``."""
        return only(
            (
                declared
                for declared in self.extensions.values()
                if isinstance(declared, kind)
            ),
            default=None,
        )

    def get_by_id(self, capability_id: CapabilityId) -> AbstractCapabilityDeclaration:
        """Return the declaration of the capability with the given id.

        Its ``role`` is the one the capability plays (§4.1).

        Raises:
            KeyError: `capability_id` is not declared.
        """
        match capability_id:
            case model.OfficialCapabilityId.ruml_datapoints if self.datapoints:
                return self.datapoints
            case model.OfficialCapabilityId.ruml_text_reference if self.text_reference:
                return self.text_reference
            case model.OfficialCapabilityId.ruml_tree_reference if self.tree_reference:
                return self.tree_reference
            case model.OfficialCapabilityId.ruml_tree_include if self.tree_include:
                return self.tree_include
            case model.OfficialCapabilityId.ruml_context if self.context:
                return self.context
            case model.OfficialCapabilityId.ruml_query if self.query:
                return self.query
            case model.OfficialCapabilityId.ruml_ai_query if self.ai_query:
                return self.ai_query
            case model.OfficialCapabilityId.ruml_expression if self.expression:
                return self.expression
            case model.OfficialCapabilityId.ruml_actions if self.actions:
                return self.actions
            case model.OfficialCapabilityId.ruml_protocol if self.protocol:
                return self.protocol
            case _ if capability_id in self.extensions:
                return self.extensions[capability_id]
            case _ if capability_id in self.draft:
                return self.draft[capability_id]
            case _ if capability_id in self.third_party:
                return self.third_party[capability_id]
            case _:
                raise KeyError(capability_id)

    def get_by_role(self, role: CapabilityRole) -> list[AbstractCapabilityDeclaration]:
        """Return the declarations of every capability playing ``role`` (§4.1).

        They come in declaration order, each once even if its id is declared twice.
        """
        return [
            declaration
            for capability_id in dict.fromkeys(self.declaration_order)
            if (declaration := self.get_by_id(capability_id)).role == role
        ]
