import copy
import json
from uuid import UUID

import pytest
from pydantic import TypeAdapter, ValidationError

from benefitbridge.domain.facts import FactValue
from benefitbridge.domain.rules import (
    IntervalValue,
    PredicateNode,
    RequirementSet,
    validate_source_references,
)


@pytest.fixture
def graph(examples):
    return examples["RequirementSet"]


@pytest.mark.parametrize(
    "mutation",
    [
        "child",
        "root",
        "preferred",
        "duplicate",
        "cycle",
        "orphan_cycle",
        "preferred_mandatory",
        "optional_mandatory",
        "empty_all",
        "extra_predicate_children",
        "invalid_operator",
        "wrong_value_tag",
        "missing_source",
    ],
)
def test_invalid_rule_graphs_are_rejected(graph, mutation):
    root, predicate = graph["nodes"]
    match mutation:
        case "child":
            root["children"] = ["absent"]
        case "root":
            graph["mandatory_root"] = "absent"
        case "preferred":
            graph["preferred_roots"] = ["absent"]
        case "duplicate":
            graph["nodes"].append(copy.deepcopy(predicate))
        case "cycle":
            root["children"] = ["root"]
        case "orphan_cycle":
            graph["nodes"].append({"id": "orphan", "type": "NOT", "child": "orphan"})
        case "preferred_mandatory":
            predicate["modality"] = "PREFERRED"
        case "optional_mandatory":
            predicate["modality"] = "OPTIONAL"
        case "empty_all":
            root["children"] = []
        case "extra_predicate_children":
            predicate["children"] = []
        case "invalid_operator":
            predicate["operator"] = "EVAL_CODE"
        case "wrong_value_tag":
            predicate["expected"] = {"type": "STRING", "value": "true"}
        case "missing_source":
            predicate["source_span_ids"] = []
    with pytest.raises(ValidationError):
        RequirementSet.model_validate(graph)


def test_valid_dag_can_share_a_predicate(graph):
    graph["nodes"][0]["children"].append("not-enrolled")
    graph["nodes"].append({"id": "not-enrolled", "type": "NOT", "child": "r-enrolled"})
    RequirementSet.model_validate(graph)


@pytest.mark.parametrize("depth,valid", [(12, True), (13, False)])
def test_graph_depth_limit(graph, depth, valid):
    predicate = graph["nodes"][1]
    graph["mandatory_root"] = "n0"
    graph["nodes"] = [
        {"id": f"n{i}", "type": "NOT", "child": f"n{i + 1}" if i < depth - 2 else predicate["id"]}
        for i in range(depth - 1)
    ] + [predicate]
    if valid:
        RequirementSet.model_validate(graph)
    else:
        with pytest.raises(ValidationError):
            RequirementSet.model_validate(graph)


def test_graph_node_and_fanout_limits(graph):
    predicate = graph["nodes"][1]
    graph["nodes"] = [{**predicate, "id": f"r{i}"} for i in range(101)]
    graph["mandatory_root"] = "r0"
    with pytest.raises(ValidationError):
        RequirementSet.model_validate(graph)
    graph["nodes"] = [
        {"id": "root", "type": "ANY", "children": [f"r{i}" for i in range(51)]}
    ] + graph["nodes"][:51]
    graph["mandatory_root"] = "root"
    with pytest.raises(ValidationError):
        RequirementSet.model_validate(graph)


def test_empty_incomplete_policy_stays_representable_without_eligibility(graph):
    graph.update(completeness="INCOMPLETE", mandatory_root=None, nodes=[])
    requirements = RequirementSet.model_validate(graph)
    assert requirements.mandatory_root is None
    assert "eligibility" not in requirements.model_dump()


def test_unsupported_attribute_remains_available_for_unknown_evaluation(graph):
    graph["nodes"][1]["attribute"] = "provider.custom_credential"
    graph["nodes"][1]["interpretation"] = "UNRESOLVED"
    assert RequirementSet.model_validate(graph).nodes[1].attribute == "provider.custom_credential"


def test_explicit_reference_time_requires_date_and_other_times_omit_it(graph):
    predicate = graph["nodes"][1]
    with pytest.raises(ValidationError):
        PredicateNode.model_validate({**predicate, "reference_time": "EXPLICIT"})
    with pytest.raises(ValidationError):
        PredicateNode.model_validate({**predicate, "reference_date": None})
    date = {"type": "DATE", "value": "2027-09", "precision": "MONTH", "expected": False}
    explicit = PredicateNode.model_validate(
        {**predicate, "reference_time": "EXPLICIT", "reference_date": date}
    )
    assert json.loads(explicit.model_dump_json())["reference_date"] == date
    assert "reference_date" not in json.loads(
        PredicateNode.model_validate(predicate).model_dump_json()
    )


def test_source_membership_includes_application_tasks(graph):
    requirements = RequirementSet.model_validate(graph)
    predicate_ids = frozenset(UUID(value) for value in graph["nodes"][1]["source_span_ids"])
    with pytest.raises(ValueError, match="pinned source bundle"):
        validate_source_references(requirements, predicate_ids)
    task_ids = frozenset(UUID(value) for value in graph["application_tasks"][0]["source_span_ids"])
    validate_source_references(requirements, predicate_ids | task_ids)


@pytest.mark.parametrize(
    "upper",
    [
        {"type": "GPA", "number": "3", "scale_max": "5"},
        {"type": "GPA", "number": "2", "scale_max": "4"},
        {"type": "STRING", "value": "4"},
    ],
)
def test_interval_rejects_incompatible_or_reversed_bounds(upper):
    with pytest.raises(ValidationError):
        IntervalValue.model_validate(
            {
                "type": "INTERVAL",
                "lower": {"type": "GPA", "number": "3", "scale_max": "4"},
                "upper": upper,
                "lower_inclusive": True,
                "upper_inclusive": True,
            }
        )


def test_valid_interval_is_rule_only(graph):
    predicate = graph["nodes"][1]
    interval = {
        "type": "INTERVAL",
        "lower": {"type": "GPA", "number": "3", "scale_max": "4"},
        "upper": {"type": "GPA", "number": "4", "scale_max": "4"},
        "lower_inclusive": True,
        "upper_inclusive": True,
    }
    with pytest.raises(ValidationError):
        TypeAdapter(FactValue).validate_python(interval)
    PredicateNode.model_validate(
        {**predicate, "attribute": "education.gpa", "operator": "OVERLAPS", "expected": interval}
    )


def test_membership_and_date_operators_require_appropriate_values(graph):
    predicate = graph["nodes"][1]
    for operator in ("IN", "NOT_IN", "BEFORE", "AFTER"):
        with pytest.raises(ValidationError):
            PredicateNode.model_validate({**predicate, "operator": operator})
