# SPDX-FileCopyrightText: 2026 Rulemapping Group GmbH
# SPDX-License-Identifier: Apache-2.0
from dataclasses import dataclass

from ruml_parser.internal.ruml.aliases import OfficialCapabilityId
from ruml_parser.internal.ruml.capability.abstract_node_capability import (
    AbstractNodeCapability,
)


@dataclass(frozen=True, slots=True, kw_only=True)
class ExpressionNodeCapability(AbstractNodeCapability):
    """The combiner of a `DELEGATED` node (§3.6.2), which computes its status."""

    id = str(OfficialCapabilityId.ruml_expression)
    expression: str
    """JSONata expression computing the node's status from `$children` and the
    datapoints"""
    description: str
    """Human-readable statement of the rule the expression encodes"""
