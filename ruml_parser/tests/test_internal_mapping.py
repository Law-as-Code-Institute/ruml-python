# SPDX-FileCopyrightText: 2026 Rulemapping Group GmbH
# SPDX-License-Identifier: Apache-2.0
from datetime import UTC, date, datetime
from uuid import UUID

import pytest

from ruml_parser.internal import ruml as internal
from ruml_parser.internal.mapping import to_internal
from ruml_parser.model.ruml import RumlRulemappingLogicFormat
from ruml_parser.structural_error import RumlStructuralError
from ruml_parser.tests.ruml_builders import (
    DOCUMENT_ID,
    NODE_ID,
    TIMESTAMP,
    capability,
    node,
    node_capability,
    node_with_capabilities,
    ruml_document,
    unchecked_capability,
    unchecked_node_capability,
)
from ruml_parser.tests.ruml_dict import RumlRulemappingLogicFormatDict

AWARE_TIMESTAMP = datetime(2026, 8, 20, 12, tzinfo=UTC)
ELEMENT = "4c1f0a52-8f7e-4b4a-9d0e-2a6b3c8e1f10"


def map_document(document: RumlRulemappingLogicFormatDict) -> internal.RumlDocument:
    return to_internal(RumlRulemappingLogicFormat.model_validate(document))


def test_maps_a_document_using_every_capability() -> None:
    # Arrange
    document = ruml_document(
        metadata={
            "id": DOCUMENT_ID,
            "title": "Title",
            "version": "1.0.0",
            "created": TIMESTAMP,
            "modified": TIMESTAMP,
            "status": "inForce",
            "comment": "Checked",
            "documentType": "law",
            "authors": [{"name": "Ada", "email": "ada@example.com"}],
            "tags": ["tax"],
            "derivedFrom": {
                "originalId": DOCUMENT_ID,
                "originalStatus": "approved",
                "derivationType": "revision",
                "derivedAt": TIMESTAMP,
            },
        },
        capabilities=[
            capability(
                "ruml:datapoints",
                {
                    "data": {
                        "dp_age": {
                            "name": "Age",
                            "type": "integer",
                            "binding": {"type": "input", "hint": "Years"},
                            "validation": {"min": 0, "enum": [1, 2]},
                        },
                        "dp_income": {
                            "name": "Income",
                            "type": "currency",
                            "unit": "EUR",
                            "sensitive": True,
                            "binding": {
                                "type": "external",
                                "ref": "tax-office",
                                "sourceType": "api",
                                "fallback": {"type": "input"},
                            },
                        },
                        "dp_addresses": {
                            "name": "Addresses",
                            "type": "object",
                            "set": "set_address",
                            "cardinality": {"min": 1, "max": 3},
                            "binding": {"type": "input"},
                        },
                    },
                    "sets": {
                        "set_address": {
                            "name": "Address",
                            "description": "A postal address",
                            "fields": {
                                "dp_street": {
                                    "name": "Street",
                                    "type": "string",
                                    "binding": {"type": "input"},
                                },
                                "dp_owner": {
                                    "name": "Owner",
                                    "type": "object",
                                    "set": "set_person",
                                    "binding": {"type": "input"},
                                },
                            },
                        },
                        "set_person": {
                            "name": "Person",
                            "fields": {
                                "dp_name": {
                                    "name": "Name",
                                    "type": "string",
                                    "binding": {"type": "input"},
                                }
                            },
                        },
                    },
                },
            ),
            capability(
                "ruml:text-reference",
                {
                    "data": {
                        "text_1": {
                            "title": "EStG § 1",
                            "uri": "/akn/de/act/2009-10-08/estg#sec_1__subsec_2",
                            "timestamp": TIMESTAMP,
                            "status": "inForce",
                            "type": "url",
                            "url": "https://example.com/estg",
                        }
                    }
                },
                required=True,
            ),
            capability(
                "ruml:context",
                {
                    "data": {
                        "ctx_1": {
                            "title": "Ruling",
                            "category": "courtDecision",
                            "timestamp": TIMESTAMP,
                            "content": {"text": "..."},
                            "accessDate": "2026-08-01",
                        }
                    }
                },
            ),
            capability("ruml:query", required=True),
            capability("ruml:ai-query", {"config": {"systemPrompt": "Be precise."}}),
            unchecked_capability("ruml:actions", {"config": {"runtime": "x"}}),
            capability(
                "ruml:protocol", {"config": {"level": "verbose"}}, required=True
            ),
            capability("ruml:draft/experimental", role="data"),
            unchecked_capability(
                "com.example/engine", {"data": {"entry": 1}}, role="data"
            ),
        ],
        rulemap={
            "nodes": {
                "1": node(operator="AND", children=["2"], metadata={"k": "v"}),
                "2": node(
                    id="f9608100-f4b1-4e93-817e-01a2ff5149ed",
                    label="Adult",
                    decisionMode="majority",
                    capabilities=[
                        node_capability("ruml:query", {"expression": "$age >= 18"}),
                        node_capability(
                            "ruml:ai-query",
                            {
                                "model": "llm",
                                "prompt": "Is the person an adult?",
                                "inputs": {
                                    "context": [
                                        "ctx_1",
                                        {"id": "ctx_1", "role": "subject"},
                                    ],
                                    "dataPoints": ["dp_age"],
                                },
                                "config": {"temperature": 0.5},
                            },
                        ),
                        node_capability(
                            "ruml:actions",
                            {"onTrue": {"operation": "notify", "ref": "mail"}},
                        ),
                        node_capability("ruml:context", {"refs": ["ctx_1"]}),
                        node_capability(
                            "ruml:text-reference",
                            {
                                "refs": [
                                    {"id": "text_1", "type": "represents"},
                                    {
                                        "id": "text_1",
                                        "element": ELEMENT,
                                        "type": "refers-to",
                                    },
                                ]
                            },
                        ),
                        unchecked_node_capability(
                            "ruml:datapoints", {"dp_age": "used"}
                        ),
                        unchecked_node_capability(
                            "com.example/engine", {"entries": [1, "two"]}
                        ),
                    ],
                ),
            }
        },
    )

    # Act
    result = map_document(document)

    # Assert
    assert result == internal.RumlDocument(
        spec_version="1.0",
        metadata=internal.Metadata(
            id=UUID(DOCUMENT_ID),
            title="Title",
            version="1.0.0",
            created=AWARE_TIMESTAMP,
            modified=AWARE_TIMESTAMP,
            status=internal.DocumentStatus.inForce,
            comment="Checked",
            document_type=internal.DocumentType.law,
            authors=[internal.Author(name="Ada", email="ada@example.com")],
            tags=["tax"],
            derived_from=internal.DerivedFrom(
                original_id=UUID(DOCUMENT_ID),
                original_status=internal.DocumentStatus.approved,
                derivation_type=internal.DerivationType.revision,
                derived_at=AWARE_TIMESTAMP,
            ),
        ),
        capabilities=internal.CapabilityDeclarations(
            datapoints=internal.DatapointsCapabilityDeclaration(
                data={
                    "dp_age": internal.Datapoint(
                        name="Age",
                        type=internal.DatapointType.integer,
                        binding=internal.InputBinding(hint="Years"),
                        validation=internal.Validation(min=0, enum=[1, 2]),
                    ),
                    "dp_income": internal.Datapoint(
                        name="Income",
                        type=internal.DatapointType.currency,
                        unit="EUR",
                        sensitive=True,
                        binding=internal.ExternalBinding(
                            ref="tax-office",
                            source_type=internal.ExternalSourceType.api,
                            fallback=internal.InputBinding(),
                        ),
                    ),
                    "dp_addresses": internal.Datapoint(
                        name="Addresses",
                        type=internal.DatapointType.object,
                        set="set_address",
                        cardinality=internal.Cardinality(min=1, max=3),
                        binding=internal.InputBinding(),
                    ),
                },
                sets={
                    "set_address": internal.DatapointSet(
                        name="Address",
                        description="A postal address",
                        fields={
                            "dp_street": internal.Datapoint(
                                name="Street",
                                type=internal.DatapointType.string,
                                binding=internal.InputBinding(),
                            ),
                            "dp_owner": internal.Datapoint(
                                name="Owner",
                                type=internal.DatapointType.object,
                                set="set_person",
                                binding=internal.InputBinding(),
                            ),
                        },
                    ),
                    "set_person": internal.DatapointSet(
                        name="Person",
                        fields={
                            "dp_name": internal.Datapoint(
                                name="Name",
                                type=internal.DatapointType.string,
                                binding=internal.InputBinding(),
                            )
                        },
                    ),
                },
            ),
            text_reference=internal.TextReferenceCapabilityDeclaration(
                required=True,
                data={
                    "text_1": internal.Text(
                        title="EStG § 1",
                        uri="/akn/de/act/2009-10-08/estg#sec_1__subsec_2",
                        timestamp=AWARE_TIMESTAMP,
                        status=internal.LegislativeStatus.inForce,
                        type=internal.TextType.url,
                        url="https://example.com/estg",
                    )
                },
            ),
            context=internal.ContextCapabilityDeclaration(
                data={
                    "ctx_1": internal.Context(
                        title="Ruling",
                        category=internal.ContextCategory.courtDecision,
                        timestamp=AWARE_TIMESTAMP,
                        content={"text": "..."},
                        access_date=date(2026, 8, 1),
                    )
                }
            ),
            query=internal.QueryCapabilityDeclaration(
                required=True,
            ),
            ai_query=internal.AiQueryCapabilityDeclaration(
                config=internal.AiQueryDeclarationConfig(system_prompt="Be precise.")
            ),
            actions=internal.ActionsCapabilityDeclaration(
                config={"runtime": "x"},
            ),
            protocol=internal.ProtocolCapabilityDeclaration(
                required=True,
                config=internal.ProtocolConfig(level=internal.ProtocolLevel.verbose),
            ),
            draft={
                "ruml:draft/experimental": internal.DraftCapabilityDeclaration(
                    id="ruml:draft/experimental", role=internal.CapabilityRole.data
                )
            },
            third_party={
                "com.example/engine": internal.CapabilityDeclarationWithData(
                    id="com.example/engine",
                    role=internal.CapabilityRole.data,
                    data={"entry": 1},
                )
            },
        ),
        nodes={
            "1": internal.BranchNode(
                id=UUID(NODE_ID),
                operator=internal.Operator.AND,
                label="root",
                children=["2"],
                metadata={"k": "v"},
                decision_mode=internal.DecisionMode.fallback,
            ),
            "2": internal.LeafNode(
                id=UUID("f9608100-f4b1-4e93-817e-01a2ff5149ed"),
                label="Adult",
                decision_mode=internal.DecisionMode.majority,
                capabilities=internal.NodeCapabilities(
                    entries=[
                        internal.QueryNodeCapability(expression="$age >= 18"),
                        internal.AiQueryNodeCapability(
                            model="llm",
                            prompt="Is the person an adult?",
                            inputs=internal.QueryInputs(
                                context=[
                                    internal.ContextInput(id="ctx_1"),
                                    internal.ContextInput(
                                        id="ctx_1", role=internal.ContextRole.subject
                                    ),
                                ],
                                datapoints=["dp_age"],
                            ),
                            config=internal.AiQueryNodeConfig(temperature=0.5),
                        ),
                        internal.ActionsNodeCapability(
                            on_true=internal.Action(operation="notify", ref="mail")
                        ),
                        internal.ContextRefsNodeCapability(refs=["ctx_1"]),
                        internal.TextRefsNodeCapability(
                            refs=[
                                internal.TextAnchor(
                                    id="text_1",
                                    type=internal.TextAnchorType.represents,
                                ),
                                internal.TextAnchor(
                                    id="text_1",
                                    element=ELEMENT,
                                    type=internal.TextAnchorType.refers_to,
                                ),
                            ]
                        ),
                        internal.OtherNodeCapability(
                            id="ruml:datapoints", payload={"dp_age": "used"}
                        ),
                        internal.OtherNodeCapability(
                            id="com.example/engine", payload={"entries": [1, "two"]}
                        ),
                    ],
                ),
            ),
        },
    )


def test_maps_a_minimal_document_to_defaults() -> None:
    # Arrange
    document = ruml_document()

    # Act
    result = map_document(document)

    # Assert
    assert result == internal.RumlDocument(
        spec_version="1.0",
        metadata=internal.Metadata(
            id=UUID(DOCUMENT_ID),
            version="1.0.0",
            created=AWARE_TIMESTAMP,
            modified=AWARE_TIMESTAMP,
            status=internal.DocumentStatus.draft,
        ),
        nodes={
            "1": internal.LeafNode(
                id=UUID(NODE_ID),
                label="root",
                decision_mode=internal.DecisionMode.fallback,
            )
        },
    )


def test_a_childless_node_is_a_leaf_whatever_its_operator() -> None:
    # Arrange: an AND operator is set, but there are no children to combine
    document = ruml_document(rulemap={"nodes": {"1": node(operator="AND")}})

    # Act
    result = map_document(document)

    # Assert
    assert isinstance(result.nodes["1"], internal.LeafNode)


def test_node_capabilities_must_be_declared_at_the_root() -> None:
    # Arrange: two nodes use capabilities, the root declares none
    document = ruml_document(
        rulemap={
            "nodes": {
                "1": node(operator="AND", children=["2"]),
                "2": node(
                    capabilities=[
                        node_capability("ruml:query", {"expression": "$x"}),
                        unchecked_node_capability("com.example/x", {"x": 1}),
                    ]
                ),
                "3": node(
                    capabilities=[node_capability("ruml:ai-query", {"model": "llm"})]
                ),
            }
        }
    )
    parsed = RumlRulemappingLogicFormat.model_validate(document)

    # Act / Assert: every offending node is reported
    with pytest.raises(RumlStructuralError) as excinfo:
        to_internal(parsed)
    assert str(excinfo.value) == (
        "node '2' uses capabilities the root does not declare: "
        "'ruml:query', 'com.example/x' (spec rule CAP-15); "
        "node '3' uses capabilities the root does not declare: 'ruml:ai-query' "
        "(spec rule CAP-15)"
    )
    assert [violation.paths for violation in excinfo.value.violations] == [
        ["/rulemap/nodes/2/capabilities/0", "/rulemap/nodes/2/capabilities/1"],
        ["/rulemap/nodes/3/capabilities/0"],
    ]


def test_only_the_undeclared_node_capabilities_are_reported() -> None:
    # Arrange: the root declares one of the two capabilities the node uses
    document = ruml_document(
        capabilities=[capability("ruml:query")],
        rulemap={
            "nodes": {
                "1": node(
                    capabilities=[
                        node_capability("ruml:query", {"expression": "$x"}),
                        unchecked_node_capability("com.example/x", {"x": 1}),
                    ]
                )
            }
        },
    )
    parsed = RumlRulemappingLogicFormat.model_validate(document)

    # Act / Assert
    with pytest.raises(
        ValueError,
        match=r"^node '1' uses capabilities the root does not declare: 'com.example/x' ",
    ):
        to_internal(parsed)


def test_node_capability_payload_must_have_the_shape_of_its_id() -> None:
    # Arrange: a valid free-form payload for the generated model, but not a query
    document = node_with_capabilities(
        unchecked_node_capability("ruml:query", {"description": "no expression"})
    )
    parsed = RumlRulemappingLogicFormat.model_validate(document)

    # Act / Assert
    with pytest.raises(ValueError, match="'ruml:query' does not have the shape"):
        to_internal(parsed)


def test_root_capability_payload_must_have_the_shape_of_its_id() -> None:
    # Arrange: `config` is a `PlainPayload` field, which `ruml:datapoints` lacks
    document = ruml_document(
        capabilities=[unchecked_capability("ruml:datapoints", {"config": {}})]
    )
    parsed = RumlRulemappingLogicFormat.model_validate(document)

    # Act / Assert
    with pytest.raises(ValueError, match="'ruml:datapoints' does not have the shape"):
        to_internal(parsed)


def test_non_official_capability_payloads_are_kept_as_they_are() -> None:
    # Arrange: one entry with a payload, one with an empty one
    document = node_with_capabilities(
        unchecked_node_capability("com.example/x", {"expression": "$x"}),
        unchecked_node_capability("com.example/y", {}),
    )

    # Act
    result = map_document(document)

    # Assert
    assert result.nodes["1"].capabilities == internal.NodeCapabilities(
        entries=[
            internal.OtherNodeCapability(
                id="com.example/x", payload={"expression": "$x"}
            ),
            internal.OtherNodeCapability(id="com.example/y", payload={}),
        ]
    )


def test_root_capability_without_payload_maps_to_defaults() -> None:
    # Arrange
    document = ruml_document(
        capabilities=[
            capability("ruml:datapoints"),
            capability("com.example/x", required=True, role="data"),
        ]
    )

    # Act
    result = map_document(document)

    # Assert
    assert result.capabilities == internal.CapabilityDeclarations(
        datapoints=internal.DatapointsCapabilityDeclaration(),
        third_party={
            "com.example/x": internal.CapabilityDeclarationWithData(
                id="com.example/x",
                required=True,
                role=internal.CapabilityRole.data,
            )
        },
    )


def test_duplicate_root_capability_ids_are_rejected() -> None:
    # Arrange: the root repeats `ruml:query`
    document = ruml_document(
        capabilities=[
            capability("ruml:query"),
            capability("com.example/x", role="data"),
            capability("ruml:query", required=True),
        ]
    )
    parsed = RumlRulemappingLogicFormat.model_validate(document)

    # Act / Assert
    with pytest.raises(RumlStructuralError) as excinfo:
        to_internal(parsed)
    [violation] = excinfo.value.violations
    assert violation.rule == "CAP-10"
    assert violation.paths == ["/capabilities/2"]
    assert str(excinfo.value) == (
        "the root declares the capability 'ruml:query' more than once"
        " (spec rule CAP-10)"
    )


def test_a_node_repeating_a_data_capability_is_rejected() -> None:
    # Arrange: the schema cannot tell `com.example/x` plays `data` (CAP-06)
    document = ruml_document(
        capabilities=[capability("com.example/x", role="data")],
        rulemap={
            "nodes": {
                "1": node(
                    capabilities=[
                        unchecked_node_capability("com.example/x", {}),
                        unchecked_node_capability("com.example/x", {"x": 1}),
                    ]
                )
            }
        },
    )
    parsed = RumlRulemappingLogicFormat.model_validate(document)

    # Act / Assert
    with pytest.raises(RumlStructuralError) as excinfo:
        to_internal(parsed)
    [violation] = excinfo.value.violations
    assert violation.rule == "CAP-06"
    assert violation.paths == [
        "/rulemap/nodes/1/capabilities/0",
        "/rulemap/nodes/1/capabilities/1",
    ]


def test_a_node_may_repeat_decision_and_reaction_capabilities() -> None:
    # Arrange: CAP-06 lets `decision` and `reaction` ids repeat on a node
    action = {"onTrue": {"operation": "notify", "ref": "mail"}}
    document = ruml_document(
        capabilities=[
            capability("ruml:query"),
            capability("ruml:actions"),
            capability("com.example/check", role="decision"),
        ],
        rulemap={
            "nodes": {
                "1": node(
                    capabilities=[
                        node_capability("ruml:query", {"expression": "$a"}),
                        node_capability("ruml:query", {"expression": "$b"}),
                        unchecked_node_capability("ruml:actions", action),
                        unchecked_node_capability("ruml:actions", action),
                        unchecked_node_capability("com.example/check", {}),
                        unchecked_node_capability("com.example/check", {}),
                    ]
                )
            }
        },
    )

    # Act
    result = map_document(document).nodes["1"].capabilities

    # Assert: every entry kept, in declaration order
    assert result.ids == [
        "ruml:query",
        "ruml:query",
        "ruml:actions",
        "ruml:actions",
        "com.example/check",
        "com.example/check",
    ]
    assert len(result.actions) == 2


@pytest.mark.parametrize("capability_id", ["ruml:draft/x", "com.example/x"])
def test_a_non_official_capability_without_role_is_rejected(
    capability_id: str,
) -> None:
    # Arrange: the schema rejects this too (CAP-03), but a plain model does not
    parsed = RumlRulemappingLogicFormat.model_validate(
        ruml_document(
            capabilities=[capability("ruml:query"), capability(capability_id)]
        )
    )

    # Act / Assert
    with pytest.raises(RumlStructuralError) as excinfo:
        to_internal(parsed)
    [violation] = excinfo.value.violations
    assert violation.rule == "CAP-03"
    assert violation.paths == ["/capabilities/1"]


def test_every_actions_variant_maps_to_the_same_class() -> None:
    # Arrange
    action = {"operation": "notify", "ref": "mail"}
    documents = [
        node_with_capabilities(unchecked_node_capability("ruml:actions", {key: action}))
        for key in ("onTrue", "onFalse", "onUndefined")
    ]

    # Act
    results = [
        map_document(document).nodes["1"].capabilities.actions for document in documents
    ]

    # Assert
    mapped_action = internal.Action(operation="notify", ref="mail")
    assert results == [
        [internal.ActionsNodeCapability(on_true=mapped_action)],
        [internal.ActionsNodeCapability(on_false=mapped_action)],
        [internal.ActionsNodeCapability(on_undefined=mapped_action)],
    ]


def test_a_delegated_node_maps_its_combiner_to_a_capability_expression() -> None:
    # Arrange: a DELEGATED node whose combiner reads its two children
    combiner = node_capability(
        "ruml:expression",
        {"expression": "$children[0] and $children[1]", "description": "Both hold"},
    )
    document = ruml_document(
        capabilities=[capability("ruml:expression", required=True)],
        rulemap={
            "nodes": {
                "1": node(
                    operator="DELEGATED", children=["2", "3"], capabilities=[combiner]
                ),
                "2": node(id=str(UUID(int=2)), label="a"),
                "3": node(id=str(UUID(int=3)), label="b"),
            }
        },
    )

    # Act
    result = map_document(document).nodes["1"]

    # Assert
    assert isinstance(result, internal.BranchNode)
    assert result.operator == internal.Operator.DELEGATED
    assert result.capabilities.expression == internal.ExpressionNodeCapability(
        expression="$children[0] and $children[1]", description="Both hold"
    )
    assert result.capabilities.ids == ["ruml:expression"]


def test_the_root_declaration_of_ruml_expression_maps_to_its_own_field() -> None:
    # Arrange: CAP-11 makes the combiner's declaration required
    document = ruml_document(
        capabilities=[
            unchecked_capability(
                "ruml:expression", {"config": {"engine": "jsonata"}}, required=True
            )
        ]
    )

    # Act
    result = map_document(document)

    # Assert: typed like the other official capabilities, not a third-party one
    assert result.capabilities == internal.CapabilityDeclarations(
        expression=internal.ExpressionCapabilityDeclaration(
            required=True,
            config={"engine": "jsonata"},
        )
    )
    assert result.capabilities.declaration_order == ["ruml:expression"]


def test_official_capabilities_play_the_roles_their_chapters_fix() -> None:
    # Arrange: every official capability, none declaring a role (CAP-05 forbids it),
    # except those this package does not model yet
    not_modeled = {"ruml:tree-reference", "ruml:tree-include"}
    ids = [str(id) for id in internal.OfficialCapabilityId if id not in not_modeled]
    document = ruml_document(capabilities=[capability(id) for id in ids])

    # Act
    result = map_document(document).capabilities

    # Assert: the roles of the §4.1 overview tables
    roles = {id: result.get_by_id(id).role for id in ids}
    data = internal.CapabilityRole.data
    decision = internal.CapabilityRole.decision
    combiner = internal.CapabilityRole.combiner
    reaction = internal.CapabilityRole.reaction

    assert roles == {
        "ruml:datapoints": data,
        "ruml:text-reference": data,
        "ruml:context": data,
        "ruml:query": decision,
        "ruml:ai-query": decision,
        "ruml:expression": combiner,
        "ruml:actions": reaction,
        "ruml:protocol": reaction,
    }


def test_non_official_capabilities_carry_their_declared_role() -> None:
    # Arrange: a custom combiner (§4.14) and a draft decision capability
    document = ruml_document(
        capabilities=[
            capability("com.example/combiner", role="combiner"),
            capability("ruml:draft/x", role="decision"),
        ]
    )

    # Act
    result = map_document(document).capabilities

    # Assert
    assert result.get_by_id("com.example/combiner").role == (
        internal.CapabilityRole.combiner
    )
    assert result.get_by_id("ruml:draft/x").role == internal.CapabilityRole.decision


def test_get_by_id_of_an_undeclared_capability_raises() -> None:
    # Arrange
    capabilities = internal.CapabilityDeclarations(
        query=internal.QueryCapabilityDeclaration()
    )

    # Act / Assert: an official id has a fixed role, but only once it is declared
    with pytest.raises(KeyError):
        capabilities.get_by_id("ruml:expression")


def test_get_by_role_returns_the_declarations_playing_it_in_document_order() -> None:
    # Arrange
    document = ruml_document(
        capabilities=[
            capability("com.example/combiner-b", role="combiner"),
            capability("com.example/plain", role="data"),
            capability("ruml:expression", required=True),
            capability("ruml:draft/combiner-a", role="combiner"),
        ]
    )

    # Act
    result = map_document(document).capabilities.get_by_role(
        internal.CapabilityRole.combiner
    )

    # Assert
    assert [declaration.id for declaration in result] == [
        "com.example/combiner-b",
        "ruml:expression",
        "ruml:draft/combiner-a",
    ]


@pytest.mark.parametrize(
    "capability_class",
    [internal.DraftCapabilityDeclaration, internal.CapabilityDeclarationWithData],
)
def test_non_official_capabilities_require_their_role(capability_class: type) -> None:
    # Act / Assert: CAP-03 makes declaring `role` mandatory, so it has no default
    with pytest.raises(TypeError, match="role"):
        capability_class()


@pytest.mark.parametrize(
    "capability_class",
    [internal.DraftCapabilityDeclaration, internal.CapabilityDeclarationWithData],
)
def test_non_official_capabilities_require_their_id(capability_class: type) -> None:
    # Act / Assert: `id` has no default, not even the base class's abstract property
    with pytest.raises(TypeError, match="id"):
        capability_class()


def test_expression_payload_must_have_the_shape_of_a_combiner() -> None:
    # Arrange: the description, which `ruml:expression` requires, is missing
    document = node_with_capabilities(
        unchecked_node_capability("ruml:expression", {"expression": "$children[0]"})
    )
    parsed = RumlRulemappingLogicFormat.model_validate(document)

    # Act / Assert
    with pytest.raises(ValueError, match="'ruml:expression' does not have the shape"):
        to_internal(parsed)


def test_declaration_order_follows_the_document() -> None:
    # Arrange: the AI query is declared before the query, at the root and on the node
    document = node_with_capabilities(
        node_capability("ruml:ai-query", {"model": "llm"}),
        unchecked_node_capability("com.example/x", {"x": 1}),
        node_capability("ruml:query", {"expression": "$x"}),
    )

    # Act
    result = map_document(document)

    # Assert
    expected_order = ["ruml:ai-query", "com.example/x", "ruml:query"]
    assert result.capabilities.declaration_order == expected_order
    assert result.nodes["1"].capabilities.ids == expected_order


def test_node_capability_ids_follow_the_entries() -> None:
    # Act
    capabilities = internal.NodeCapabilities(
        entries=[
            internal.AiQueryNodeCapability(model="llm"),
            internal.OtherNodeCapability(id="com.example/x", payload={"x": 1}),
            internal.QueryNodeCapability(expression="$x"),
        ]
    )

    # Assert: entry order, each id derived from its entry
    assert capabilities.ids == [
        "ruml:ai-query",
        "com.example/x",
        "ruml:query",
    ]


def test_declaration_order_is_derived_for_hand_built_root_capabilities() -> None:
    # Act
    capabilities = internal.CapabilityDeclarations(
        ai_query=internal.AiQueryCapabilityDeclaration(),
        query=internal.QueryCapabilityDeclaration(),
        expression=internal.ExpressionCapabilityDeclaration(
            required=True,
        ),
        third_party={
            "com.example/x": internal.CapabilityDeclarationWithData(
                id="com.example/x", role=internal.CapabilityRole.data
            )
        },
        draft={
            "ruml:draft/x": internal.DraftCapabilityDeclaration(
                id="ruml:draft/x", role=internal.CapabilityRole.data
            )
        },
    )

    # Assert: field order, `draft` and `third_party` last; undeclared fields contribute
    # none
    assert capabilities.declaration_order == [
        "ruml:query",
        "ruml:ai-query",
        "ruml:expression",
        "ruml:draft/x",
        "com.example/x",
    ]
    assert capabilities.ids == {
        "ruml:query",
        "ruml:ai-query",
        "ruml:expression",
        "ruml:draft/x",
        "com.example/x",
    }
