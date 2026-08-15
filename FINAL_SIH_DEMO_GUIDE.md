# Smart India Hackathon (SIH) — Live Demonstration Guide
**Project:** AI-Powered Dynamic Multi-Vehicle Logistics Optimization & Intelligent Transportation System
**Goal:** Deliver a flawless, uninterrupted 10-minute live demonstration for SIH judges.

---

## 1. Quick Launch (Environment Setup)

### Step 1: Start Backend (Terminal 1)
```powershell
cd C:\Users\reddy\OneDrive\Desktop\sih-transport\backend
uvicorn app.main:app --reload --port 8000
```
- API Docs: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/api/v1/health`

### Step 2: Start Frontend (Terminal 2)
```powershell
cd C:\Users\reddy\OneDrive\Desktop\sih-transport\frontend
npm run dev
```
- Frontend UI: `http://localhost:5173`

---

## 2. 8-Step Judge Demonstration Script

### Step 1: Login & Role Switching (1 min)
1. Navigate to `http://localhost:5173/login`.
2. Demonstrate single-click demo logins or sign in as `operator@logistics.in` (`Operator@123!`).
3. Explain that the platform supports 5 RBAC personas (Admin, Operator, Fleet Manager, Driver, Customer).

### Step 2: Integrated Operator Dashboard (1 min)
1. On `/dashboard`, highlight live telemetry cards:
   - Total Vehicles & Utilization Rate.
   - Active Shipments vs Delivered vs Delayed.
   - Empty-KM Reduction metrics and total cost savings in INR.
   - Top notification bell showing real-time system alerts.

### Step 3: AI Route Optimization & Consolidation (2 min)
1. Open `/optimization`.
2. Click **Scenario 1 (Normal Operations - 10 Shipments, 5 Vehicles)** or choose **Auto-Consolidate**.
3. View the Google OR-Tools multi-vehicle routing solution on the interactive map:
   - Capacity constraint satisfaction (weight & volume).
   - Time-window adherence.
   - Hazardous materials / Refrigerated constraints.
4. Expand a route card to demonstrate **Explainable AI**:
   - Algorithmic decision rationale: why specific vehicles and sequences were assigned.
   - Clear breakdown of fuel cost, driver wages, tolls, and CO₂ emissions.

### Step 4: Real-Time GPS Tracking & Telematics (1.5 min)
1. Open `/tracking`.
2. Select an active vehicle and click **Start GPS Simulation**.
3. Watch the vehicle marker traverse the polyline in real-time.
4. Point out telematics widgets:
   - Dynamic Speedometer & Heading.
   - Live Fuel depletion gauge & low-fuel warnings.
   - Continuous dynamic ETA recalculation.

### Step 5: Incident Injection & Automated Recovery (2 min)
1. In `/incidents` or `/tracking`, click **Inject Breakdown Incident** for an in-transit vehicle.
2. An incident alert appears instantly on the operator dashboard and notifications badge.
3. Open the incident to reveal **3 Scored Recovery Plans (0–100 Score)**:
   - Plan A: Dispatch Nearest Alternative Vehicle.
   - Plan B: Split / Transship Cargo.
   - Plan C: Emergency Repair On-Site.
4. Compare recovery scores, extra delay (min), and financial impact (INR).
5. Click **Approve Plan A** — notice route dynamically re-assigns and vehicles reroute automatically.

### Step 6: Return Cargo Matching & Empty-KM Reduction (1.5 min)
1. Open `/return-cargo`.
2. Explain the **Empty Backhaul Problem** (trucks returning empty after delivery).
3. Search compatible return loads for a vehicle completing delivery in Delhi/Mumbai.
4. Show multi-factor match score, detour distance, and net profitability calculation:
   - *Example: 632 km empty backhaul reduced to 0 km with Rs. 14,200 net margin!*
5. Click **Approve Return Match** to generate the reverse return route.

### Step 7: What-If Contingency Simulation Sandbox (1 min)
1. Open `/what-if`.
2. Choose a disruption scenario:
   - **Severe Weather / Monsoon Flooding**
   - **Fuel Price Spike (+15%)**
   - **Driver Shortage / Strike**
   - **High Traffic Congestion (+90 min delay)**
3. Adjust sliders and click **Run Simulation**.
4. Show Before vs After KPI delta cards (Cost, Delivery Time, CO₂ Emissions, SLA Risk).

### Step 8: Executive Analytics & Diagnostics (0.5 min)
1. Open `/analytics`.
2. Review Actual vs Predicted delivery accuracy tables and ML model performance.
3. Conclude by showing `/api/v1/health` and system status to demonstrate zero crashing and high reliability.
