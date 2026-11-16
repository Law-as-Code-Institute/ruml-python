# SPDX-FileCopyrightText: 2026 Rulemapping Group GmbH
# SPDX-License-Identifier: Apache-2.0
"""§3.3.2: `metadata.title` and `metadata.description` are plain strings — the
former 100/2000-character limits are gone from the schema.
"""

from ruml_parser.ruml_parser import RumlParser
from ruml_parser.tests.ruml_builders import minimal_metadata, ruml_document

PARSER = RumlParser()


def test_title_and_description_have_no_length_limit() -> None:
    # Arrange: both fields well beyond the former 100/2000-character limits
    metadata = minimal_metadata()
    metadata["title"] = "t" * 150
    metadata["description"] = "d" * 3000
    document = ruml_document(metadata=metadata)

    # Act
    parsed = PARSER.parse_dict(document)

    # Assert
    assert parsed.metadata.title == "t" * 150
    assert parsed.metadata.description == "d" * 3000
