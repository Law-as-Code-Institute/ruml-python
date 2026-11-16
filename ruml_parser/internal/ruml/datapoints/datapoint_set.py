# SPDX-FileCopyrightText: 2026 Rulemapping Group GmbH
# SPDX-License-Identifier: Apache-2.0
from collections.abc import Mapping
from dataclasses import dataclass

from ruml_parser.internal.ruml.aliases import DatapointId
from ruml_parser.internal.ruml.datapoints.datapoint import Datapoint


@dataclass(frozen=True, slots=True, kw_only=True)
class DatapointSet:
    """A reusable structured type: a named group of datapoints (§4.7.4)."""

    name: str
    """Display name of the set (at least one character)"""
    description: str | None = None
    """What the set represents"""
    fields: Mapping[DatapointId, Datapoint]
    """Member datapoints, keyed by datapoint id; a field may itself be of type 'object'
    (nesting)"""
