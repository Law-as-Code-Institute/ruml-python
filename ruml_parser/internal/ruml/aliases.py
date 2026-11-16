# SPDX-FileCopyrightText: 2026 Rulemapping Group GmbH
# SPDX-License-Identifier: Apache-2.0
from collections.abc import Mapping
from typing import Any

from ruml_parser.model import ruml as model

DocumentStatus = model.DocumentStatus


DocumentType = model.DocumentType


DerivationType = model.DerivationType


LegislativeStatus = model.Status


Operator = model.Operator


DecisionMode = model.DecisionMode


DatapointType = model.Type


ExternalSourceType = model.SourceType


TextType = model.Type2


TextAnchorType = model.Type3


ContextCategory = model.Category


ContextType = model.Type4


ContextRole = model.Role


Effort = model.Effort


ProtocolLevel = model.Level


OfficialCapabilityId = model.OfficialCapabilityId


CapabilityRole = model.Role1


type LexId = str
"""Key of a node in the rulemap: a positive integer without leading zeros."""


type DatapointId = str
"""Id of a datapoint: lower-case snake_case, `[a-z_][a-z0-9_]*` (DP-02)."""


type SetId = str
"""Id of a datapoint set: lower-case snake_case, `[a-z_][a-z0-9_]*` (DP-02)."""


type TextId = str
"""Id of a root-level text entry: lower-case snake_case, `[a-z_][a-z0-9_]*` (TXT-02)."""


type ContextId = str
"""Id of a root-level context entry: lower-case snake_case, `[a-z_][a-z0-9_]*` (CTX-04)."""


type CapabilityId = str
"""A capability id: official (`ruml:query`), draft (`ruml:draft/my-capability`) or
third-party in reverse-domain form (`com.example/my-capability`)."""


type Hash = str
"""An integrity hash in the form `<algorithm>:<hex value>`."""


type LanguageCode = str
"""An ISO 639-1 two-letter language code."""


type CapabilityPayload = Mapping[str, Any]
"""Free-form (root or node-level) payload of a capability without a dedicated model."""
