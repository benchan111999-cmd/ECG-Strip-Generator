"""Reject ambiguous metadata, invalid arrays, false reviews and absent leads."""

import math

import numpy as np
import pytest
from pydantic import ValidationError

from ecg_strip_generator.models import RenderRequest, Signal
from ecg_strip_generator.provenance import signal_digest
from ecg_strip_generator.validation import prepare_signal
from examples.make_fixture import make_fixture


@pytest.mark.parametrize(
    "field,value",
    [
        ("sampling_rate_hz", 0),
        ("sampling_rate_hz", math.inf),
        ("sampling_rate_hz", True),
        ("unit", "counts"),
        ("unit", "unknown"),
        ("leads", ["II", "II"]),
        ("leads", ["unknown"]),
        ("samples", [[0.0], [math.nan]]),
        ("samples", [[0.0], [math.inf]]),
        ("samples", [[0.0, 1.0], [1.0]]),
        ("samples", [[True], [0.0]]),
        ("samples", []),
    ],
)
def test_invalid_signal_rejected(field, value) -> None:
    payload = make_fixture(1).signal.model_dump(mode="json")
    payload[field] = value
    with pytest.raises(ValidationError):
        Signal.model_validate(payload)


@pytest.mark.parametrize("unit,factor", [("mV", 1), ("uV", 1000), ("V", 0.001)])
def test_unit_conversion_preserves_physical_signal(unit, factor) -> None:
    request = make_fixture(2)
    payload = request.model_dump(mode="json")
    payload["signal"]["unit"] = unit
    payload["signal"]["samples"] = [
        [v * factor for v in row] for row in payload["signal"]["samples"]
    ]
    payload["signal_sha256"] = signal_digest(Signal.model_validate(payload["signal"]))
    result = prepare_signal(RenderRequest.model_validate(payload))
    np.testing.assert_allclose(result.values_mv, request.signal.samples, atol=1e-14)
    np.testing.assert_allclose(result.times_s, np.arange(200) / 100)
    assert result.duration_s == 2


def test_missing_lead_ii_never_falls_back_to_mlii() -> None:
    payload = make_fixture(1).model_dump(mode="json")
    payload["signal"]["leads"] = ["MLII"]
    payload["signal_sha256"] = signal_digest(Signal.model_validate(payload["signal"]))
    with pytest.raises(ValueError, match="Missing requested leads: II"):
        prepare_signal(RenderRequest.model_validate(payload))


def test_cannot_expand_one_lead_into_twelve() -> None:
    payload = make_fixture(1).model_dump(mode="json")
    payload["preset"] = make_fixture(12).preset.model_dump(mode="json")
    with pytest.raises(ValueError, match="Missing requested leads"):
        prepare_signal(RenderRequest.model_validate(payload))


def test_exact_selected_order_and_amplitudes() -> None:
    payload = make_fixture(12).model_dump(mode="json")
    payload["preset"]["displayed_leads"] = ["V6", "I"]
    result = prepare_signal(RenderRequest.model_validate(payload))
    assert result.leads == ("V6", "I")
    np.testing.assert_array_equal(
        result.values_mv[:, 0], np.array(payload["signal"]["samples"])[:, 11]
    )
    np.testing.assert_array_equal(
        result.values_mv[:, 1], np.array(payload["signal"]["samples"])[:, 0]
    )


@pytest.mark.parametrize(
    "review",
    [
        {"teaching_release": "approved"},
        {"clinical_review": "approved"},
        {"technical_validation": "passed"},
        {"teaching_release": "retired"},
        {"teaching_release": "unknown"},
    ],
)
def test_render_does_not_accept_self_approved_cases(review) -> None:
    payload = make_fixture(12).model_dump(mode="json")
    payload["case"]["review"].update(review)
    with pytest.raises(ValidationError):
        RenderRequest.model_validate(payload)


def test_bad_checksum_and_clipping_fail() -> None:
    request = make_fixture(1)
    payload = request.model_dump(mode="json")
    payload["signal"]["samples"][0][0] = 3.0
    with pytest.raises(ValueError, match="checksum"):
        prepare_signal(RenderRequest.model_validate(payload))
    payload["signal_sha256"] = signal_digest(Signal.model_validate(payload["signal"]))
    with pytest.raises(ValueError, match="exceeds display amplitude"):
        prepare_signal(RenderRequest.model_validate(payload))


@pytest.mark.parametrize("change", ["window", "version", "extra", "sequential", "duplicate"])
def test_manifest_contract_failures(change) -> None:
    payload = make_fixture(2).model_dump(mode="json")
    if change == "window":
        payload["case"]["end_sample"] += 1
    elif change == "version":
        payload["case"]["source"]["version"] = ""
    elif change == "extra":
        payload["case"]["patient_name"] = "not allowed"
    elif change == "sequential":
        payload["preset"]["time_alignment"] = "sequential"
    else:
        payload["preset"]["displayed_leads"] = ["I", "I"]
    with pytest.raises(ValidationError):
        RenderRequest.model_validate(payload)


@pytest.mark.parametrize(
    "field,value",
    [
        ("licence", "unknown"),
        ("version", "latest"),
        ("attribution", " "),
        ("annotation_reference", "unresolved"),
    ],
)
def test_unknown_source_declarations_fail(field, value) -> None:
    payload = make_fixture(1).model_dump(mode="json")
    payload["case"]["source"][field] = value
    with pytest.raises(ValidationError):
        RenderRequest.model_validate(payload)
