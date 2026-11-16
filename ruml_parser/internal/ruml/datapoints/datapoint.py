# SPDX-FileCopyrightText: 2026 Rulemapping Group GmbH
# SPDX-License-Identifier: Apache-2.0
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

from ruml_parser.internal.ruml.aliases import DatapointType, ExternalSourceType, SetId
from ruml_parser.internal.ruml.datapoints.option import Option


@dataclass(frozen=True, slots=True, kw_only=True)
class InputBinding:
    """The datapoint value is supplied by user input."""

    hint: str | None = None
    """Hint shown to the user when entering the value"""
    placeholder: str | None = None
    """Placeholder text for the input field"""
    default_value: Any | None = None
    """Default value pre-filled for the input"""


@dataclass(frozen=True, slots=True, kw_only=True)
class ExternalBinding:
    """The datapoint value is fetched from an external source."""

    ref: str
    """Symbolic reference to the external source"""
    description: str | None = None
    """Description of the external source"""
    source_type: ExternalSourceType | None = None
    """Kind of external source the value is fetched from"""
    fallback: InputBinding | None = None
    """Input binding used when the external source cannot be reached"""


@dataclass(frozen=True, slots=True, kw_only=True)
class Validation:
    """Validation rules applied to a datapoint value.

    Unlike elsewhere in this model, `None` means "not specified" for every field here,
    `required` included: the schema declares no defaults for them.
    """

    required: bool | None = None
    """Whether a value must be provided"""
    min: float | str | None = None
    """Minimum value (number, or ISO-8601 string for temporal types)"""
    max: float | str | None = None
    """Maximum value (number, or ISO-8601 string for temporal types)"""
    min_length: int | None = None
    """Minimum length of the value"""
    max_length: int | None = None
    """Maximum length of the value"""
    pattern: str | None = None
    """Regular expression the value must match"""
    enum: Sequence[Any] | None = None
    """Explicit set of allowed values"""
    message: str | None = None
    """Custom validation error message"""


@dataclass(frozen=True, slots=True, kw_only=True)
class Cardinality:
    """How often an object datapoint repeats (§4.7.4).

    A datapoint without a cardinality is a single object; a `max` above one makes its
    value a list of objects. Like `Validation`, `None` means "not specified" here: the
    schema declares no defaults for the bounds.
    """

    min: int | None = None
    """Least number of objects; zero or more"""
    max: int | None = None
    """Greatest number of objects; one or more"""


@dataclass(frozen=True, slots=True, kw_only=True)
class Datapoint:
    name: str
    """Human-readable name of the datapoint"""
    type: DatapointType
    """Data type of the datapoint"""
    description: str | None = None
    """Description of what the datapoint represents"""
    unit: str | None = None
    """Unit of the value; required for type 'currency'"""
    sensitive: bool = False
    """Whether the datapoint holds sensitive/personal data"""
    format: str | None = None
    """Format refining the type (e.g. taxId for identifier)"""
    options: Sequence[Option] = field(default_factory=list)
    """Allowed options; required and non-empty for type 'enum'"""
    binding: InputBinding | ExternalBinding
    """How the datapoint value is sourced"""
    validation: Validation | None = None
    """Validation rules applied to the datapoint value"""
    set: SetId | None = None
    """The set this datapoint instantiates; required when type is 'object' (§4.7.4)"""
    cardinality: Cardinality | None = None
    """Repetition of the object; absent means a single object"""
