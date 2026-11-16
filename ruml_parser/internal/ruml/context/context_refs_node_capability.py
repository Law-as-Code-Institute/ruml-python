# SPDX-FileCopyrightText: 2026 Rulemapping Group GmbH
# SPDX-License-Identifier: Apache-2.0
from collections.abc import Sequence
from dataclasses import dataclass

from ruml_parser.internal.ruml.aliases import ContextId, OfficialCapabilityId
from ruml_parser.internal.ruml.capability.abstract_node_capability import (
    AbstractNodeCapability,
)


@dataclass(frozen=True, slots=True, kw_only=True)
class ContextRefsNodeCapability(AbstractNodeCapability):
    id = str(OfficialCapabilityId.ruml_context)

    refs: Sequence[ContextId]
    """Ids of root-level context entries referenced by the node; at least one"""
