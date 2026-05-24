from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from sqlalchemy.orm import Session
from api.dependencies.common import get_predictor
from database.db import get_db
from database import crud


router = APIRouter(tags=["meta"])


@router.get("/health")
async def health():
    return {"status": "ok"}


@router.get("/drivers")
async def drivers(db: Session = Depends(get_db)):
    items = crud.get_drivers(db)
    return [{"id": x.id, "name": x.name, "home_region": x.home_region, "efficiency_score": x.efficiency_score} for x in items]


@router.get("/locations")
async def locations(db: Session = Depends(get_db)):
    items = crud.get_locations(db)
    return [{"stop_name": x.stop_name, "latitude": x.latitude, "longitude": x.longitude, "region": x.region} for x in items]


@router.get("/route-map/{driver_id}")
async def route_map(driver_id: str, db: Session = Depends(get_db), predictor=Depends(get_predictor)):
    path = predictor.route_map_html(db, driver_id)
    if not path:
        raise HTTPException(status_code=404, detail="No route history for driver")
    return FileResponse(path, media_type="text/html")


@router.get("/monitoring/summary")
async def monitoring_summary(db: Session = Depends(get_db), predictor=Depends(get_predictor)):
    return predictor.monitoring_summary(db)


@router.get("/monitoring/dashboard")
async def monitoring_dashboard(db: Session = Depends(get_db), predictor=Depends(get_predictor)):
    summary = predictor.monitoring_summary(db)
    html = f"""
    <!doctype html>
    <html>
    <head>
      <meta charset="utf-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1" />
      <title>Route Ops Dashboard</title>
      <style>
        :root {{
          --bg: #f6f7fb;
          --panel: #ffffff;
          --ink: #1b2430;
          --muted: #5c6773;
          --accent: #0f766e;
          --accent-2: #ea580c;
          --line: #e6e8ee;
        }}
        body {{ margin: 0; font-family: "Segoe UI", sans-serif; color: var(--ink); background: radial-gradient(circle at 20% -10%, #e7f8f5 0%, var(--bg) 40%); }}
        .wrap {{ max-width: 1100px; margin: 0 auto; padding: 24px; }}
        h1 {{ margin: 0 0 8px; font-size: 28px; }}
        .sub {{ color: var(--muted); margin-bottom: 18px; }}
        .grid {{ display: grid; gap: 14px; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); }}
        .card {{ background: var(--panel); border: 1px solid var(--line); border-radius: 14px; padding: 14px; box-shadow: 0 5px 18px rgba(0,0,0,0.04); }}
        .label {{ color: var(--muted); font-size: 12px; text-transform: uppercase; letter-spacing: 0.08em; }}
        .value {{ font-size: 24px; font-weight: 700; margin-top: 6px; }}
        .row {{ display: grid; grid-template-columns: 2fr 1fr; gap: 14px; margin-top: 14px; }}
        .panel-title {{ margin: 0 0 12px; font-size: 18px; }}
        .bar-wrap {{ margin: 10px 0; }}
        .bar-label {{ display: flex; justify-content: space-between; font-size: 13px; color: var(--muted); margin-bottom: 4px; }}
        .bar-bg {{ background: #eef1f5; border-radius: 999px; overflow: hidden; height: 12px; }}
        .bar {{ height: 100%; background: linear-gradient(90deg, var(--accent), #22c55e); }}
        .bar.orange {{ background: linear-gradient(90deg, var(--accent-2), #f59e0b); }}
        input, select, button {{ width: 100%; box-sizing: border-box; border: 1px solid #d7dce5; border-radius: 10px; padding: 10px 12px; font-size: 14px; }}
        button {{ background: var(--accent); color: white; border: none; cursor: pointer; font-weight: 600; }}
        button:hover {{ opacity: 0.95; }}
        .form-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }}
        .full {{ grid-column: 1 / -1; }}
        pre {{ background: #111827; color: #e5e7eb; border-radius: 10px; padding: 10px; font-size: 12px; overflow: auto; min-height: 100px; }}
        @media (max-width: 800px) {{
          .row {{ grid-template-columns: 1fr; }}
          .form-grid {{ grid-template-columns: 1fr; }}
        }}
      </style>
    </head>
    <body>
      <div class="wrap">
        <h1>Route Ops Dashboard</h1>
        <div class="sub">Monitoring + live dynamic rerouting</div>
        <div class="grid">
          <div class="card"><div class="label">Total Predictions</div><div class="value" id="p_total">{summary['total_predictions']}</div></div>
          <div class="card"><div class="label">Avg Confidence</div><div class="value" id="p_conf">{summary['avg_confidence']}</div></div>
          <div class="card"><div class="label">Avg Efficiency</div><div class="value" id="p_eff">{summary['avg_efficiency_score']}</div></div>
          <div class="card"><div class="label">Total Trips</div><div class="value" id="p_trips">{summary['total_trips']}</div></div>
        </div>
        <div class="row">
          <div class="card">
            <h3 class="panel-title">Cache Hit Rate</h3>
            <div class="bar-wrap">
              <div class="bar-label"><span>Google Maps</span><span id="maps_rate">{summary['cache']['google_maps']['hit_rate']}</span></div>
              <div class="bar-bg"><div id="maps_bar" class="bar" style="width:{int(summary['cache']['google_maps']['hit_rate'] * 100)}%"></div></div>
            </div>
            <div class="bar-wrap">
              <div class="bar-label"><span>Google Places</span><span id="places_rate">{summary['cache']['google_places']['hit_rate']}</span></div>
              <div class="bar-bg"><div id="places_bar" class="bar orange" style="width:{int(summary['cache']['google_places']['hit_rate'] * 100)}%"></div></div>
            </div>
            <button onclick="refreshSummary()">Refresh Metrics</button>
          </div>
          <div class="card">
            <h3 class="panel-title">Dynamic Reroute</h3>
            <form id="reroute-form" class="form-grid">
              <input id="driver_id" placeholder="Driver ID (e.g. D1)" required />
              <input id="date" type="date" required />
              <input id="current_stop" class="full" placeholder="Current stop (e.g. Store_1)" required />
              <input id="remaining_stops" class="full" placeholder="Remaining stops comma-separated" required />
              <select id="traffic_level" class="full">
                <option value="high">High Traffic</option>
                <option value="medium">Medium Traffic</option>
                <option value="low">Low Traffic</option>
              </select>
              <button class="full" type="submit">Recompute Route</button>
            </form>
            <pre id="reroute_out">Waiting for reroute request...</pre>
          </div>
        </div>
      </div>
      <script>
        async function refreshSummary() {{
          const res = await fetch('/monitoring/summary');
          const s = await res.json();
          document.getElementById('p_total').textContent = s.total_predictions;
          document.getElementById('p_conf').textContent = s.avg_confidence;
          document.getElementById('p_eff').textContent = s.avg_efficiency_score;
          document.getElementById('p_trips').textContent = s.total_trips;
          document.getElementById('maps_rate').textContent = s.cache.google_maps.hit_rate;
          document.getElementById('places_rate').textContent = s.cache.google_places.hit_rate;
          document.getElementById('maps_bar').style.width = Math.round(s.cache.google_maps.hit_rate * 100) + '%';
          document.getElementById('places_bar').style.width = Math.round(s.cache.google_places.hit_rate * 100) + '%';
        }}

        document.getElementById('reroute-form').addEventListener('submit', async (e) => {{
          e.preventDefault();
          const payload = {{
            driver_id: document.getElementById('driver_id').value.trim(),
            date: document.getElementById('date').value,
            current_stop: document.getElementById('current_stop').value.trim(),
            remaining_stops: document.getElementById('remaining_stops').value.split(',').map(x => x.trim()).filter(Boolean),
            traffic_level: document.getElementById('traffic_level').value
          }};
          const out = document.getElementById('reroute_out');
          out.textContent = 'Computing...';
          const res = await fetch('/reroute/dynamic', {{
            method: 'POST',
            headers: {{ 'Content-Type': 'application/json' }},
            body: JSON.stringify(payload)
          }});
          const data = await res.json();
          out.textContent = JSON.stringify(data, null, 2);
          refreshSummary();
        }});
      </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html)
