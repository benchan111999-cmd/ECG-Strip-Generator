"""Packaged, reviewed source metadata; local availability is never registry state."""

import json
from importlib.resources import files
from typing import Annotated, Literal, Self

from pydantic import Field, model_validator

from ecg_strip_generator.models import Contract

Text = Annotated[str, Field(min_length=1)]


class Dataset(Contract):
    id: Annotated[str, Field(pattern=r"^[a-z][a-z0-9-]{0,31}$")]
    version: Annotated[str, Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")]
    title: Text
    role: Literal["core", "supplementary"]
    licence: Literal["CC-BY-4.0", "ODC-By-1.0"]
    citation: Text
    additional_citations: tuple[Text, ...] = ()
    lead_characteristics: Text
    annotation_characteristics: Text
    limitations: Annotated[tuple[Text, ...], Field(min_length=1)]
    reviewed_on: Annotated[str, Field(pattern=r"^\d{4}-\d{2}-\d{2}$")]
    checksum_file: Literal["SHA256SUMS.txt"] | None = "SHA256SUMS.txt"
    checksum_absence_reason: str = ""

    @model_validator(mode="after")
    def checksum_policy(self) -> Self:
        if self.checksum_file is None and not self.checksum_absence_reason.strip():
            raise ValueError("An absent official checksum needs a reviewed reason")
        return self

    @property
    def landing_url(self) -> str:
        return f"https://physionet.org/content/{self.id}/{self.version}/"

    @property
    def files_url(self) -> str:
        return f"https://physionet.org/files/{self.id}/{self.version}/"

    @property
    def licence_url(self) -> str:
        return f"https://physionet.org/content/{self.id}/view-license/{self.version}/"


def load_registry() -> dict[str, Dataset]:
    raw = json.loads(files(__package__).joinpath("sources.json").read_text(encoding="utf-8"))
    entries = [Dataset.model_validate(item) for item in raw]
    registry = {item.id: item for item in entries}
    if not entries or len(registry) != len(entries):
        raise ValueError("Registry must contain unique dataset identifiers")
    return registry


PHYSIONET_CITATION = (
    "Pollard et al. (2026). PhysioNet as a global platform for biomedical research. "
    "Nature Health. https://doi.org/10.1038/s44360-026-00096-z"
)


def attribution(dataset: Dataset, changes: str) -> str:
    """A source notice; the caller must describe actual changes when making a derivative."""
    if not changes.strip():
        raise ValueError("Describe modifications, including an explicit none if unchanged")
    return "\n".join(
        [
            f"Contains material from {dataset.title}, version {dataset.version}.",
            f"Source: {dataset.landing_url}",
            f"Licence: {dataset.licence} ({dataset.licence_url}).",
            "Retain supplied creator, copyright, licence and warranty notices.",
            f"Changes: {changes}",
            dataset.citation,
            *dataset.additional_citations,
            PHYSIONET_CITATION,
            "No endorsement by the source creators is implied.",
        ]
    )
