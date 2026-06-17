from app.config.database import SessionLocal
from app.models.user import User
from app.core.security import get_password_hash

db = SessionLocal()

email = "admin@ads-ai.in"

existing = db.query(User).filter(
    User.email == email
).first()

if existing:
    print("Admin user already exists.")
else:
    admin = User(
        full_name="Administrator",
        email=email,
        password_hash=get_password_hash("Admin@123")
    )

    db.add(admin)
    db.commit()

    print("Admin user created successfully.")

db.close()
