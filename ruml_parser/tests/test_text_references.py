# SPDX-FileCopyrightText: 2026 Rulemapping Group GmbH
# SPDX-License-Identifier: Apache-2.0
"""§4.12: a node's `ruml:text-reference` payload anchors into the document's own texts."""

import pytest

from ruml_parser.internal import ruml as internal
from ruml_parser.internal.mapping import to_internal
from ruml_parser.model.ruml import RumlRulemappingLogicFormat
from ruml_parser.ruml_parser import RumlParser
from ruml_parser.schema_validation import RumlValidationError
from ruml_parser.tests.ruml_builders import (
    TIMESTAMP,
    capability,
    node,
    node_capability,
    ruml_document,
    unchecked_node_capability,
)
from ruml_parser.tests.ruml_dict import (
    NodeCapabilityEntryDict,
    RumlRulemappingLogicFormatDict,
)

ELEMENT = "4c1f0a52-8f7e-4b4a-9d0e-2a6b3c8e1f10"

PARSER = RumlParser()


def document(text_reference: NodeCapabilityEntryDict) -> RumlRulemappingLogicFormatDict:
    """A document declaring the text `text_1` and a node carrying ``text_reference``."""
    return ruml_document(
        capabilities=[
            capability(
                "ruml:text-reference",
                {
                    "data": {
                        "text_1": {
                            "title": "BGB § 823",
                            "uri": "/akn/de/act/1896-08-18/bgb#sec_823",
                            "timestamp": TIMESTAMP,
                            "status": "inForce",
                            "text": "Wer vorsätzlich…",
                        }
                    }
                },
            )
        ],
        rulemap={"nodes": {"1": node(capabilities=[text_reference])}},
    )


@pytest.mark.parametrize(
    "payload",
    [{}, {"normRef": {"id": "text_1"}}, {"refs": [{"id": "text_1"}]}],
    ids=["empty", "former normRef", "untyped anchor"],
)
def test_a_payload_without_typed_anchors_is_rejected_by_the_schema(
    payload: dict[str, object],
) -> None:
    # Arrange
    raw = document(unchecked_node_capability("ruml:text-reference", payload))

    # Act / Assert
    with pytest.raises(RumlValidationError) as excinfo:
        PARSER.parse_dict(raw)
    assert excinfo.value.paths
    assert all(
        path.startswith("/rulemap/nodes/1/capabilities/0/payload")
        for path in excinfo.value.paths
    )


def test_anchors_map_with_their_type_and_element() -> None:
    # Arrange
    raw = document(
        node_capability(
            "ruml:text-reference",
            {
                "refs": [
                    {"id": "text_1", "element": ELEMENT, "type": "represents"},
                    {"id": "text_1", "type": "refers-to"},
                ]
            },
        )
    )

    # Act
    result = to_internal(RumlRulemappingLogicFormat.model_validate(raw))

    # Assert
    text_reference = result.nodes["1"].capabilities.text_reference
    represents = internal.TextAnchor(
        id="text_1", element=ELEMENT, type=internal.TextAnchorType.represents
    )
    assert text_reference == internal.TextRefsNodeCapability(
        refs=[
            represents,
            internal.TextAnchor(id="text_1", type=internal.TextAnchorType.refers_to),
        ]
    )
