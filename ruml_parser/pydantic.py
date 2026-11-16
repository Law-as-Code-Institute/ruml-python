# SPDX-FileCopyrightText: 2026 Rulemapping Group GmbH
# SPDX-License-Identifier: Apache-2.0
"""Support for using rulemaps in Pydantic models and similar structures."""

from collections.abc import Mapping
from functools import cache
from typing import Annotated, Any, NoReturn

import jsonschema
from pydantic import GetPydanticSchema, ValidationError
from pydantic_core import InitErrorDetails, PydanticCustomError, core_schema

from ruml_parser.internal.ruml import RumlDocument
from ruml_parser.model.ruml import RumlRulemappingLogicFormat
from ruml_parser.ruml_parser import RumlParser
from ruml_parser.schema_validation import RumlValidationError, offending_path


@cache
def _parser() -> RumlParser:
    """Build the parser of every `ParsedRumlDocument`, on first use rather than import."""
    return RumlParser()


def _parse(
    value: Any, handler: core_schema.ValidatorFunctionWrapHandler
) -> RumlDocument:
    """Parse ``value`` with `_parser()`, raising its schema errors as Pydantic ones.

    A mapping (a dict, or decoded JSON) is checked against the schema as it is; anything
    else must validate as the generated model, whose dump is then checked.
    """
    try:
        if isinstance(value, Mapping):
            return _parser().parse_dict(value)
        return _parser().parse_model(handler(value))
    except RumlValidationError as error:
        raise _located_validation_error(error) from error


def _located_validation_error(error: RumlValidationError) -> ValidationError:
    """Turn ``error``'s violations into Pydantic errors, each at its own location.

    Raised from a validator, these show up under the field's location, like the errors
    of a nested model do.
    """
    return ValidationError.from_exception_data(
        RumlRulemappingLogicFormat.__name__,
        [_line_error(violation) for violation in error.errors],
    )


def _line_error(violation: jsonschema.exceptions.ValidationError) -> InitErrorDetails:
    """Convert ``violation`` to Pydantic error details at the location it concerns."""
    return InitErrorDetails(
        type=PydanticCustomError(
            "ruml_schema", "{message}", {"message": violation.message}
        ),
        loc=tuple(offending_path(violation)),
        input=violation.instance,
    )


def _refuse_serialization(document: RumlDocument) -> NoReturn:
    raise TypeError(
        "a RumlDocument cannot be serialized: there is no mapping back to RUML"
    )


# See: https://pydantic.dev/docs/validation/latest/concepts/types/#using-getpydanticschema-to-reduce-boilerplate
ParsedRumlDocument = Annotated[
    RumlDocument,
    GetPydanticSchema(
        lambda _source, handler: core_schema.no_info_wrap_validator_function(
            _parse,
            handler(RumlRulemappingLogicFormat),
            serialization=core_schema.plain_serializer_function_ser_schema(
                _refuse_serialization
            ),
        )
    ),
]
"""Pydantic type that accepts RUML and yields the internal `RumlDocument`.

Parses its input with a `RumlParser`, so it checks the input against the RUML schema
before `to_internal` maps it. Each schema violation becomes an error at the location it
concerns (within the field's), and the `ValueError` that `to_internal` raises becomes
part of the `ValidationError` as usual. Its JSON schema, e.g. in an OpenAPI document, is
that of `RumlRulemappingLogicFormat`, which it also accepts instances of (see
`RumlParser.parse_model` for how those are checked).

A field of this type can't be serialized, as nothing maps a `RumlDocument` back to RUML.

A plain alias rather than a `type` statement, as the latter would show up under its own
name in JSON schemas, making an implementation detail part of e.g. an OpenAPI document.
"""
