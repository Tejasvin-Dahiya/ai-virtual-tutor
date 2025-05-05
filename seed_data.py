import os
from sqlalchemy.orm import Session
import models, schemas
from database import SessionLocal, engine
import uuid

# Create database tables
models.Base.metadata.create_all(bind=engine)

def seed_subjects():
    db = SessionLocal()
    
    # Check if subjects already exist
    existing_subjects = db.query(models.Subject).count()
    if existing_subjects > 0:
        print(f"Database already contains {existing_subjects} subjects. Skipping seed.")
        db.close()
        return
    
    # Initial subject data
    subjects = [
        {
            "id": str(uuid.uuid4()),
            "name": "Mathematics",
            "description": "Learn mathematics from basic arithmetic to advanced calculus",
            "category": "Science",
            "icon_url": "🧮"
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Physics",
            "description": "Explore the fundamental laws that govern the universe",
            "category": "Science",
            "icon_url": "⚛️"
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Computer Science",
            "description": "Study algorithms, data structures, and programming concepts",
            "category": "Technology",
            "icon_url": "💻"
        },
        {
            "id": str(uuid.uuid4()),
            "name": "English Literature",
            "description": "Analyze classic and contemporary literary works",
            "category": "Humanities",
            "icon_url": "📚"
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Biology",
            "description": "Discover the science of life and living organisms",
            "category": "Science",
            "icon_url": "🧬"
        }
    ]
    
    # Add subjects to database
    for subject_data in subjects:
        subject = models.Subject(**subject_data)
        db.add(subject)
    
    db.commit()
    print(f"Added {len(subjects)} subjects to the database")
    db.close()

if __name__ == "__main__":
    seed_subjects()