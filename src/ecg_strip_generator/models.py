"""Validated input contracts; clinical and teaching authority remain independent."""

from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

Lead = Literal[
    "I",
    "II",
    "III",
    "aVR",
    "aVL",
    "aVF",
    "V1",
    "V2",
    "V3",
    "V4",
    "V5",
    "V6",
    "MLII",
    "MCL1",
]
STANDARD_LEADS = ("I", "II", "III", "aVR", "aVL", "aVF", "V1", "V2", "V3", "V4", "V5", "V6")
TWELVE_PANEL_ORDER = ("I", "aVR", "V1", "V4", "II", "aVL", "V2", "V5", "III", "aVF", "V3", "V6")
Finite = Annotated[float, Field(strict=True, allow_inf_nan=False)]
Identifier = Annotated[str, Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$")]
Digest = Annotated[str, Field(pattern=r"^[a-f0-9]{64}$")]
Evidence = Literal[
    "real_manual_rhythm_annotation",
    "real_manual_beat_annotation",
    "real_dataset_diagnostic_statement",
    "real_dataset_metadata_only",
    "synthetic_didactic",
]


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Signal(Contract):
    """Physical samples, sample-major; no ADC conversion or lead aliases."""

    leads: Annotated[tuple[Lead, ...], Field(min_length=1, max_length=12)]
    sampling_rate_hz: Annotated[Finite, Field(gt=0, le=10000)]
    unit: Literal["mV", "uV", "V"]
    samples: Annotated[tuple[tuple[Finite, ...], ...], Field(min_length=2, max_length=300000)]

    @model_validator(mode="after")
    def check_shape(self) -> Self:
        if len(set(self.leads)) != len(self.leads):
            raise ValueError("Recorded lead names must be unique")
        if any(len(row) != len(self.leads) for row in self.samples):
            raise ValueError("Every sample must contain exactly one value per recorded lead")
        return self


class Source(Contract):
    dataset: Identifier
    version: Identifier
    record_id: Identifier
    annotation_reference: Annotated[str, Field(min_length=1, max_length=160)]
    licence: Annotated[str, Field(min_length=1, max_length=200)]
    attribution: Annotated[str, Field(min_length=1, max_length=200)]
    checksum_sha256: Digest
    checksum_kind: Literal["official", "locally_observed"]
    non_clinical_fixture: bool = False

    @model_validator(mode="after")
    def require_declared_source(self) -> Self:
        for value in (self.version, self.licence, self.attribution, self.annotation_reference):
            if value.strip().lower() in ("", "unknown", "unresolved", "tbd", "latest"):
                raise ValueError(
                    "Source version, licence, attribution and reference must be explicit"
                )
        return self


class Review(Contract):
    technical_validation: Literal["not_run", "passed", "failed"] = "not_run"
    clinical_review: Literal[
        "not_reviewed", "approved", "approved_with_limited_label", "rejected"
    ] = "not_reviewed"
    teaching_release: Literal["draft", "approved", "retired"] = "draft"


class CaseManifest(Contract):
    schema_version: Literal["1"] = "1"
    case_id: Identifier
    source: Source
    source_evidence: Evidence
    start_sample: Annotated[int, Field(strict=True, ge=0)]
    end_sample: Annotated[int, Field(strict=True, gt=0)]
    review: Review = Review()

    @model_validator(mode="after")
    def check_window(self) -> Self:
        if self.end_sample <= self.start_sample:
            raise ValueError("end_sample is exclusive and must exceed start_sample")
        if self.source.non_clinical_fixture and self.source_evidence != "synthetic_didactic":
            raise ValueError("Non-clinical fixtures must be identified as synthetic_didactic")
        return self


class RenderPreset(Contract):
    displayed_leads: Annotated[tuple[Lead, ...], Field(min_length=1, max_length=12)]
    time_alignment: Literal["simultaneous", "sequential"] = "simultaneous"
    calibration_position: Literal["left", "right"] = "right"
    paper_speed_mm_s: Annotated[Finite, Field(ge=12.5, le=50)] = 25.0
    gain_mm_mv: Annotated[Finite, Field(ge=5, le=20)] = 10.0
    amplitude_limit_mv: Annotated[Finite, Field(ge=1.5, le=5)] = 2.0
    dpi: Annotated[int, Field(strict=True, ge=72, le=300)] = 150
    title: Annotated[str, Field(max_length=80, pattern=r"^[ -~]*$")] = ""
    teaching_prompt: Annotated[str, Field(max_length=120, pattern=r"^[ -~]*$")] = ""

    @model_validator(mode="after")
    def check_layout(self) -> Self:
        count = len(self.displayed_leads)
        if count not in (1, 2, 3, 4, 5, 6, 12):
            raise ValueError("Only one- through six-lead and twelve-lead layouts are supported")
        required_alignment = "sequential" if count == 12 else "simultaneous"
        if self.time_alignment != required_alignment:
            raise ValueError(f"This layout requires time_alignment='{required_alignment}'")
        if len(set(self.displayed_leads)) != count:
            raise ValueError("Displayed lead names must be unique")
        if count == 12 and set(self.displayed_leads) != set(STANDARD_LEADS):
            raise ValueError("Twelve-lead layout requires all twelve standard leads")
        return self


class RenderRequest(Contract):
    case: CaseManifest
    signal: Signal
    signal_sha256: Digest
    preset: RenderPreset

    @model_validator(mode="after")
    def check_case_signal(self) -> Self:
        if self.case.end_sample - self.case.start_sample != len(self.signal.samples):
            raise ValueError("Case sample window must match the supplied signal length")
        if self.case.review != Review():
            raise ValueError("Milestone 1 accepts only not-run, unreviewed draft cases")
        return self
