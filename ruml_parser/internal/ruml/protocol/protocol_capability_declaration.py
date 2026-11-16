# SPDX-FileCopyrightText: 2026 Rulemapping Group GmbH
# SPDX-License-Identifier: Apache-2.0
from dataclasses import dataclass, field

from ruml_parser.internal.ruml.aliases import (
    CapabilityRole,
    OfficialCapabilityId,
    ProtocolLevel,
)
from ruml_parser.internal.ruml.capability.abstract_capability_declaration import (
    AbstractCapabilityDeclaration,
)


@dataclass(frozen=True, slots=True, kw_only=True)
class ProtocolConfig:
    level: ProtocolLevel = ProtocolLevel.standard
    """Verbosity of the recorded protocol"""


@dataclass(frozen=True, slots=True, kw_only=True)
class ProtocolCapabilityDeclaration(AbstractCapabilityDeclaration):
    id = str(OfficialCapabilityId.ruml_protocol)
    role = CapabilityRole.reaction

    required: bool = False
    """Whether the engine must write a protocol; one that cannot must not evaluate"""
    config: ProtocolConfig = field(default_factory=ProtocolConfig)
    """Configuration of the protocol to record"""
