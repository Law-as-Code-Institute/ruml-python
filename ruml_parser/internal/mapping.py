# SPDX-FileCopyrightText: 2026 Rulemapping Group GmbH
# SPDX-License-Identifier: Apache-2.0
"""Mappers to convert schema-generated RUML models to our hand-written dataclasses.

The entry point is `to_internal` (which `RumlParser` and `ParsedRumlDocument` call);
the rest are the per-type mappers it is built from, named after the type they produce.

As the mapping functions access all fields of both sides (Pydantic + internal), this
module doubles as a kind of "sync check" between both when typechecked. See the
docstring of `ruml_parser.internal.ruml`.
"""

from collections.abc import Callable, Iterable, Mapping
from functools import partial
from typing import Any

from pydantic import BaseModel, TypeAdapter, ValidationError

from ruml_parser.internal.extension import CapabilityExtension
from ruml_parser.internal.ruml import (
    Action,
    ActionsCapabilityDeclaration,
    ActionsNodeCapability,
    AiQueryCapabilityDeclaration,
    AiQueryDeclarationConfig,
    AiQueryNodeCapability,
    AiQueryNodeConfig,
    Author,
    BranchNode,
    CapabilityDeclarations,
    CapabilityDeclarationWithData,
    CapabilityId,
    CapabilityPayload,
    CapabilityRole,
    Cardinality,
    Context,
    ContextCapabilityDeclaration,
    ContextInput,
    ContextRefsNodeCapability,
    Datapoint,
    DatapointId,
    DatapointsCapabilityDeclaration,
    DatapointSet,
    DerivedFrom,
    DraftCapabilityDeclaration,
    ExpressionCapabilityDeclaration,
    ExpressionNodeCapability,
    ExtensionCapabilityDeclaration,
    ExternalBinding,
    InputBinding,
    LeafNode,
    Metadata,
    Node,
    NodeCapabilities,
    NodeCapability,
    Option,
    OtherNodeCapability,
    ProtocolCapabilityDeclaration,
    ProtocolConfig,
    QueryCapabilityDeclaration,
    QueryInputs,
    QueryNodeCapability,
    RumlDocument,
    Text,
    TextAnchor,
    TextReferenceCapabilityDeclaration,
    TextRefsNodeCapability,
    TextSource,
    TreeIncludeCapabilityDeclaration,
    TreeReferenceCapabilityDeclaration,
    Validation,
)
from ruml_parser.internal.validation.capabilities import (
    reject_duplicate_capability_ids,
    reject_invalid_number_of_combiners_per_node,
    reject_repeated_data_capabilities,
    reject_undeclared_node_capabilities,
)
from ruml_parser.internal.validation.contexts import (
    reject_undeclared_context_inputs,
)
from ruml_parser.internal.validation.datapoint_sets import (
    reject_recursive_sets,
    reject_undeclared_set_references,
)
from ruml_parser.internal.validation.modular import reject_unmarked_modular_nodes
from ruml_parser.internal.validation.recursion import reject_forbidden_recursion
from ruml_parser.internal.validation.root import reject_root_as_child
from ruml_parser.internal.validation.texts import reject_undeclared_text_inputs
from ruml_parser.model import ruml as model
from ruml_parser.model.ruml import NodeCapabilityEntry
from ruml_parser.schema_validation import json_pointer
from ruml_parser.structural_error import RumlStructuralError, StructuralViolation

DRAFT_CAPABILITY_ID_PREFIX = "ruml:draft/"
"""Every draft capability id starts with this; no other kind of id does."""

type _CapabilityEntry = model.CapabilityEntry | model.NodeCapabilityEntry
"""A capability entry of either level: `{id, payload}` (plus `required` at the root)."""

_ACTIONS_ADAPTER = TypeAdapter[model.Actions](model.Actions)
"""Validates a node's `ruml:actions` payload; a union, so a `TypeAdapter` is needed."""


def to_internal(
    document: model.RumlRulemappingLogicFormat,
    extensions: Iterable[CapabilityExtension] = (),
) -> RumlDocument:
    """Translate a validated RUML document into the internal model.

    The result also satisfies the spec's cross-object rules, which
    `ruml_parser.internal.validation` checks once the mapping has built it.

    Args:
        document: The document to translate.
        extensions: Models of draft or third-party capabilities the document may use
            (see ``CapabilityExtension``); without one, a capability's entries keep
            their free-form payloads.

    Raises:
        ValueError: If validating the document turned up problems with it. Such issues
            are due to Structural (see ADR 0001) invariants that neither the schema nor
            generated models can or should enforce, so we check them here instead.
    """
    extensions_by_id = {extension.id: extension for extension in extensions}
    result = RumlDocument(
        spec_version=document.field_specVersion,
        metadata=_metadata(document.metadata),
        capabilities=_capabilities(document.capabilities, extensions_by_id),
        nodes={
            lex_id: _node(node, extensions_by_id)
            for lex_id, node in document.rulemap.nodes.items()
        },
    )

    # Validations:
    # This is the Structural category of the error-handling split in ADR 0001 (`docs/
    # adr/0001-error-handling-layers.md`): every error decidable from the RUML document
    # alone belongs here, and must reference a RUML spec error code rather than an
    # invented message.
    reject_duplicate_capability_ids(result)
    reject_undeclared_node_capabilities(result)
    reject_repeated_data_capabilities(result)
    reject_undeclared_context_inputs(result)
    reject_undeclared_text_inputs(result)
    reject_undeclared_set_references(result)
    reject_recursive_sets(result)
    reject_root_as_child(result)
    reject_unmarked_modular_nodes(result)
    reject_forbidden_recursion(result)
    reject_invalid_number_of_combiners_per_node(result)
    for extension in extensions_by_id.values():
        extension.validate(result)

    return result


# --- Metadata ---------------------------------------------------------------------------


def _metadata(src: model.Metadata) -> Metadata:
    return Metadata(
        id=src.id,
        title=src.title,
        description=src.description,
        version=src.version,
        created=src.created,
        modified=src.modified,
        status=src.status,
        comment=src.comment,
        document_type=src.documentType,
        authors=[_author(author) for author in src.authors or ()],
        organization=src.organization,
        jurisdiction=src.jurisdiction,
        legal_domain=src.legalDomain,
        tags=list(src.tags or ()),
        derived_from=_map_if_not_none(_derived_from, src.derivedFrom),
        language=src.language,
        valid_from=src.validFrom,
        valid_until=src.validUntil,
        replaces=src.replaces,
        replaced_by=src.replacedBy,
    )


def _author(src: model.Author) -> Author:
    return Author(name=src.name, email=src.email, organization=src.organization)


def _derived_from(src: model.DerivedFrom) -> DerivedFrom:
    return DerivedFrom(
        original_id=src.originalId,
        original_hash=src.originalHash,
        original_status=src.originalStatus,
        derivation_type=src.derivationType,
        derived_at=src.derivedAt,
        derived_by=src.derivedBy,
    )


# --- Root-level capabilities ----------------------------------------------------------


def _capabilities(
    src: model.Capabilities | None,
    extensions: Mapping[CapabilityId, CapabilityExtension],
) -> CapabilityDeclarations:
    datapoints: DatapointsCapabilityDeclaration | None = None
    text_reference: TextReferenceCapabilityDeclaration | None = None
    tree_reference: TreeReferenceCapabilityDeclaration | None = None
    tree_include: TreeIncludeCapabilityDeclaration | None = None
    context: ContextCapabilityDeclaration | None = None
    query: QueryCapabilityDeclaration | None = None
    ai_query: AiQueryCapabilityDeclaration | None = None
    expression: ExpressionCapabilityDeclaration | None = None
    actions: ActionsCapabilityDeclaration | None = None
    protocol: ProtocolCapabilityDeclaration | None = None
    draft: dict[str, DraftCapabilityDeclaration] = {}
    third_party: dict[str, CapabilityDeclarationWithData] = {}
    extended: dict[str, ExtensionCapabilityDeclaration] = {}
    violations: list[StructuralViolation] = []
    for index, entry in enumerate(src or ()):
        required = _default_if_none(entry.required, False)
        match capability_id := str(entry.id):
            case model.OfficialCapabilityId.ruml_datapoints:
                datapoints = _capability_datapoints(
                    required, _payload(model.DatapointsPayload, entry)
                )
            case model.OfficialCapabilityId.ruml_text_reference:
                text_reference = _capability_text_reference(
                    required, _payload(model.TextReferencePayload, entry)
                )
            case model.OfficialCapabilityId.ruml_tree_reference:
                tree_reference = TreeReferenceCapabilityDeclaration(required=required)
            case model.OfficialCapabilityId.ruml_tree_include:
                tree_include = TreeIncludeCapabilityDeclaration(required=required)
            case model.OfficialCapabilityId.ruml_context:
                context = _capability_context(
                    required, _payload(model.ContextPayload, entry)
                )
            case model.OfficialCapabilityId.ruml_query:
                query = QueryCapabilityDeclaration(
                    required=required, config=_payload(model.PlainPayload, entry).config
                )
            case model.OfficialCapabilityId.ruml_ai_query:
                ai_query = _capability_ai_query_root(
                    required, _payload(model.AiQueryPayload, entry)
                )
            case model.OfficialCapabilityId.ruml_expression:
                expression = ExpressionCapabilityDeclaration(
                    required=required, config=_payload(model.PlainPayload, entry).config
                )
            case model.OfficialCapabilityId.ruml_actions:
                actions = ActionsCapabilityDeclaration(
                    required=required, config=_payload(model.PlainPayload, entry).config
                )
            case model.OfficialCapabilityId.ruml_protocol:
                protocol = _capability_protocol(
                    required, _payload(model.ProtocolPayload, entry)
                )
            case _:
                # Every id the cases above do not catch is a non-official one.
                if (role := entry.role) is None:
                    violations.append(_undeclared_role(index, capability_id))
                elif capability_id in extensions:
                    parsing_function = partial(
                        extensions[capability_id].declaration, required=required
                    )
                    declaration = _parsed_payload(parsing_function, entry)
                    if declaration.role != role:
                        violations.append(
                            _mismatched_role(index, capability_id, role, declaration)
                        )
                    extended[capability_id] = declaration
                elif capability_id.startswith(DRAFT_CAPABILITY_ID_PREFIX):
                    draft[capability_id] = _capability_draft(
                        capability_id,
                        required,
                        role,
                        _payload(model.PlainPayload, entry),
                    )
                else:
                    # A vendor payload the spec leaves open — no model prescribes it.
                    third_party[capability_id] = _capability_with_data(
                        capability_id, required, role, entry.payload
                    )
    if violations:
        raise RumlStructuralError(violations)
    return CapabilityDeclarations(
        datapoints=datapoints,
        text_reference=text_reference,
        tree_reference=tree_reference,
        tree_include=tree_include,
        context=context,
        query=query,
        ai_query=ai_query,
        expression=expression,
        actions=actions,
        protocol=protocol,
        draft=draft,
        third_party=third_party,
        extensions=extended,
        declaration_order=[str(entry.id) for entry in src or ()],
    )


def _undeclared_role(index: int, capability_id: CapabilityId) -> StructuralViolation:
    return StructuralViolation(
        rule="CAP-03",
        message=f"capability {capability_id!r} does not declare its role"
        " (chapter 4.2: a non-official capability must)",
        paths=[json_pointer(("capabilities", index))],
    )


def _mismatched_role(
    index: int,
    capability_id: CapabilityId,
    declared: CapabilityRole,
    implementation: ExtensionCapabilityDeclaration,
) -> StructuralViolation:
    return StructuralViolation(
        rule="CAP-04",
        message=f"capability {capability_id!r} is declared with the role"
        f" {declared.value!r}, but this parser implements it with the role"
        f" {implementation.role.value!r}",
        paths=[json_pointer(("capabilities", index, "role"))],
    )


def _capability_draft(
    id: CapabilityId,
    required: bool,
    role: CapabilityRole,
    payload: model.PlainPayload,
) -> DraftCapabilityDeclaration:
    return DraftCapabilityDeclaration(
        id=id, required=required, role=role, config=payload.config
    )


def _capability_with_data(
    id: CapabilityId,
    required: bool,
    role: CapabilityRole,
    payload: Mapping[str, Any] | None,
) -> CapabilityDeclarationWithData:
    payload = payload or {}
    data = payload.get("data")
    config = payload.get("config")
    return CapabilityDeclarationWithData(
        id=id,
        required=required,
        role=role,
        data=data if isinstance(data, Mapping) else {},
        config=config if isinstance(config, Mapping) else None,
    )


def _capability_datapoints(
    required: bool, payload: model.DatapointsPayload
) -> DatapointsCapabilityDeclaration:
    return DatapointsCapabilityDeclaration(
        required=required,
        data=_datapoints(payload.data),
        sets={key: _datapoint_set(set_) for key, set_ in (payload.sets or {}).items()},
    )


def _datapoint_set(src: model.DatapointSet) -> DatapointSet:
    return DatapointSet(
        name=src.name, description=src.description, fields=_datapoints(src.fields)
    )


def _datapoints(
    src: Mapping[DatapointId, model.Datapoint] | None,
) -> dict[DatapointId, Datapoint]:
    return {key: _datapoint(datapoint) for key, datapoint in (src or {}).items()}


def _datapoint(src: model.Datapoint) -> Datapoint:
    return Datapoint(
        name=src.name,
        type=src.type,
        description=src.description,
        unit=src.unit,
        sensitive=_default_if_none(src.sensitive, False),
        format=src.format,
        options=[_option(option) for option in src.options or ()],
        binding=_binding(src.binding),
        validation=_map_if_not_none(_validation, src.validation),
        set=src.set,
        cardinality=_map_if_not_none(_cardinality, src.cardinality),
    )


def _cardinality(src: model.Cardinality) -> Cardinality:
    return Cardinality(min=src.min, max=src.max)


def _option(src: model.Option) -> Option:
    return Option(value=src.value, label=src.label)


def _binding(src: model.Binding) -> InputBinding | ExternalBinding:
    # The schema describes every binding kind (input, external, computed) with one
    # object, so `model.Binding` carries the fields of all kinds; `type` says which
    # kind a binding is, and thus which of its fields apply.
    match src.type:
        case model.Type1.external:
            return ExternalBinding(
                ref=_required_field(src.ref, "binding.ref"),
                description=src.description,
                source_type=src.sourceType,
                fallback=_map_if_not_none(_input_binding, src.fallback),
            )
        case model.Type1.computed:
            raise NotImplementedError(
                "a computed datapoint binding is not supported yet"
            )
        case _:
            return _input_binding(src)


def _required_field[T](value: T | None, field: str) -> T:
    """Return a field the schema requires for this binding kind but types optional."""
    if value is None:
        raise ValueError(f"{field} is required for this binding kind")
    return value


def _input_binding(src: model.Binding | model.Fallback) -> InputBinding:
    return InputBinding(
        hint=src.hint, placeholder=src.placeholder, default_value=src.defaultValue
    )


def _validation(src: model.Validation) -> Validation:
    return Validation(
        required=src.required,
        min=src.min,
        max=src.max,
        min_length=src.minLength,
        max_length=src.maxLength,
        pattern=src.pattern,
        enum=None if src.enum is None else list(src.enum),
        message=src.message,
    )


def _capability_text_reference(
    required: bool, payload: model.TextReferencePayload
) -> TextReferenceCapabilityDeclaration:
    return TextReferenceCapabilityDeclaration(
        required=required,
        data={key: _text(text) for key, text in (payload.data or {}).items()},
    )


def _text(src: model.Text) -> Text:
    return Text(
        title=src.title,
        uri=src.uri,
        timestamp=src.timestamp,
        status=src.status,
        type=_default_if_none(src.type, model.Type2.embedded),
        text=src.text,
        content=_map_if_not_none(_text_content, src.content),
        digest=src.digest,
        source=_map_if_not_none(_text_source, src.source),
        url=_map_if_not_none(str, src.url),
        container_path=src.containerPath,
        ref=src.ref,
        version=src.version,
        valid_from=src.validFrom,
        valid_until=src.validUntil,
        language=src.language,
        is_referenced=_default_if_none(src.isReferenced, True),
    )


def _text_content(src: model.RumlTextDocument) -> Mapping[str, Any]:
    return src.model_dump(mode="json", exclude_none=True)


def _text_source(src: model.TextSource) -> TextSource:
    return TextSource(uri=src.uri, digest=src.digest, terms=src.terms)


def _capability_context(
    required: bool, payload: model.ContextPayload
) -> ContextCapabilityDeclaration:
    return ContextCapabilityDeclaration(
        required=required,
        data={key: _context(context) for key, context in (payload.data or {}).items()},
    )


def _context(src: model.Context) -> Context:
    return Context(
        title=src.title,
        category=src.category,
        type=_default_if_none(src.type, model.Type4.embedded),
        timestamp=src.timestamp,
        subject=_default_if_none(src.subject, False),
        metadata=src.metadata or {},
        content=src.content,
        source=src.source,
        url=_map_if_not_none(str, src.url),
        container_path=src.containerPath,
        ref=src.ref,
        hash=src.hash,
        access_date=src.accessDate,
    )


def _capability_ai_query_root(
    required: bool, payload: model.AiQueryPayload
) -> AiQueryCapabilityDeclaration:
    return AiQueryCapabilityDeclaration(
        required=required,
        config=_map_if_not_none(_ai_query_root_config, payload.config),
    )


def _ai_query_root_config(src: model.Config1) -> AiQueryDeclarationConfig:
    return AiQueryDeclarationConfig(system_prompt=src.systemPrompt)


def _capability_protocol(
    required: bool, payload: model.ProtocolPayload
) -> ProtocolCapabilityDeclaration:
    config = payload.config or model.Config2()
    return ProtocolCapabilityDeclaration(
        required=required, config=_protocol_config(config)
    )


def _protocol_config(src: model.Config2) -> ProtocolConfig:
    return ProtocolConfig(level=_default_if_none(src.level, model.Level.standard))


# --- Node-level capabilities ----------------------------------------------------------


def _node_capabilities(
    src: model.NodeCapabilities | None,
    extensions: Mapping[CapabilityId, CapabilityExtension],
) -> NodeCapabilities:
    return NodeCapabilities(
        entries=[
            _create_internal_capability_entry(entry, extensions) for entry in src or ()
        ]
    )


def _create_internal_capability_entry(
    entry: NodeCapabilityEntry, extensions: Mapping[CapabilityId, CapabilityExtension]
) -> NodeCapability:
    match str(entry.id):
        case model.OfficialCapabilityId.ruml_query:
            return _capability_query(_payload(model.CapabilityQuery, entry))
        case model.OfficialCapabilityId.ruml_actions:
            return _actions(_parsed_payload(_ACTIONS_ADAPTER.validate_python, entry))
        case model.OfficialCapabilityId.ruml_context:
            return _context_refs(_payload(model.ContextRefs, entry))
        case model.OfficialCapabilityId.ruml_ai_query:
            return _capability_ai_query(_payload(model.CapabilityAiQueryNode, entry))
        case model.OfficialCapabilityId.ruml_text_reference:
            return _text_refs(_payload(model.TextRefs, entry))
        case model.OfficialCapabilityId.ruml_expression:
            return _capability_expression(_payload(model.CapabilityExpression, entry))
        case capability_id if capability_id in extensions:
            return _parsed_payload(extensions[capability_id].node, entry)
        case capability_id:
            return OtherNodeCapability(id=capability_id, payload=entry.payload)


def _capability_query(src: model.CapabilityQuery) -> QueryNodeCapability:
    return QueryNodeCapability(expression=src.expression, description=src.description)


def _capability_expression(src: model.CapabilityExpression) -> ExpressionNodeCapability:
    return ExpressionNodeCapability(
        expression=src.expression, description=src.description
    )


def _actions(
    src: model.Actions1 | model.Actions2 | model.Actions3,
) -> ActionsNodeCapability:
    return ActionsNodeCapability(
        description=src.description,
        on_true=_map_if_not_none(_action, src.onTrue),
        on_false=_map_if_not_none(_action, src.onFalse),
        on_undefined=_map_if_not_none(_action, src.onUndefined),
    )


def _action(src: model.Action) -> Action:
    return Action(operation=src.operation, ref=src.ref, config=src.config)


def _context_refs(src: model.ContextRefs) -> ContextRefsNodeCapability:
    return ContextRefsNodeCapability(refs=list(src.refs))


def _text_refs(src: model.TextRefs) -> TextRefsNodeCapability:
    return TextRefsNodeCapability(refs=[_text_anchor(ref) for ref in src.refs])


def _text_anchor(src: model.TextAnchor) -> TextAnchor:
    return TextAnchor(id=src.id, type=src.type, element=src.element)


def _capability_ai_query(
    src: model.CapabilityAiQueryNode,
) -> AiQueryNodeCapability:
    return AiQueryNodeCapability(
        model=src.model,
        prompt=src.prompt,
        description=src.description,
        inputs=_query_inputs(src.inputs),
        config=_map_if_not_none(_ai_query_config, src.config),
    )


def _query_inputs(src: model.Inputs | None) -> QueryInputs:
    if src is None:
        return QueryInputs()
    return QueryInputs(
        context=[_context_input(context) for context in src.context or ()],
        datapoints=list(src.dataPoints or ()),
        texts=list(src.texts or ()),
    )


def _context_input(src: str | model.Context1) -> ContextInput:
    if isinstance(src, str):
        return ContextInput(id=src)
    return ContextInput(
        id=src.id, role=_default_if_none(src.role, model.Role.reference)
    )


def _ai_query_config(src: model.Config) -> AiQueryNodeConfig:
    return AiQueryNodeConfig(
        deterministic=src.deterministic,
        effort=_default_if_none(src.effort, model.Effort.medium),
        temperature=src.temperature,
    )


# --- Rulemap ----------------------------------------------------------------------------


def _node(
    src: model.Node, extensions: Mapping[CapabilityId, CapabilityExtension]
) -> Node:
    if src.children:
        assert src.operator, (  # nosemgrep: gitlab.bandit.B101
            "Branch node must have operator"
        )
        return BranchNode(
            id=src.id,
            operator=src.operator,
            label=src.label,
            alt_text=src.altText,
            description=src.description,
            children=list(src.children or ()),
            capabilities=_node_capabilities(src.capabilities, extensions),
            metadata=src.metadata or {},
            decision_mode=src.decisionMode,
            modular=src.modular,
        )
    return LeafNode(
        id=src.id,
        label=src.label,
        alt_text=src.altText,
        description=src.description,
        capabilities=_node_capabilities(src.capabilities, extensions),
        metadata=src.metadata or {},
        decision_mode=src.decisionMode,
        modular=src.modular,
    )


# --- Helpers ----------------------------------------------------------------------------


def _map_if_not_none[S, T](mapper: Callable[[S], T], src: S | None) -> T | None:
    """Map `src` using `mapper` if the former is not `None`, else return `None`."""
    return None if src is None else mapper(src)


def _default_if_none[T](value: T | None, default: T) -> T:
    """Return `value` if it's not `None`, otherwise return `default`.

    This is useful to apply schema defaults the generated model only records as `None`.
    """
    return default if value is None else value


def _payload[M: BaseModel](kind: type[M], entry: _CapabilityEntry) -> M:
    """Validate an entry's payload against the model its id prescribes.

    The schema picks a payload's schema by the entry's id (`if`/`then` rules), which
    the codegen cannot follow: the generated entry models type `payload` as a free-form
    object. Validating it here yields the model the id prescribes, or rejects the
    payload as the schema would have. An absent payload counts as an empty one, so a
    bare declaration like `{"id": "ruml:query"}` maps to the model's defaults.
    """
    return _parsed_payload(TypeAdapter[M](kind).validate_python, entry)


def _parsed_payload[T](
    parse: Callable[[CapabilityPayload], T], entry: _CapabilityEntry
) -> T:
    """Parse an entry's payload with ``parse``, like ``_payload`` does with a model.

    This serves payloads not parsed into a single model: a union, or a payload an
    extension parses.
    """
    try:
        return parse(entry.payload or {})
    except ValidationError as error:
        raise ValueError(
            f"capability '{entry.id}' does not have the shape its id prescribes: "
            f"{error}"
        ) from error
