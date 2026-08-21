import logging
from sqlalchemy import inspect, text

logger = logging.getLogger(__name__)


def run_migrations(db_engine):
    """
    Ensures new columns required for the breakdown handling and live fleet modules
    are added to the existing SQLite or PostgreSQL database.
    """
    inspector = inspect(db_engine)

    # 1. Update 'vehicles' table
    try:
        columns = [c["name"] for c in inspector.get_columns("vehicles")]
        with db_engine.connect() as conn:
            if "operator_id" not in columns:
                logger.info("Migrating: Adding 'operator_id' to 'vehicles' table")
                conn.execute(text("ALTER TABLE vehicles ADD COLUMN operator_id VARCHAR(36)"))
                conn.commit()
            if "current_load_kg" not in columns:
                logger.info("Migrating: Adding 'current_load_kg' to 'vehicles' table")
                conn.execute(text("ALTER TABLE vehicles ADD COLUMN current_load_kg NUMERIC(10, 2) DEFAULT 0.0"))
                conn.commit()
    except Exception as e:
        logger.error("Failed executing vehicles table migration: %s", e)

    # 2. Update 'shipments' table
    try:
        columns = [c["name"] for c in inspector.get_columns("shipments")]
        with db_engine.connect() as conn:
            if "assigned_vehicle_id" not in columns:
                logger.info("Migrating: Adding 'assigned_vehicle_id' to 'shipments' table")
                conn.execute(text("ALTER TABLE shipments ADD COLUMN assigned_vehicle_id VARCHAR(36)"))
                conn.commit()
            if "assigned_driver_id" not in columns:
                logger.info("Migrating: Adding 'assigned_driver_id' to 'shipments' table")
                conn.execute(text("ALTER TABLE shipments ADD COLUMN assigned_driver_id VARCHAR(36)"))
                conn.commit()
            if "delay_reason" not in columns:
                logger.info("Migrating: Adding 'delay_reason' to 'shipments' table")
                conn.execute(text("ALTER TABLE shipments ADD COLUMN delay_reason VARCHAR(255)"))
                conn.commit()
    except Exception as e:
        logger.error("Failed executing shipments table migration: %s", e)
