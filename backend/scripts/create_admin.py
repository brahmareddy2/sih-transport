"""
Bootstrap script: Create or update admin user with verified bcrypt password hash.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.user import User

settings = get_settings()


def create_or_update_admin():
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.email == settings.admin_email).first()
        if admin:
            admin.password_hash = hash_password(settings.admin_password)
            admin.is_active = True
            db.commit()
            print(f"Updated password for existing admin: {settings.admin_email}")
        else:
            admin = User(
                email=settings.admin_email,
                password_hash=hash_password(settings.admin_password),
                full_name=settings.admin_full_name,
                role="admin",
                is_active=True,
            )
            db.add(admin)
            db.commit()
            print(f"Created new admin user: {settings.admin_email}")
    finally:
        db.close()


if __name__ == "__main__":
    create_or_update_admin()
