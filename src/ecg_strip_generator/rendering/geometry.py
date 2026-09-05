"""Physical page geometry in millimetres, independent of plotting."""

from dataclasses import asdict, dataclass

from ecg_strip_generator.models import RenderPreset

MM_PER_INCH = 25.4


@dataclass(frozen=True)
class Geometry:
    rows: int
    columns: int
    waveform_width_mm: float
    cell_width_mm: float
    cell_height_mm: float
    page_width_mm: float
    page_height_mm: float
    calibration_gutter_mm: float = 16.0
    margin_mm: float = 10.0
    top_mm: float = 22.0
    bottom_mm: float = 20.0
    gap_mm: float = 8.0

    def panel_bounds_mm(self, index: int) -> tuple[float, float, float, float]:
        x = self.margin_mm
        y = self.bottom_mm + (self.rows - index - 1) * (self.cell_height_mm + self.gap_mm)
        return x, y, self.cell_width_mm, self.cell_height_mm

    def as_dict(self) -> dict:
        return asdict(self)


def calculate_geometry(duration_s: float, preset: RenderPreset) -> Geometry:
    twelve = len(preset.displayed_leads) == 12
    rows = 4 if twelve else len(preset.displayed_leads)
    gap = 0.0 if twelve else 8.0
    waveform_width = duration_s * preset.paper_speed_mm_s
    cell_width = 16.0 + waveform_width
    cell_height = 2 * preset.amplitude_limit_mv * preset.gain_mm_mv + 8.0
    width = max(86.0, 20.0 + cell_width)
    height = 42.0 + rows * cell_height + (rows - 1) * gap
    pixels = (width / MM_PER_INCH * preset.dpi) * (height / MM_PER_INCH * preset.dpi)
    if width > 1500 or pixels > 40_000_000:
        raise ValueError("Page exceeds supported render dimensions; shorten window or lower DPI")
    return Geometry(rows, 1, waveform_width, cell_width, cell_height, width, height, gap_mm=gap)
