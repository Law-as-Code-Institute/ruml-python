# SPDX-FileCopyrightText: 2026 Rulemapping Group GmbH
# SPDX-License-Identifier: Apache-2.0
"""Interfaces for extensions to the parser."""

from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from ruml_parser.internal.ruml import (
    CapabilityId,
    CapabilityPayload,
    ExtensionCapabilityDeclaration,
    ExtensionNodeCapability,
    RumlDocument,
)


@dataclass(frozen=True, slots=True, kw_only=True)
class PayloadSchemas:
    """The JSON Schemas of a capability's payloads, at the root and on a node."""

    root: Mapping[str, Any]
    """JSON Schema document (draft 2020-12) of the root-level declaration's payload"""
    node: Mapping[str, Any]
    """JSON Schema document (draft 2020-12) of a node-level entry's payload"""


class CapabilityExtension(ABC):
    """Draft/3rd-party capability extension for the parser.

    Draft and third-party capability payloads are (almost by definition) "free-form" in
    the official RUML schema, and would therefore normally be represented as generic
    ``DraftCapabilityDeclaration``/``CapabilityDeclarationWithData``/
    ``OtherNodeCapability`` instances in the internal model returned by the parser. For
    a given capability, implementations of this interface facilitate the representation
    as models specific to that capability instead.

    Before that, ``ruml_parser.ruml_parser.RumlParser`` checks the payloads against the
    extension's ``payload_schemas``.
    """

    @property
    @abstractmethod
    def id(self) -> CapabilityId:
        """The id of the capability this extension models; never an official one."""

    @property
    @abstractmethod
    def payload_schemas(self) -> PayloadSchemas:
        """The JSON Schemas of the capability's payloads."""

    @abstractmethod
    def declaration(
        self, payload: CapabilityPayload, *, required: bool
    ) -> ExtensionCapabilityDeclaration:
        """Turn a free-form capability root payload into this extension's specific one.

        Args:
            payload: The declaration's payload; an absent one is passed as an empty one.
            required: Whether the declaration marks the capability as required.

        Raises:
            ValueError: If the payload has the wrong shape. A Pydantic
                ``ValidationError`` (``ValueError`` subclass) is reported as such a
                mismatch, naming the capability.
        """

    @abstractmethod
    def node(self, payload: CapabilityPayload) -> ExtensionNodeCapability:
        """Model one node-level entry of the capability.

        Args:
            payload: The entry's payload; an absent one is passed as an empty one.

        Raises:
            ValueError: If the payload has the wrong shape. A Pydantic
                ``ValidationError`` (which is one) is reported as such a mismatch,
                naming the capability.
        """

    def validate(self, document: RumlDocument) -> None:
        """Check the capability's cross-object rules on the document built with it.

        ``to_internal`` calls this after its own checks of the spec's rules, which a
        capability's rules may rely on. Does nothing unless overridden.

        Raises:
            ValueError: If the document violates one of the rules, naming its error
                code.
        """
