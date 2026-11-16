# SPDX-FileCopyrightText: 2026 Rulemapping Group GmbH
# SPDX-License-Identifier: Apache-2.0
"""A capability extension for tests: ``com.example/greeting``, of made-up shape."""

from dataclasses import dataclass
from typing import TypedDict, override

from pydantic import TypeAdapter

from ruml_parser.internal.extension import CapabilityExtension, PayloadSchemas
from ruml_parser.internal.ruml import (
    CapabilityPayload,
    CapabilityRole,
    ExtensionCapabilityDeclaration,
    ExtensionNodeCapability,
)

GREETING_ID = "com.example/greeting"

GREETING_PAYLOAD_SCHEMAS = PayloadSchemas(
    root={
        "type": "object",
        "properties": {"salutation": {"type": "string"}},
        "required": ["salutation"],
        "additionalProperties": False,
    },
    node={
        "type": "object",
        "properties": {"name": {"type": "string"}},
        "required": ["name"],
        "additionalProperties": False,
    },
)


@dataclass(frozen=True, slots=True, kw_only=True)
class GreetingsCapabilityDeclaration(ExtensionCapabilityDeclaration):
    id = GREETING_ID
    role = CapabilityRole.data

    required: bool = False
    salutation: str


@dataclass(frozen=True, slots=True, kw_only=True)
class GreetingNodeCapability(ExtensionNodeCapability):
    id = GREETING_ID
    name: str


class GreetingsPayload(TypedDict):
    salutation: str


class GreetingPayload(TypedDict):
    name: str


class GreetingExtension(CapabilityExtension):
    id = GREETING_ID
    payload_schemas = GREETING_PAYLOAD_SCHEMAS

    @override
    def declaration(
        self, payload: CapabilityPayload, *, required: bool
    ) -> GreetingsCapabilityDeclaration:
        parsed = TypeAdapter(GreetingsPayload).validate_python(payload)
        return GreetingsCapabilityDeclaration(
            required=required, salutation=parsed["salutation"]
        )

    @override
    def node(self, payload: CapabilityPayload) -> GreetingNodeCapability:
        parsed = TypeAdapter(GreetingPayload).validate_python(payload)
        return GreetingNodeCapability(name=parsed["name"])
