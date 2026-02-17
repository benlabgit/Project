from __future__ import annotations

from math import pi
from typing import List

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field


app = FastAPI(title="Tank Submittal Configurator")
templates = Jinja2Templates(directory="templates")


class TankConfig(BaseModel):
    spec: str = Field(..., description="Tank specification or standard")
    diameter_in: float = Field(..., gt=0, description="Tank diameter in inches")
    shell_height_in: float = Field(..., gt=0, description="Shell height in inches")
    nominal_capacity_gal: float = Field(..., gt=0, description="Rated capacity in gallons")
    shell_material: str = Field(..., description="Shell material")
    roof_type: str = Field(..., description="Roof style description")
    nozzle_count: int = Field(3, gt=0, description="Number of shell nozzles to schedule")


class NozzleScheduleItem(BaseModel):
    nozzle: str
    size_in: float
    elevation_in: float
    orientation: str


class TankDrawing(BaseModel):
    overall_height_in: float
    diameter_in: float
    shell_height_in: float
    roof_type: str
    svg: str
    nozzles: List[NozzleScheduleItem]


@app.get("/", response_class=HTMLResponse)
async def home(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("index.html", {"request": request})


def build_nozzle_schedule(config: TankConfig) -> List[NozzleScheduleItem]:
    spacing = config.shell_height_in / (config.nozzle_count + 1)
    orientations = ["N", "E", "S", "W"]
    schedule: List[NozzleScheduleItem] = []

    for i in range(config.nozzle_count):
        elevation = round(spacing * (i + 1), 1)
        size = round(2 + (0.15 * config.diameter_in) / max(config.nozzle_count, 1), 1)
        schedule.append(
            NozzleScheduleItem(
                nozzle=f"N{i + 1}",
                size_in=size,
                elevation_in=elevation,
                orientation=orientations[i % len(orientations)],
            )
        )

    return schedule


def tank_profile_svg(config: TankConfig, nozzles: List[NozzleScheduleItem]) -> str:
    view_height = 360
    view_width = 420
    margin = 20

    scale = min(
        (view_height - 2 * margin) / config.shell_height_in,
        (view_width - 2 * margin) / config.diameter_in,
    )

    shell_height_px = config.shell_height_in * scale
    diameter_px = config.diameter_in * scale
    roof_height_px = max(20.0, 0.08 * diameter_px)

    cx = view_width / 2
    top_y = (view_height - shell_height_px - roof_height_px) / 2
    bottom_y = top_y + shell_height_px

    nozzle_elements = []
    for item in nozzles:
        nozzle_x = cx + diameter_px / 2
        nozzle_y = top_y + shell_height_px - item.elevation_in * scale
        nozzle_elements.append(
            f'<line x1="{nozzle_x}" y1="{nozzle_y}" x2="{nozzle_x + 28}" y2="{nozzle_y}" '
            f'stroke="#2563eb" stroke-width="3" />'
        )
        nozzle_elements.append(
            f'<circle cx="{nozzle_x + 32}" cy="{nozzle_y}" r="6" fill="#2563eb" />'
        )
        nozzle_elements.append(
            f'<text x="{nozzle_x + 40}" y="{nozzle_y - 8}" font-size="12" fill="#0f172a">{item.nozzle}</text>'
        )

    svg_parts = [
        f'<svg viewBox="0 0 {view_width} {view_height}" role="img" aria-label="Tank elevation">',
        '<defs>'
        '<linearGradient id="shellShade" x1="0%" x2="100%" y1="0%" y2="0%">'
        '<stop offset="0%" stop-color="#e2e8f0"/><stop offset="100%" stop-color="#cbd5e1"/>'
        '</linearGradient>'
        '<marker id="arrow" markerWidth="10" markerHeight="10" refX="5" refY="5" orient="auto-start-reverse">'
        '<path d="M0,0 L10,5 L0,10 z" fill="#0f172a" />'
        '</marker>'
        '</defs>',
        # Shell
        f'<rect x="{cx - diameter_px / 2}" y="{top_y}" width="{diameter_px}" height="{shell_height_px}" '
        'fill="url(#shellShade)" stroke="#0f172a" stroke-width="2" rx="10" />',
        # Roof
        f'<polygon points="{cx - diameter_px / 2},{top_y} {cx},{top_y - roof_height_px} {cx + diameter_px / 2},{top_y}" '
        'fill="#e2e8f0" stroke="#0f172a" stroke-width="2" />',
        f'<text x="{cx}" y="{top_y - roof_height_px - 6}" text-anchor="middle" font-size="12" fill="#0f172a">{config.roof_type}</text>',
        # Floor line
        f'<line x1="{cx - diameter_px / 2}" y1="{bottom_y}" x2="{cx + diameter_px / 2}" y2="{bottom_y}" '
        'stroke="#0f172a" stroke-width="2" />',
        # Diameter dimension
        f'<line x1="{cx - diameter_px / 2}" y1="{bottom_y + 20}" x2="{cx + diameter_px / 2}" y2="{bottom_y + 20}" '
        'stroke="#0f172a" stroke-width="1.5" marker-start="url(#arrow)" marker-end="url(#arrow)" />',
        f'<text x="{cx}" y="{bottom_y + 36}" text-anchor="middle" font-size="12" fill="#0f172a">Diameter: {config.diameter_in:.1f} in</text>',
        # Height dimension
        f'<line x1="{cx - diameter_px / 2 - 30}" y1="{top_y}" x2="{cx - diameter_px / 2 - 30}" y2="{bottom_y}" '
        'stroke="#0f172a" stroke-width="1.5" marker-start="url(#arrow)" marker-end="url(#arrow)" />',
        f'<text x="{cx - diameter_px / 2 - 36}" y="{top_y + shell_height_px / 2}" text-anchor="middle" transform="rotate(-90 {cx - diameter_px / 2 - 36} {top_y + shell_height_px / 2})" '
        'font-size="12" fill="#0f172a">Shell: {config.shell_height_in:.1f} in</text>',
    ]

    svg_parts.extend(nozzle_elements)
    svg_parts.append('</svg>')
    return "".join(svg_parts)


def compute_drawing(config: TankConfig) -> TankDrawing:
    nozzles = build_nozzle_schedule(config)
    svg = tank_profile_svg(config, nozzles)
    return TankDrawing(
        overall_height_in=config.shell_height_in + 0.08 * config.diameter_in,
        diameter_in=config.diameter_in,
        shell_height_in=config.shell_height_in,
        roof_type=config.roof_type,
        svg=svg,
        nozzles=nozzles,
    )


@app.post("/api/config", response_model=TankDrawing)
async def create_configuration(config: TankConfig) -> TankDrawing:
    return compute_drawing(config)


def _gallons_from_geometry(diameter_in: float, shell_height_in: float) -> float:
    radius_ft = (diameter_in / 12) / 2
    height_ft = shell_height_in / 12
    volume_cuft = pi * radius_ft**2 * height_ft
    return volume_cuft * 7.48052


@app.get("/api/estimate")
async def estimate_capacity(diameter_in: float, shell_height_in: float) -> dict[str, float]:
    estimated_gallons = _gallons_from_geometry(diameter_in, shell_height_in)
    return {"estimated_capacity_gal": round(estimated_gallons, 1)}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
