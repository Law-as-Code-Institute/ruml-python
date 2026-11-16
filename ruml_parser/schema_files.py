# SPDX-FileCopyrightText: 2026 Rulemapping Group GmbH
# SPDX-License-Identifier: Apache-2.0
"""Paths of & metadata handling for the RUML JSON Schema files.

The files come with the `ruml-schema` package, which this package pins to the version
its models are generated from.
"""

import json
from pathlib import Path

from ruml_schema import RUML_RESULT_SCHEMA_PATH, RUML_SCHEMA_PATH

SCHEMA_PATH = RUML_SCHEMA_PATH
"""The RUML schema."""

RESULT_SCHEMA_PATH = RUML_RESULT_SCHEMA_PATH
"""The RUML-Result schema."""


def schema_id(path: Path) -> str:
    """Read the ``$id`` that the schema file at ``path`` declares."""
    return json.loads(path.read_text(encoding="utf-8"))["$id"]
