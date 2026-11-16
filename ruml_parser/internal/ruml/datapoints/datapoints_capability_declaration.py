# SPDX-FileCopyrightText: 2026 Rulemapping Group GmbH
# SPDX-License-Identifier: Apache-2.0
from collections.abc import Mapping
from dataclasses import dataclass, field

from ruml_parser.internal.ruml.aliases import (
    CapabilityRole,
    DatapointId,
    OfficialCapabilityId,
    SetId,
)
from ruml_parser.internal.ruml.capability.abstract_capability_declaration import (
    AbstractCapabilityDeclaration,
)
from ruml_parser.internal.ruml.datapoints.datapoint import Datapoint
from ruml_parser.internal.ruml.datapoints.datapoint_set import DatapointSet


@dataclass(frozen=True, slots=True, kw_only=True)
class DatapointsCapabilityDeclaration(AbstractCapabilityDeclaration):
    id = str(OfficialCapabilityId.ruml_datapoints)
    role = CapabilityRole.data

    required: bool = False
    """Whether this capability must be resolved to evaluate"""
    data: Mapping[DatapointId, Datapoint] = field(default_factory=dict)
    """Datapoint definitions, keyed by datapoint id"""
    sets: Mapping[SetId, DatapointSet] = field(default_factory=dict)
    """Reusable structured types, keyed by set id"""
