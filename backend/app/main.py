"""
FastAPI application entry point.
Registers all routers, configures CORS, middleware, and startup events.
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.logging_config import setup_logging

# Setup logging first, before any other imports that log
setup_logging()
logger = logging.getLogger(__name__)
settings = get_settings()


# ── Lifespan (startup / shutdown) ─────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Runs on startup and shutdown.
    Use for: DB pool warmup, cache priming, background tasks.
    """
    logger.info("=" * 60)
    logger.info("  Cargo Pilot Backend starting up")
    logger.info("  Environment : %s", settings.environment)
    logger.info("  DB Host     : %s:%s", settings.postgres_host, settings.postgres_port)
    logger.info("  Redis       : %s", settings.redis_url)
    logger.info("=" * 60)

    # Ensure default demo users exist
    try:
        import uuid
        from app.core.database import SessionLocal
        from app.models.user import User
        from app.core.security import hash_password

        demo_users = [
            ("admin@logistics.in", "Admin@123!", "admin", "System Administrator"),
            ("operator@logistics.in", "Operator@123!", "fleet_operator", "Fleet Operator"),
            ("fleet@logistics.in", "Fleet@123!", "fleet_operator", "Fleet Operator"),
            ("driver@logistics.in", "Driver@123!", "driver", "Lead Driver"),
            ("customer@logistics.in", "Customer@123!", "customer", "Enterprise Customer"),
        ]

        db = SessionLocal()
        try:
            for email, pwd, role, name in demo_users:
                u = db.query(User).filter(User.email == email).first()
                if not u:
                    u = User(
                        id=uuid.uuid4(),
                        email=email,
                        password_hash=hash_password(pwd),
                        role=role,
                        full_name=name,
                        is_active=True,
                    )
                    db.add(u)
                else:
                    u.password_hash = hash_password(pwd)
                    u.is_active = True
                    u.role = role
            db.commit()
            logger.info("Demo credentials initialized successfully")
        except Exception as e:
            db.rollback()
            logger.warning("Demo user bootstrapping notice: %s", e)
        finally:
            db.close()
    except Exception as e:
        logger.warning("Could not bootstrap demo users: %s", e)

    # Start GPS simulator background loop task
    import asyncio
    from app.services.tracking.gps_simulator import run_simulation_loop
    gps_sim_task = asyncio.create_task(run_simulation_loop())
    app.state.gps_sim_task = gps_sim_task

    yield

    logger.info("Cancelling GPS simulation loop...")
    gps_sim_task.cancel()
    try:
        await gps_sim_task
    except asyncio.CancelledError:
        pass

    logger.info("Cargo Pilot Backend shutting down")


# ── FastAPI app ───────────────────────────────────────────
app = FastAPI(
    title="AI-Powered Cargo Pilot API",
    description=(
        "Intelligent Transportation and Logistics Decision Support System (Cargo Pilot). "
        "India-specific platform covering fleet management, route optimization, "
        "disruption handling, and analytics."
    ),
    version="1.0.0-phase1",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)


# ── CORS Middleware ───────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.backend_cors_origins,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1|192\.168\.\d+\.\d+|10\.\d+\.\d+\.\d+|172\.(1[6-9]|2\d|3[0-1])\.\d+\.\d+)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "X-Request-ID"],
)


# ── Global Exception Handler ──────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception on %s %s: %s", request.method, request.url, exc, exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error", "error_code": "INTERNAL_ERROR"},
    )


# ── Register Routers ──────────────────────────────────────
API_PREFIX = "/api/v1"

# Health (no auth, no version prefix — needed by Docker)
from app.api.health import router as health_router
app.include_router(health_router)

# Auth
from app.api.auth import router as auth_router
app.include_router(auth_router, prefix=API_PREFIX)

# Phase 1: Core CRUD routers
from app.api.vehicles import router as vehicles_router
from app.api.drivers import router as drivers_router
from app.api.shipments import router as shipments_router
from app.api.places import router as places_router
app.include_router(vehicles_router, prefix=API_PREFIX)
app.include_router(drivers_router, prefix=API_PREFIX)
app.include_router(shipments_router, prefix=API_PREFIX)
app.include_router(places_router, prefix=API_PREFIX)

# Phase 2: Optimization and Seed routers
from app.api.optimization import router as optimization_router
from app.api.seed import router as seed_router
app.include_router(optimization_router, prefix=API_PREFIX)
app.include_router(seed_router, prefix=API_PREFIX)

# Phase 3: AI/ML Prediction and Risk Intelligence
from app.api.ml import router as ml_router
app.include_router(ml_router, prefix=API_PREFIX)

# Phase 4: Real-Time GPS Tracking & Telematics
from app.api.tracking import router as tracking_router
app.include_router(tracking_router, prefix=API_PREFIX)

# Phase 5: Incident Management & Recovery Planning
from app.api.incidents import router as incidents_router
app.include_router(incidents_router, prefix=API_PREFIX)

# Phase 6: Return Cargo Matching & Empty-Kilometer Reduction
from app.api.return_cargo import router as return_cargo_router
app.include_router(return_cargo_router, prefix=API_PREFIX)

# Phase 7: What-If Simulation, Integrated Analytics & Notifications
from app.api.what_if import router as what_if_router
from app.api.analytics import router as analytics_router
from app.api.notifications import router as notifications_router
from app.api.admin import router as admin_router
from app.api.financials import router as financials_router
app.include_router(what_if_router, prefix=API_PREFIX)
app.include_router(analytics_router, prefix=API_PREFIX)
app.include_router(notifications_router, prefix=API_PREFIX)
app.include_router(admin_router, prefix=API_PREFIX)
app.include_router(financials_router, prefix=API_PREFIX)

# Phase 8: Universal Voice-First + Simple Mode User Experience
from app.api.voice import router as voice_router
from app.api.assistant import router as assistant_router
app.include_router(voice_router, prefix=API_PREFIX)
app.include_router(assistant_router, prefix=API_PREFIX)

# Stub router for routes
from app.api.stubs import routes_router
app.include_router(routes_router, prefix=API_PREFIX)

# Vehicle Breakdown handling
from app.api.breakdowns import router as breakdowns_router
app.include_router(breakdowns_router, prefix=API_PREFIX)


# ── Root redirect ─────────────────────────────────────────
@app.get("/", include_in_schema=False)
def root():
    return {
        "name": "AI-Powered Cargo Pilot",
        "version": "1.0.0-phase7",
        "docs": "/docs",
        "health": "/health",
        "api": f"{API_PREFIX}",
    }
