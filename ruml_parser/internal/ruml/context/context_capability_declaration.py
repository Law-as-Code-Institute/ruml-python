# SPDX-FileCopyrightText: 2026 Rulemapping Group GmbH
# SPDX-License-Identifier: Apache-2.0
from collections.abc import Mapping
from dataclasses import dataclass, field

from ruml_parser.internal.ruml.aliases import (
    CapabilityRole,
    ContextId,
    OfficialCapabilityId,
)
from ruml_parser.internal.ruml.capability.abstract_capability_declaration import (
    AbstractCapabilityDeclaration,
)
from ruml_parser.internal.ruml.context.context import Context


@dataclass(frozen=True, slots=True, kw_only=True)
class ContextCapabilityDeclaration(AbstractCapabilityDeclaration):
    id = str(OfficialCapabilityId.ruml_context)
    role = CapabilityRole.data

    required: bool = False
    """Whether this capability must be resolved to evaluate"""
    data: Mapping[ContextId, Context] = field(default_factory=dict)
    """Context entries, keyed by context id"""
