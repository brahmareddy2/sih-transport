# Smart India Hackathon (SIH) Demo & Operating Guide
## AI-Powered Dynamic Multi-Vehicle Logistics Optimization & Transportation DSS

---

### 1. How to Start the Platform Locally

#### Backend (FastAPI + Uvicorn)
```bash
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### Frontend (React + Vite)
```bash
cd frontend
npm run dev -- --host 0.0.0.0 --port 5173
```

---

### 2. Demo Login Credentials

| Role | Email | Password | Access Capabilities |
|---|---|---|---|
| **System Admin** | `admin@logistics.in` | `Admin@123!` | Full control, seed generator, user management |
| **Logistics Operator** | `operator@logistics.in` | `Operator@123!` | VRP Optimizer, Incidents, Return Cargo, What-If |
| **Fleet Manager** | `fleet@logistics.in` | `Fleet@123!` | Live GPS Tracking, Vehicle telematics, Service |
| **Delivery Driver** | `driver@logistics.in` | `Driver@123!` | Turn-by-turn route, Trip status |
| **Customer** | `customer@logistics.in` | `Customer@123!` | Shipment tracking, Delivery confirmation |

---

### 3. Key Portal URLs

- **Main Dashboard**: `http://localhost:5173/operator`
- **Interactive Swagger API Docs**: `http://localhost:8000/docs`
- **Health Check**: `http://localhost:8000/health`
- **Readiness Probe**: `http://localhost:8000/health/ready`

---

### 4. Step-by-Step Module Walkthrough

#### A. Synthetic Data Generator & Digital Twin
- Navigate to `🛰️ Optimization` ➔ **Seed Data** tab.
- Click **Generate Full Synthetic Dataset**.
- Instantly populates: 50 Indian commercial trucks, 50 certified drivers, 500 multi-city shipments, 300 historical routes, and 80 past incidents with deterministic seed (`SEED=42`).

#### B. CVRPTW Route Optimization & Explainable AI
- Navigate to `🛰️ Optimization` ➔ **Pre-built Scenarios** tab.
- Select Scenario 1 (Multi-Depot Hub Distribution) or Scenario 3 (Cold Chain & Hazmat).
- Click **Run Scenario Optimization**.
- View OR-Tools route legs, total cost (₹), fuel liters, toll expenses, CO2 emissions (kg), and the **Explainable Decision Rationale** box explaining why each route was chosen.

#### C. Live GPS Tracking & Telematics Digital Twin
- Navigate to `🚛 GPS Tracking`.
- Click **▶ Start Simulation** to start vehicle tracking along road coordinates.
- Watch live speed (km/h), fuel level depletion (L), heading angle, and dynamic ETA updates over WebSockets.

#### D. Incident Management & Automated Recovery Engine
- Navigate to `🚨 Incidents`.
- Select an active vehicle and choose **Simulate Breakdown** or **Road Closure**.
- Click **Generate Recovery Options** to run the deterministic recovery engine.
- Compare ranked plans with 0–100 recovery scores, added cost (₹), and delay metrics.
- Click **Approve & Execute** to reassign the standby vehicle, update the shipment status, and notify operators.

#### E. Return Cargo Matching & Empty-KM Reduction
- Navigate to `🔄 Return Cargo`.
- Click **Scan Fleet for Return Cargo**.
- View ranked return shipments for vehicles away from home depot.
- Review Deadhead Before vs After (e.g. 300 km ➔ 50 km = 83.3% empty-km reduction).
- Click **⚡ Approve & Generate Return Route** to create the reverse logistics route.

#### F. What-If Scenario Contingency Simulator
- Navigate to `⚡ What-If`.
- Select any of the 9 disruption scenarios (Heavy Traffic, Breakdown, Puncture, Road Closure, Low Fuel, Driver Unavailable, Urgent Order).
- Click **🚀 Run Simulation**.
- Review side-by-side **BEFORE vs AFTER** comparison metrics and actionable recovery steps.

#### G. Executive Analytics & AI Accuracy Validation
- Navigate to `📈 Analytics`.
- Review live PostgreSQL KPIs, cost distributions, fuel curves, and **Actual vs Predicted** comparison tables (Predicted ETA vs Actual ETA accuracy %, Demand forecast confidence bands, Delay Classifier precision).

---

### 5. Troubleshooting

- **Database fallback**: If PostgreSQL is not running locally outside Docker, the backend seamlessly switches to SQLite local development storage (`dev_logistics.db`).
- **Port conflicts**: If port 8000 or 5173 is occupied, run with alternate flags: `uvicorn app.main:app --port 8001` or `npm run dev -- --port 5174`.
- **Clean Reset**: To reset the database, click "Generate Full Synthetic Dataset" in the optimization tab with "Overwrite existing data" checked.
