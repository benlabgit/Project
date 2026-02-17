# Horizontal Tank Submittal Configurator

A minimal FastAPI web app for configuring **horizontal** steel tank submittal drawings. Enter basic tank parameters to generate a summary, nozzle schedule, lightweight 2D elevation sketch, and downloadable PDF submittal output.

## Getting started

### Prerequisites
- Python 3.11+

### Install dependencies
```bash
pip install -r requirements.txt
```

### Run the app
```bash
uvicorn main:app --reload
```
Visit http://localhost:8000 to open the configurator UI.

## Features
- Horizontal tank side-elevation SVG preview.
- Auto-generated top nozzle schedule by shell length spacing.
- Downloadable PDF submittal summary via `POST /api/config/pdf`.
- Quick volume estimate via `GET /api/estimate`.

## API
- `POST /api/config` — accepts horizontal tank parameters and returns drawing metadata plus an SVG elevation.
- `POST /api/config/pdf` — accepts the same payload and returns a PDF file download.
- `GET /api/estimate` — quick capacity estimate based on diameter and shell length.

### Example request
```bash
curl -X POST http://localhost:8000/api/config \
  -H "Content-Type: application/json" \
  -d '{"spec":"UL-142","diameter_in":96,"shell_length_in":360,"nominal_capacity_gal":10000,"shell_material":"ASTM A36","head_type":"2:1 Elliptical","nozzle_count":3}'
```
