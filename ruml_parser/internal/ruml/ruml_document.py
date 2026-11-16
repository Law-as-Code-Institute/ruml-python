# SPDX-FileCopyrightText: 2026 Rulemapping Group GmbH
# SPDX-License-Identifier: Apache-2.0
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field

from ruml_parser.internal.ruml.aliases import LexId
from ruml_parser.internal.ruml.capability.capability_declarations import (
    CapabilityDeclarations,
)
from ruml_parser.internal.ruml.capability.node_capabilities import NodeCapability
from ruml_parser.internal.ruml.metadata import Metadata
from ruml_parser.internal.ruml.nodes.node import Node


@dataclass(frozen=True, slots=True, kw_only=True)
class RumlDocument:
    """A RUML file.

    The `$format` discriminator is dropped (it is a constant, and this class already
    says what the object is), and the `rulemap` wrapper object, whose only content is
    `nodes`, is flattened into `nodes`.
    """

    spec_version: str
    """RUML spec version the file conforms to"""
    metadata: Metadata
    """Metadata about the RUML file itself"""
    capabilities: CapabilityDeclarations = field(default_factory=CapabilityDeclarations)
    """Root-level capability declarations.
    
    As per spec chapter 4.3, these are required for capabilities that are used at the
    node level (rule CAP-15).
    """
    nodes: Mapping[LexId, Node]
    """The decision logic tree: the rulemap nodes, keyed by lexId"""

    def all_node_capabilities_of_type[T: NodeCapability](
        self, capability_type: type[T]
    ) -> Iterable[tuple[LexId, T]]:
        """
        Return all capabilities of type ``capability_type`` from all nodes
        """
        for lex_id, node in self.nodes.items():
            for capability in node.capabilities.all_of_type(capability_type):
                yield (lex_id, capability)
