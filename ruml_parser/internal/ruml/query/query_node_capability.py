# SPDX-FileCopyrightText: 2026 Rulemapping Group GmbH
# SPDX-License-Identifier: Apache-2.0
from dataclasses import dataclass

from ruml_parser.internal.ruml.aliases import OfficialCapabilityId
from ruml_parser.internal.ruml.capability.abstract_node_capability import (
    AbstractNodeCapability,
)


@dataclass(frozen=True, slots=True, kw_only=True)
class QueryNodeCapability(AbstractNodeCapability):
    id = str(OfficialCapabilityId.ruml_query)
    expression: str
    """JSONata expression computing the node's truth value"""
    description: str | None = None
    """Optional explanation of what the expression evaluates"""
