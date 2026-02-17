from __future__ import annotations

from math import pi
from typing import List

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field


app = FastAPI(title="Horizontal Tank Submittal Configurator")
templates = Jinja2Templates(directory="templates")


class TankConfig(BaseModel):
    spec: str = Field(..., description="Tank specification or standard")
    diameter_in: float = Field(..., gt=0, description="Tank diameter in inches")
    shell_length_in: float = Field(..., gt=0, description="Shell length in inches")
    nominal_capacity_gal: float = Field(..., gt=0, description="Rated capacity in gallons")
    shell_material: str = Field(..., description="Shell material")
    head_type: str = Field(..., description="Head style description")
    nozzle_count: int = Field(3, gt=0, description="Number of top nozzles to schedule")


class NozzleScheduleItem(BaseModel):
    nozzle: str
    size_in: float
    location_from_left_in: float
    orientation: str


class TankDrawing(BaseModel):
    overall_length_in: float
    overall_height_in: float
    diameter_in: float
    shell_length_in: float
    head_type: str
    svg: str
    nozzles: List[NozzleScheduleItem]


@app.get("/", response_class=HTMLResponse)
async def home(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("index.html", {"request": request})


def build_nozzle_schedule(config: TankConfig) -> List[NozzleScheduleItem]:
    spacing = config.shell_length_in / (config.nozzle_count + 1)
    orientations = ["TOP", "TOP-R", "TOP", "TOP-L"]
    schedule: List[NozzleScheduleItem] = []

    for i in range(config.nozzle_count):
        location = round(spacing * (i + 1), 1)
        size = round(2 + (0.12 * config.diameter_in) / max(config.nozzle_count, 1), 1)
        schedule.append(
            NozzleScheduleItem(
                nozzle=f"N{i + 1}",
                size_in=size,
                location_from_left_in=location,
                orientation=orientations[i % len(orientations)],
            )
        )

    return schedule


def tank_profile_svg(config: TankConfig, nozzles: List[NozzleScheduleItem]) -> str:
    view_height = 320
    view_width = 760
    margin = 36

    total_length_in = config.shell_length_in + config.diameter_in
    scale = min(
        (view_width - 2 * margin) / total_length_in,
        (view_height - 2 * margin) / config.diameter_in,
    )

    diameter_px = config.diameter_in * scale
    shell_length_px = config.shell_length_in * scale
    radius = diameter_px / 2

    left_x = (view_width - (shell_length_px + diameter_px)) / 2
    right_x = left_x + diameter_px + shell_length_px
    center_y = view_height / 2
    top_y = center_y - radius
    bottom_y = center_y + radius

    shell_left = left_x + radius

    nozzle_elements = []
    for item in nozzles:
        nozzle_x = shell_left + item.location_from_left_in * scale
        nozzle_elements.append(
            f'<line x1="{nozzle_x}" y1="{top_y}" x2="{nozzle_x}" y2="{top_y - 24}" stroke="#2563eb" stroke-width="3" />'
        )
        nozzle_elements.append(
            f'<circle cx="{nozzle_x}" cy="{top_y - 28}" r="6" fill="#2563eb" />'
        )
        nozzle_elements.append(
            f'<text x="{nozzle_x + 8}" y="{top_y - 34}" font-size="12" fill="#0f172a">{item.nozzle}</text>'
        )

    saddle_y = bottom_y + 10
    saddle_width = max(24, shell_length_px * 0.12)

    svg_parts = [
        f'<svg viewBox="0 0 {view_width} {view_height}" role="img" aria-label="Horizontal tank elevation">',
        '<defs>'
        '<linearGradient id="shellShade" x1="0%" x2="100%" y1="0%" y2="0%">'
        '<stop offset="0%" stop-color="#e2e8f0"/><stop offset="100%" stop-color="#cbd5e1"/>'
        '</linearGradient>'
        '<marker id="arrow" markerWidth="10" markerHeight="10" refX="5" refY="5" orient="auto-start-reverse">'
        '<path d="M0,0 L10,5 L0,10 z" fill="#0f172a" />'
        '</marker>'
        '</defs>',
        f'<rect x="{shell_left}" y="{top_y}" width="{shell_length_px}" height="{diameter_px}" fill="url(#shellShade)" stroke="#0f172a" stroke-width="2" />',
        f'<circle cx="{left_x + radius}" cy="{center_y}" r="{radius}" fill="url(#shellShade)" stroke="#0f172a" stroke-width="2" />',
        f'<circle cx="{right_x - radius}" cy="{center_y}" r="{radius}" fill="url(#shellShade)" stroke="#0f172a" stroke-width="2" />',
        f'<rect x="{shell_left + shell_length_px * 0.2}" y="{saddle_y}" width="{saddle_width}" height="14" fill="#64748b" rx="3" />',
        f'<rect x="{shell_left + shell_length_px * 0.68}" y="{saddle_y}" width="{saddle_width}" height="14" fill="#64748b" rx="3" />',
        f'<text x="{view_width / 2}" y="{top_y - 10}" text-anchor="middle" font-size="12" fill="#0f172a">Head type: {config.head_type}</text>',
        f'<line x1="{left_x}" y1="{bottom_y + 30}" x2="{right_x}" y2="{bottom_y + 30}" stroke="#0f172a" stroke-width="1.5" marker-start="url(#arrow)" marker-end="url(#arrow)"/>',
        f'<text x="{view_width / 2}" y="{bottom_y + 48}" text-anchor="middle" font-size="12" fill="#0f172a">Overall length: {total_length_in:.1f} in</text>',
        f'<line x1="{left_x - 24}" y1="{top_y}" x2="{left_x - 24}" y2="{bottom_y}" stroke="#0f172a" stroke-width="1.5" marker-start="url(#arrow)" marker-end="url(#arrow)"/>',
        f'<text x="{left_x - 30}" y="{center_y}" text-anchor="middle" transform="rotate(-90 {left_x - 30} {center_y})" font-size="12" fill="#0f172a">Diameter: {config.diameter_in:.1f} in</text>',
    ]

    svg_parts.extend(nozzle_elements)
    svg_parts.append("</svg>")
    return "".join(svg_parts)


def compute_drawing(config: TankConfig) -> TankDrawing:
    nozzles = build_nozzle_schedule(config)
    svg = tank_profile_svg(config, nozzles)
    return TankDrawing(
        overall_length_in=config.shell_length_in + config.diameter_in,
        overall_height_in=config.diameter_in,
        diameter_in=config.diameter_in,
        shell_length_in=config.shell_length_in,
        head_type=config.head_type,
        svg=svg,
        nozzles=nozzles,
    )


def _escape_pdf_text(value: str) -> str:
    return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _build_pdf(lines: list[str]) -> bytes:
    content_ops = ["BT", "/F1 12 Tf", "50 780 Td"]
    for idx, line in enumerate(lines):
        prefix = "" if idx == 0 else "T* "
        content_ops.append(f"{prefix}({_escape_pdf_text(line)}) Tj")
    content_ops.append("ET")
    content_stream = "\n".join(content_ops).encode("latin-1", "replace")

    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Count 1 /Kids [3 0 R] >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        f"<< /Length {len(content_stream)} >>\nstream\n".encode("latin-1") + content_stream + b"\nendstream",
    ]

    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for i, obj in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{i} 0 obj\n".encode("latin-1"))
        pdf.extend(obj)
        pdf.extend(b"\nendobj\n")

    xref_pos = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode("latin-1"))
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode("latin-1"))

    pdf.extend(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF".encode(
            "latin-1"
        )
    )
    return bytes(pdf)


@app.post("/api/config", response_model=TankDrawing)
async def create_configuration(config: TankConfig) -> TankDrawing:
    return compute_drawing(config)


@app.post("/api/config/pdf")
async def create_configuration_pdf(config: TankConfig) -> Response:
    drawing = compute_drawing(config)
    lines = [
        "Horizontal Tank Submittal",
        f"Spec: {config.spec}",
        f"Material: {config.shell_material}",
        f"Head Type: {config.head_type}",
        f"Diameter: {drawing.diameter_in:.1f} in",
        f"Shell Length: {drawing.shell_length_in:.1f} in",
        f"Overall Length: {drawing.overall_length_in:.1f} in",
        f"Nominal Capacity: {config.nominal_capacity_gal:,.1f} gal",
        "Nozzles:",
    ]
    lines.extend(
        [
            f"  {item.nozzle}: {item.size_in:.1f} in @ {item.location_from_left_in:.1f} in ({item.orientation})"
            for item in drawing.nozzles
        ]
    )
    pdf = _build_pdf(lines)

    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="horizontal_tank_submittal.pdf"'},
    )


def _gallons_from_geometry(diameter_in: float, shell_length_in: float) -> float:
    radius_ft = (diameter_in / 12) / 2
    length_ft = shell_length_in / 12
    volume_cuft = pi * radius_ft**2 * length_ft
    return volume_cuft * 7.48052


@app.get("/api/estimate")
async def estimate_capacity(diameter_in: float, shell_length_in: float) -> dict[str, float]:
    estimated_gallons = _gallons_from_geometry(diameter_in, shell_length_in)
    return {"estimated_capacity_gal": round(estimated_gallons, 1)}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
