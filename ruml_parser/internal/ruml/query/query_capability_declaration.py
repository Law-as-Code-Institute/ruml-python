# SPDX-FileCopyrightText: 2026 Rulemapping Group GmbH
# SPDX-License-Identifier: Apache-2.0
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from ruml_parser.internal.ruml.aliases import CapabilityRole, OfficialCapabilityId
from ruml_parser.internal.ruml.capability.abstract_capability_declaration import (
    AbstractCapabilityDeclaration,
)


@dataclass(frozen=True, slots=True, kw_only=True)
class QueryCapabilityDeclaration(AbstractCapabilityDeclaration):
    """Root-level declaration of `ruml:query` (`PlainPayload`)."""

    id = str(OfficialCapabilityId.ruml_query)
    role = CapabilityRole.decision

    required: bool = False
    """Whether this capability must be resolved to evaluate"""
    config: Mapping[str, Any] | None = None
    """Capability-specific configuration"""
