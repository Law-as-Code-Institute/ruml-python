# SPDX-FileCopyrightText: 2026 Rulemapping Group GmbH
# SPDX-License-Identifier: Apache-2.0
from abc import ABC
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from ruml_parser.internal.ruml.aliases import CapabilityId, CapabilityRole
from ruml_parser.internal.ruml.capability.abstract_capability_declaration import (
    AbstractCapabilityDeclaration,
)


@dataclass(frozen=True, slots=True, kw_only=True)
class DraftCapabilityDeclaration(AbstractCapabilityDeclaration):
    """Root-level declaration of a draft capability (`ruml:draft/...`, `PlainPayload`)."""

    id: CapabilityId = field()
    """The id of the declared capability"""
    required: bool = False
    """Whether this capability must be resolved to evaluate"""
    role: CapabilityRole = field()
    """The role the capability declares (§4.1; CAP-03 makes declaring it mandatory)"""
    config: Mapping[str, Any] | None = None
    """Capability-specific configuration"""


@dataclass(frozen=True, slots=True, kw_only=True)
class CapabilityDeclarationWithData(AbstractCapabilityDeclaration):
    """Root-level declaration of a third-party capability (payload left open)."""

    id: CapabilityId = field()
    """The id of the declared capability"""
    required: bool = False
    """Whether this capability must be resolved to evaluate"""
    role: CapabilityRole = field()
    """The role the capability declares (§4.1; CAP-03 makes declaring it mandatory)"""
    data: Mapping[str, Any] = field(default_factory=dict)
    """Capability-specific data payload, keyed by entry id"""
    config: Mapping[str, Any] | None = None
    """Capability-specific configuration"""


@dataclass(frozen=True, slots=True, kw_only=True)
class ExtensionCapabilityDeclaration(AbstractCapabilityDeclaration, ABC):
    """Base class for root-level declarations of a capability an extension models.

    The extension is a ``ruml_parser.internal.extension.CapabilityExtension``.
    Subclasses are dataclasses defined by the extension, frozen like this one, with the
    entry's ``required`` flag next to the payload's fields, and the capability's ``id``
    and ``role`` as class attributes.
    """
