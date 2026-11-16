# SPDX-FileCopyrightText: 2026 Rulemapping Group GmbH
# SPDX-License-Identifier: Apache-2.0
from collections.abc import Sequence
from dataclasses import dataclass

from more_itertools import only

from ruml_parser.internal.ruml.actions.actions_node_capability import (
    ActionsNodeCapability,
)
from ruml_parser.internal.ruml.ai_query.ai_query_node_capability import (
    AiQueryNodeCapability,
)
from ruml_parser.internal.ruml.aliases import CapabilityId
from ruml_parser.internal.ruml.capability.extension_node_capability import (
    ExtensionNodeCapability,
)
from ruml_parser.internal.ruml.capability.other_node_capability import (
    OtherNodeCapability,
)
from ruml_parser.internal.ruml.context.context_refs_node_capability import (
    ContextRefsNodeCapability,
)
from ruml_parser.internal.ruml.expression.expression_node_capability import (
    ExpressionNodeCapability,
)
from ruml_parser.internal.ruml.query.query_node_capability import QueryNodeCapability
from ruml_parser.internal.ruml.text_reference.text_refs_node_capability import (
    TextRefsNodeCapability,
)

type NodeCapability = (
    QueryNodeCapability
    | ActionsNodeCapability
    | ContextRefsNodeCapability
    | AiQueryNodeCapability
    | TextRefsNodeCapability
    | ExpressionNodeCapability
    | ExtensionNodeCapability
    | OtherNodeCapability
)
"""One node-level capability entry."""


@dataclass(frozen=True, slots=True, kw_only=True)
class NodeCapabilities:
    """Node-level capability values.

    Replaces the generated `list[NodeCapabilityEntry]`: each entry is the typed model
    of its capability — or an `OtherNodeCapability` for ids without a node-level model —
    kept in declaration order, which the spec makes significant (§4.3): the decision
    modes depend on it.

    In a spec-compliant document, every capability here is also declared in the
    root-level `CapabilityDeclarations` (see `RumlDocument`).
    """

    entries: Sequence[NodeCapability] = ()
    """The node's capability entries, in declaration order"""

    def __post_init__(self) -> None:
        object.__setattr__(self, "entries", tuple(self.entries))  # frozen

    def all_of_type[EntryT: NodeCapability](self, clazz: type[EntryT]) -> list[EntryT]:
        return [entry for entry in self.entries if isinstance(entry, clazz)]

    @property
    def ids(self) -> list[CapabilityId]:
        """Every id present, in declaration order; a duplicate appears repeatedly."""
        return [entry.id for entry in self.entries]

    @property
    def actions(self) -> list[ActionsNodeCapability]:
        """`ruml:actions`, in declaration order; a reaction may repeat (CAP-06)"""
        return self.all_of_type(ActionsNodeCapability)

    @property
    def expression(self) -> ExpressionNodeCapability | None:
        """`ruml:expression`"""
        return self._sole(ExpressionNodeCapability)

    @property
    def context(self) -> ContextRefsNodeCapability | None:
        """`ruml:context`"""
        return self._sole(ContextRefsNodeCapability)

    @property
    def text_reference(self) -> TextRefsNodeCapability | None:
        """`ruml:text-reference`"""
        return self._sole(TextRefsNodeCapability)

    @property
    def extensions(self) -> Sequence[ExtensionNodeCapability]:
        # TODO: Müssen wir nicht eigentlich gewährleisten, dass auch **Extension**-
        # Capabilities in der **Rolle** zurückgegeben werden, in der sie gebraucht
        # werden?
        return self.all_of_type(ExtensionNodeCapability)

    def _sole[EntryT: NodeCapability](self, kind: type[EntryT]) -> EntryT | None:
        """Return the entry of type ``kind``, or `None`.

        For a `data` or `combiner` capability only: their ids do not repeat on a node
        (CAP-06, OP-02).
        """
        return only(
            self.all_of_type(kind),
            default=None,
            # TODO: This can be an AssertionError once `to_internal` rejects repeated
            # entries (CAP-06, OP-02) before anything reads them.
            too_long=ValueError(
                f"Expected at most one {kind.__name__} entry (CAP-06, OP-02)"
            ),
        )
