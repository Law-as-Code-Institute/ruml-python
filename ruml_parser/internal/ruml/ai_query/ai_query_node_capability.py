# SPDX-FileCopyrightText: 2026 Rulemapping Group GmbH
# SPDX-License-Identifier: Apache-2.0
from collections.abc import Sequence
from dataclasses import dataclass, field

from ruml_parser.internal.ruml.aliases import (
    ContextRole,
    Effort,
    OfficialCapabilityId,
)
from ruml_parser.internal.ruml.capability.abstract_node_capability import (
    AbstractNodeCapability,
)
from ruml_parser.model import ruml as model


@dataclass(frozen=True, slots=True, kw_only=True)
class ContextInput:
    """A context entry supplied as input to an AI query.

    The schema also allows a bare id string, meaning role `reference`; the mapping
    normalizes that to this form.
    """

    id: str
    """Id of the referenced context entry"""
    role: ContextRole = model.Role.reference
    """Role the context plays in the query"""


@dataclass(frozen=True, slots=True, kw_only=True)
class QueryInputs:
    """Inputs supplied to an AI query."""

    context: Sequence[ContextInput] = field(default_factory=list)
    """Context entries supplied as input to the query"""
    datapoints: Sequence[str] = field(default_factory=list)
    """Ids of datapoints supplied as input to the query"""
    texts: Sequence[str] = field(default_factory=list)
    """Ids of texts supplied as input to the query"""


@dataclass(frozen=True, slots=True, kw_only=True)
class AiQueryNodeConfig:
    deterministic: bool | None = None
    """Whether the query should be evaluated deterministically"""
    effort: Effort = model.Effort.medium
    """Effort the model should spend on the query"""
    temperature: float | None = None
    """Sampling temperature for the query, between 0 and 1"""


@dataclass(frozen=True, slots=True, kw_only=True)
class AiQueryNodeCapability(AbstractNodeCapability):
    id = str(OfficialCapabilityId.ruml_ai_query)

    model: str
    """Symbolic reference to the AI model, resolved by the tool at runtime"""
    prompt: str | None = None
    """Prompt evaluated for this node"""
    description: str | None = None
    """Description of what the query determines"""
    inputs: QueryInputs = field(default_factory=QueryInputs)
    """Inputs (context, datapoints, texts) supplied to the query"""
    config: AiQueryNodeConfig | None = None
    """Node-level configuration for the query"""
