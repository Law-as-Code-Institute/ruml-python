# SPDX-FileCopyrightText: 2026 Rulemapping Group GmbH
# SPDX-License-Identifier: Apache-2.0
"""§4.13: the `ruml:protocol` declaration."""

import pytest

from ruml_parser.internal import ruml as internal
from ruml_parser.ruml_parser import RumlParser
from ruml_parser.schema_validation import RumlValidationError
from ruml_parser.tests.ruml_builders import (
    capability,
    node_with_capabilities,
    ruml_document,
    unchecked_node_capability,
)

PARSER = RumlParser()


def test_declaration_without_payload_maps_to_the_defaults() -> None:
    # Arrange
    document = ruml_document(capabilities=[capability("ruml:protocol")])

    # Act
    result = PARSER.parse_dict(document)

    # Assert
    assert result.capabilities.protocol == internal.ProtocolCapabilityDeclaration(
        required=False,
        config=internal.ProtocolConfig(level=internal.ProtocolLevel.standard),
    )


def test_node_level_payload_is_rejected() -> None:
    # Arrange: the capability is a directive to the engine, with no node-level payload
    document = node_with_capabilities(
        unchecked_node_capability("ruml:protocol", {"config": {"level": "verbose"}})
    )

    # Act / Assert
    with pytest.raises(RumlValidationError) as excinfo:
        PARSER.parse_dict(document)
    assert excinfo.value.paths == ["/rulemap/nodes/1/capabilities/0"]
