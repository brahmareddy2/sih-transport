# Phase 4 — Real-Time GPS Tracking & Telematics Integration

## Files Created

| File | Purpose |
|------|---------|
| `backend/app/services/tracking/gps_simulator.py` | Core simulation loop (asyncio background task), status triggers, and telemetry update broadcasts |
| `backend/app/services/tracking/eta_calculator.py` | Calculates remaining travel time, distance, and integrates Phase 3 ML delay prediction |
| `backend/app/schemas/tracking.py` | Pydantic response/request models for vehicles and simulation controls |
| `backend/app/api/tracking.py` | REST API routes and WS (`/ws`) connection registry |
| `backend/tests/test_tracking.py` | Complete tracking test suite (10 unit/integration tests) |
| `frontend/src/services/trackingApi.js` | REST client calls and WebSocket helper with reconnection handler |
| `frontend/src/pages/LiveTracking.jsx` | Dynamic vehicle tracking dashboard displaying live map (with leaflet and SVG grids fallback), metrics, and simulation controls |

## Files Modified

| File | Changes |
|------|---------|
| `backend/app/models/analytics.py` | Added `trip_id` (UUID index) to `VehicleLocationHistory` table |
| `backend/app/main.py` | Registered `tracking_router` and started `run_simulation_loop` asyncio task in application lifespan |
| `frontend/src/App.jsx` | Imported `LiveTracking` and registered route at `/tracking` with operator/admin protection |
| `frontend/src/pages/Optimization.jsx` | Added "Real-Time Fleet Status" summary card to operator tab and linked it to the Live Tracking map |

## REST & WebSocket APIs Added

- `GET /api/v1/tracking/vehicles` — Retrieve active state of all vehicles in the fleet
- `GET /api/v1/tracking/vehicles/{vehicle_id}` — Fetch state of a specific vehicle
- `GET /api/v1/tracking/vehicles/{vehicle_id}/history` — Fetch recent location history logs for a vehicle
- `GET /api/v1/tracking/trips/{trip_id}/location-history` — Fetch telemetry history for an optimized trip
- `POST /api/v1/tracking/simulate/start` — Start simulated movement along the vehicle's assigned route
- `POST /api/v1/tracking/simulate/pause` — Pause simulation (status becomes `STOPPED`)
- `POST /api/v1/tracking/simulate/resume` — Resume simulation (status becomes `IN_TRANSIT`)
- `POST /api/v1/tracking/simulate/stop` — Stop simulation (status becomes `OFFLINE`)
- `WS /api/v1/tracking/ws` — WebSocket update stream (requires JWT token query parameter)

## Database Changes

Added `trip_id` to `vehicle_locations_history` table:
```python
trip_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
```
Ensures tracking location history coordinates are correctly referenced to their corresponding VRP optimized route.

## GPS Simulation & Telematics Logic

- **Background Loop:** Runs a single, lightweight `asyncio` task ticking every 3 seconds inside FastAPI lifespan, avoiding CPU overhead.
- **Path Interpolation:** Vehicles move gradually between route stops coordinates sorted by sequence.
- **Heading:** Dynamically calculated based on bearing angle between points.
- **Fuel Monitoring:** Fuel level decreases dynamically (`distance_km / fuel_efficiency`). If fuel drops below 15% capacity, status changes to `LOW_FUEL` and triggers in-app warning notification.
- **ETA & ML Integration:** ETA calculates deterministic duration and integrates Phase 3 `predict_delay_risk` ML predictions if shipment data is linked.

## WebSocket & Failures Handling

- Telemetry update payload (`fleet_update`) broadcasts to all active listeners every 3 seconds.
- Browser client connects using `token` query parameters and automatically attempts reconnection every 4 seconds if disconnected, updating the page state indicator (`CONNECTED` | `RECONNECTING` | `OFFLINE`).

## Known Limitations

- **Map Offline Fallback:** If Leaflet.js fails to load due to network limits, the app automatically switches to a beautiful SVG coordinate grid fallback to prevent crashes.
