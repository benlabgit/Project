# Tank Submittal Configurator

A minimal FastAPI web app for configuring steel tank submittal drawings. Enter basic tank parameters to generate a summary, nozzle schedule, and a lightweight 2D elevation sketch.

## Getting started

### Prerequisites
- Python 3.11+

### Install dependencies
```
pip install -r requirements.txt
```

### Run the app
```
uvicorn main:app --reload
```
Visit http://localhost:8000 to open the configurator UI.

### How to test the webpage
1. Start the backend locally:
   ```bash
   uvicorn main:app --reload
   ```
   The app logs will note that it is serving on `http://127.0.0.1:8000`.
2. Open `http://localhost:8000` in your browser. Use the default form values or enter your own, then click **Generate drawing**.
3. Verify the results:
   - The summary card should update with your spec, dimensions, material, and roof information.
   - The nozzle schedule table should show the requested number of nozzles with elevations and orientations.
   - The elevation panel should replace the placeholder text with an SVG preview of the tank.
4. (Optional) Hit the API directly without the UI to confirm the backend works:
   ```bash
   curl -X POST http://localhost:8000/api/config \
     -H "Content-Type: application/json" \
     -d '{"spec":"AWWA D103","diameter_in":360,"shell_height_in":480,"nominal_capacity_gal":250000,"shell_material":"ASTM A36","roof_type":"Low cone roof","nozzle_count":3}'
   ```
   You should receive a JSON payload with `nozzles`, `svg`, and overall dimensions. You can also check the quick capacity endpoint:
   ```bash
   curl "http://localhost:8000/api/estimate?diameter_in=360&shell_height_in=480"
   ```
   This returns a small JSON object with an `estimated_capacity_gal` value.

## API
- `POST /api/config` — accepts tank parameters and returns drawing metadata plus an SVG elevation.
- `GET /api/estimate` — quick capacity estimate based on diameter and shell height.

You can start from the default values in the UI or use your own specs. The nozzle schedule is auto-generated and distributed along the shell height for quick submittal sketches.
