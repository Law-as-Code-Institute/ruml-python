# SPDX-FileCopyrightText: 2026 Rulemapping Group GmbH
# SPDX-License-Identifier: Apache-2.0
from abc import ABC, abstractmethod

from ruml_parser.internal.ruml.aliases import CapabilityId, CapabilityRole


class AbstractCapabilityDeclaration(ABC):
    """Base class for all root-level capability declarations."""

    @property
    @abstractmethod
    def id(self) -> CapabilityId:
        """The id of the declared capability."""

    @property
    @abstractmethod
    def role(self) -> CapabilityRole:
        """The role the capability plays (§4.1).

        Fixed by its chapter for an official id, and by the extension for an extension
        capability; declared in the document for any other.
        """
