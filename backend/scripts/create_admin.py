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

import argparse

settings = get_settings()


def create_or_update_admin(email: str, password: str, full_name: str):
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.email == email).first()
        if admin:
            admin.password_hash = hash_password(password)
            admin.is_active = True
            db.commit()
            print(f"Updated password for existing admin: {email}")
        else:
            admin = User(
                email=email,
                password_hash=hash_password(password),
                full_name=full_name,
                role="admin",
                is_active=True,
            )
            db.add(admin)
            db.commit()
            print(f"Created new admin user: {email}")
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create or update an admin user")
    parser.add_argument("--email", type=str, default=settings.admin_email, help="Admin email address")
    parser.add_argument("--password", type=str, default=settings.admin_password, help="Admin password")
    parser.add_argument("--name", type=str, default=settings.admin_full_name, help="Admin full name")
    args = parser.parse_args()

    create_or_update_admin(args.email, args.password, args.name)
