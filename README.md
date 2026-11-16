# ruml-python

The Python parser for RUML, the Rulemapping Logic Format: Pydantic models, parsing and
validation. RUML is an open, JSON-based file format for the machine-executable
representation of legal decision logic; the specification, the schemas and the
conformance tests are in [ruml](https://github.com/Law-as-Code-Institute/ruml).

RUML-Result is the companion format for the outcome of evaluating a rulemap. This
library is the parsing/validation layer only — it has no evaluation logic.

## Installing

```sh
pip install ruml-parser
```

It needs Python 3.14 or later.

## Usage

### Using RumlParser directly

As its name implies, `RumlParser` can be used to parse a rulemap from JSON text or a
decoded dict:

```python
from ruml_parser import RumlParser

parser = RumlParser()
document = parser.parse_json(json_text)  # or parse_dict(raw_dict)
```

`document.nodes` is a `dict[LexId, Node]`; lexId `"1"` is the rulemap root by convention
(RUML has no explicit root marker).

### Using Pydantic

For easy interoperability with Pydantic and related frameworks (e.g. FastAPI), we also
provide a way to annotate a Pydantic field (or FastAPI parameter) such that it takes
rulemap-structured data (e.g. from JSON) as input and contains a `RumlDocument` once
parsed:

```python
from pydantic import BaseModel
from ruml_parser import ParsedRumlDocument


class OuterModel(BaseModel):
    document: ParsedRumlDocument  # = Annotated[RumlDocument, ...]
```

Note that OpenAPI/JSON Schemas generated from `ParsedRumlDocument` will deviate from the
true RUML JSON Schema a bit due to being internally generated from a set of Pydantic
models that were themselves auto-generated from the original JSON Schema. Refer to
[CONTRIBUTING.md](CONTRIBUTING.md) for details.

`ParsedRumlDocument` can also be used if the RUML document is at the root of the JSON to
be parsed (even though, in this case, one might as well use `RumlParser` directly):

```python
from pydantic import TypeAdapter
from ruml_parser import ParsedRumlDocument

document = TypeAdapter(ParsedRumlDocument).validate_python(raw_dict)  # RumlDocument
```

### Capability extensions

The schema leaves the payloads of draft and third-party capabilities free-form, and so
does the internal model. To work with typed models of such a capability, implement a
`CapabilityExtension` for it and pass it to `RumlParser`. The parser then validates the
capability's payloads against the extension's JSON Schemas (combined with the RUML
schema), parses its root-level declaration and node-level entries into types of the
extension's, and lets it check the capability's cross-object rules on the result:

```python
parser = RumlParser(extensions=[MyCapabilityExtension()])
document = parser.parse_dict(raw_dict)
```

Naturally, `document` can't have any fields that are statically annotated as the types
associated with the extension, so helpers must be used for correctly-typed access:

```python
declaration = document.capabilities.extension(MyCapability)  # MyCapability | None
entries = document.all_node_capabilities_of_type(MyNodeCapability)  # (lexId, entry)s
```

## Contributing

Feedback is welcome as issues; pull requests are not accepted yet. See
[CONTRIBUTING.md](CONTRIBUTING.md).

For information relevant to development of ruml-parser itself, see
[DEVELOPMENT.md](DEVELOPMENT.md).

## Licence

Apache-2.0, see [LICENSE](LICENSE). Copyright 2026 Rulemapping Group GmbH.

Published by Law as Code Institut GmbH. RUML is a trademark of Rulemapping Group GmbH; an
application for registration as an EU trade mark has been filed.
