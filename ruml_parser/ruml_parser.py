# SPDX-FileCopyrightText: 2026 Rulemapping Group GmbH
# SPDX-License-Identifier: Apache-2.0
"""``RumlParser``: RUML in any of its forms, parsed into the internal ``RumlDocument``."""

import json
from collections.abc import Iterable, Mapping
from typing import Any

from ruml_parser.internal.extension import CapabilityExtension
from ruml_parser.internal.mapping import to_internal
from ruml_parser.internal.ruml import RumlDocument
from ruml_parser.model.ruml import RumlRulemappingLogicFormat
from ruml_parser.schema_validation import RumlValidationError, ruml_validator


class RumlParser:
    """Parses RUML into the internal model, modeling the capabilities of ``extensions``.

    Every ``parse_*`` method checks its input against the RUML schema and the
    extensions' payload schemas, then maps it with ``to_internal``, which checks the
    spec's cross-object rules and the extensions' own.

    The generated Pydantic model alone is not a faithful validator: codegen drops the
    schema's top-level ``allOf`` cross-field rules and cannot follow the ``if``/``then``
    rules that pick a capability payload's schema by its id (see
    scripts/update_models.py). Validating against the schema first catches what the
    model would silently accept.

    The schema validator is built once, on construction, so reuse an instance rather
    than creating one per document.

    Raises (from every ``parse_*`` method):
        RumlValidationError: If the document violates the RUML schema or an
            extension's payload schema.
        ValueError: If it violates a rule that ``to_internal`` checks; see there.
    """

    def __init__(self, *, extensions: Iterable[CapabilityExtension] = ()) -> None:
        self._extensions = tuple(extensions)
        self._validator = ruml_validator(self._extensions)

    def parse_json(self, ruml: str | bytes) -> RumlDocument:
        """Parse a RUML document given as JSON text.

        Raises:
            json.JSONDecodeError: If ``ruml`` is not JSON (a ``ValueError`` as well).
        """
        return self.parse_dict(json.loads(ruml))

    def parse_dict(self, ruml: Mapping[str, Any]) -> RumlDocument:
        """Parse a RUML document given as decoded JSON, e.g. from ``json.loads``."""
        self._validate_schema(ruml)
        return self._to_internal(RumlRulemappingLogicFormat.model_validate(ruml))

    def parse_model(self, ruml: RumlRulemappingLogicFormat) -> RumlDocument:
        """Parse a RUML document given as the generated Pydantic model.

        The model accepts documents the schema rejects (see the class docstring), so it is
        dumped back to JSON to be checked against the schema as well. Its dump
        reflects what the model holds, though, not the JSON it was validated from:
        values the model normalizes (e.g. an upper-case UUID) pass even where the
        schema rejects their original form.
        """
        self._validate_schema(
            ruml.model_dump(mode="json", by_alias=True, exclude_unset=True)
        )
        return self._to_internal(ruml)

    def _validate_schema(self, ruml: Mapping[str, Any]) -> None:
        errors = list(self._validator.iter_errors(ruml))
        if errors:
            raise RumlValidationError(errors)

    def _to_internal(self, ruml: RumlRulemappingLogicFormat) -> RumlDocument:
        return to_internal(ruml, self._extensions)
