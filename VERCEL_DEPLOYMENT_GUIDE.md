# Complete Vercel Deployment Guide
**Project:** AI-Powered Dynamic Multi-Vehicle Logistics Optimization & Intelligent Transportation System

---

## 1. Production Architecture Overview

The system consists of two layers:
1. **Frontend (React + Vite SPA)**: Deployed on **Vercel** for fast global Edge CDN delivery, automatic SSL, and continuous deployments from Git.
2. **Backend (FastAPI + OR-Tools + ML + WebSockets)**: Deployed on a Python host (**Render**, **Railway**, **Fly.io**, or **AWS/VPS**) because OR-Tools and continuous background GPS simulation tasks require a persistent Python environment.

---

## 2. Deploying Frontend to Vercel (Step-by-Step)

### Method A: Via GitHub (Recommended)

1. **Push your code to GitHub**:
   ```bash
   git add .
   git commit -m "Configure Vercel deployment"
   git push origin main
   ```

2. **Import Project into Vercel**:
   - Go to [vercel.com/new](https://vercel.com/new) and log in.
   - Select your GitHub repository (`sih-transport`).
   - Configure project settings:
     - **Framework Preset**: `Vite`
     - **Root Directory**: `frontend` (or leave as `./` since root `vercel.json` is pre-configured)
     - **Build Command**: `npm run build`
     - **Output Directory**: `dist`

3. **Configure Environment Variables**:
   - Under **Environment Variables** in Vercel settings, add:
     - `VITE_API_BASE_URL`: `https://your-backend-service.onrender.com` (Your live backend API URL)
     - `VITE_WS_URL`: `wss://your-backend-service.onrender.com`

4. **Click Deploy**:
   - Vercel will build and deploy the React application in ~30 seconds.
   - You will receive a live URL like `https://sih-transport.vercel.app`.

---

### Method B: Via Vercel CLI (Direct Terminal Deploy)

1. **Install Vercel CLI**:
   ```powershell
   npm install -g vercel
   ```

2. **Deploy from Frontend directory**:
   ```powershell
   cd C:\Users\reddy\OneDrive\Desktop\sih-transport\frontend
   vercel
   ```
   Follow the prompts to link to your Vercel account.

3. **Deploy to Production**:
   ```powershell
   vercel --prod
   ```

---

## 3. Deploying FastAPI Backend (Free Hosting on Render / Railway)

### Option 1: Render.com (1-Click Free Python Deployment)
1. Go to [render.com](https://render.com) and create a new **Web Service**.
2. Connect your GitHub repository.
3. Set the following parameters:
   - **Root Directory**: `backend`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Under **Environment Variables**, add:
   - `DATABASE_URL`: Your PostgreSQL connection string (or SQLite default)
   - `SECRET_KEY`: Any secure random string
   - `BACKEND_CORS_ORIGINS`: `["https://your-app.vercel.app","http://localhost:5173"]`
5. Click **Create Web Service**. Copy the provided URL (e.g. `https://sih-backend.onrender.com`) and paste it as `VITE_API_BASE_URL` in Vercel.

---

### Option 2: Railway.app (Fast Docker/Python Deployment)
1. Go to [railway.app](https://railway.app) and create a **New Project from GitHub Repo**.
2. Select the repository and choose the `backend` folder or root `docker-compose.yml`.
3. Railway automatically detects `requirements.txt` and starts Uvicorn.
4. Copy the public Railway domain and set it as `VITE_API_BASE_URL` in Vercel.

---

## 4. Pre-Configured Vercel Files

- `frontend/vercel.json`: Handles client-side SPA routing rewrites (prevents 404 errors on page reload).
- `vercel.json` (Root): Enables seamless zero-config deployment if imported from the repo root.
