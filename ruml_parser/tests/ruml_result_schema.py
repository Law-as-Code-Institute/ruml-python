# SPDX-FileCopyrightText: 2026 Rulemapping Group GmbH
# SPDX-License-Identifier: Apache-2.0
"""Validation of RUML-Result documents against `ruml-result.schema.json` (ruml-schema).

The generated `ruml_result` model is a loosened approximation of the schema: codegen
does not follow the `if`/`then` rules that pick a capability entry's payload schema by
its id, so a payload the model accepts may still violate the schema. Tests that produce
result documents check them against the schema itself with `assert_valid_ruml_result`.
"""

import json
from collections.abc import Mapping
from functools import lru_cache
from typing import Any

import jsonschema

from ruml_parser.schema_files import RESULT_SCHEMA_PATH


@lru_cache(maxsize=1)
def _validator() -> jsonschema.protocols.Validator:
    schema = json.loads(RESULT_SCHEMA_PATH.read_text(encoding="utf-8"))
    validator_cls = jsonschema.validators.validator_for(schema)
    validator_cls.check_schema(schema)
    return validator_cls(schema)


def assert_valid_ruml_result(document: Mapping[str, Any]) -> None:
    """Assert that ``document``, a RUML-Result in its JSON form, satisfies the schema.

    Raises:
        AssertionError: Listing every violation with its JSON path.
    """
    errors = list(_validator().iter_errors(document))
    assert not errors, "\n".join(f"{e.json_path}: {e.message}" for e in errors)
