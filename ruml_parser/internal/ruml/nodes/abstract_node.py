# SPDX-FileCopyrightText: 2026 Rulemapping Group GmbH
# SPDX-License-Identifier: Apache-2.0
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from ruml_parser.internal.ruml.aliases import DecisionMode
from ruml_parser.internal.ruml.capability.node_capabilities import NodeCapabilities


@dataclass(frozen=True, slots=True, kw_only=True)
class AbstractNode:
    id: UUID
    """Unique identifier of the node"""
    label: str
    """Human-readable label for the node"""
    alt_text: str | None = None
    """Alternative short-form label or text for the node"""
    description: str | None = None
    """Longer explanation of what the node represents (at most 10000 characters)"""
    capabilities: NodeCapabilities = field(default_factory=NodeCapabilities)
    """Node-level capability values"""
    metadata: Mapping[str, Any] = field(default_factory=dict)
    """Free-form, implementation-defined node metadata"""
    decision_mode: DecisionMode | None = None
    """Combination mode for a leaf node with multiple decision capabilities"""
    modular: bool | None = None
    """Whether the node is a reusable, self-contained module"""
