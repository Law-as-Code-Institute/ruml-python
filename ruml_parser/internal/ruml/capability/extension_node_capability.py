# SPDX-FileCopyrightText: 2026 Rulemapping Group GmbH
# SPDX-License-Identifier: Apache-2.0
from dataclasses import dataclass

from ruml_parser.internal.ruml.capability.abstract_node_capability import (
    AbstractNodeCapability,
)


@dataclass(frozen=True, slots=True, kw_only=True)
class ExtensionNodeCapability(AbstractNodeCapability):
    """Base class for node-level entries of a capability an extension models.

    The extension is a ``ruml_parser.internal.extension.CapabilityExtension``.
    Subclasses are dataclasses defined by the extension, frozen like this one, with the
    capability's id as a class attribute.
    """
