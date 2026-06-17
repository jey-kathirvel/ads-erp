from app.config.database import engine
from app.models.base import Base

# Import all models
from app.models.user import User

Base.metadata.create_all(bind=engine)

print("All tables created successfully.")
