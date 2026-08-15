# SIH Logistics DSS — Troubleshooting & Diagnostics Guide

This document contains step-by-step solutions for common issues, operational checks, and fallback mechanisms during demonstrations.

---

## 1. Database & Seeding

### Issue: "Database locked" or "no such table"
**Cause:** SQLite file is locked by a hanging process or schema migration was not applied.
**Fix:**
```powershell
# In backend/ directory:
python -c "from app.core.database import Base, engine; Base.metadata.create_all(bind=engine)"
python -m app.services.synthetic.seed_generator
```

### Issue: Resetting to Fresh Demonstration Data
```powershell
# Reseeds all 50 vehicles, 50 drivers, 500 shipments, 300 trips, 80 incidents
python -m app.services.synthetic.seed_generator
```

---

## 2. Authentication & Login

### Issue: "Invalid credentials" on login
**Fix:** Demo credentials are automatically seeded upon startup:
- `admin@logistics.in` / `Admin@123!`
- `operator@logistics.in` / `Operator@123!`
- `fleet@logistics.in` / `Fleet@123!`
- `driver@logistics.in` / `Driver@123!`
- `customer@logistics.in` / `Customer@123!`

---

## 3. OR-Tools Optimization

### Issue: "No feasible route found" or empty routes generated
**Cause:** All vehicles are marked `in_transit` or time windows are expired.
**Fix:**
- Reset vehicle status: In Dashboard or Fleet page, reset vehicle statuses to `available`.
- Run Scenario 1 or Scenario 5 from the Optimization tab (`/optimization`).

---

## 4. Real-Time GPS Tracking & WebSockets

### Issue: GPS marker is not moving
**Cause:** GPS simulation task has not been started for the specific vehicle.
**Fix:**
- Click **Start GPS Simulation** on `/tracking`.
- Ensure WebSocket connection is established (fallback polling automatically engages if WebSocket drops).

---

## 5. Security & Pre-Flight Verification

### Complete 14-Stage E2E Automated Verification
Run the automated test anytime to verify every single subsystem end-to-end:
```powershell
cd C:\Users\reddy\OneDrive\Desktop\sih-transport\backend
python -m tests.verify_e2e_demo_flow
```
Expected result: `[SUCCESS] ALL 14 STAGES OF SIH DEMO PIPELINE VERIFIED -- 100% PASS`

### Full Regression Suite
```powershell
cd C:\Users\reddy\OneDrive\Desktop\sih-transport\backend
python -m pytest tests/
```
Expected result: `86 passed in ~80s`

### Frontend Production Build
```powershell
cd C:\Users\reddy\OneDrive\Desktop\sih-transport\frontend
npm.cmd run build
```
Expected result: `✓ built in ~4s (118 modules transformed)`
