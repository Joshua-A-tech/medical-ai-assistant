# migrate_db.py - Run this to initialize database
from app import Base, engine

print("Creating database tables...")
Base.metadata.create_all(bind=engine)
print("Database tables created successfully!")