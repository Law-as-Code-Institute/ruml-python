# SPDX-FileCopyrightText: 2026 Rulemapping Group GmbH
# SPDX-License-Identifier: Apache-2.0
from abc import ABC, abstractmethod

from ruml_parser.internal.ruml.aliases import CapabilityId


class AbstractNodeCapability(ABC):
    """Base class for all Node Capabilities."""

    @property
    @abstractmethod
    def id(self) -> CapabilityId:
        pass
