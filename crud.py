from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import models, schemas
import uuid
from datetime import datetime
from database import SessionLocal, engine
from ai_service import AITutorService
import json


server = FastAPI(title="Learning Platform API")
ai_service = AITutorService()
# Dependency
def get_db():
    print("Get DB")
    db = SessionLocal()
    try:
        yield db
    finally:
        print("Got DB")
        db.close()

# Subject Routes
@server.get("/api/subjects", response_model=List[schemas.Subject])
def read_subjects(db: Session = Depends(get_db)):
    """Get all available subjects"""
    print("Get all subject")
    return db.query(models.Subject).all()

@server.get("/api/subjects/{subject_id}", response_model=schemas.Subject)
def read_subject(subject_id: str, db: Session = Depends(get_db)):
    """Get a subject by ID"""
    db_subject = db.query(models.Subject).filter(models.Subject.id == subject_id).first()
    if db_subject is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found")
    return db_subject

@server.post("/api/subjects/", response_model=schemas.Subject, status_code=status.HTTP_201_CREATED)
def create_subject(subject: schemas.SubjectCreate, db: Session = Depends(get_db)):
    """Create a new subject"""
    db_subject = models.Subject(
        id=str(uuid.uuid4()),
        name=subject.name,
        description=subject.description,
        category=subject.category,
        icon_url=subject.icon
    )
    db.add(db_subject)
    db.commit()
    db.refresh(db_subject)
    return db_subject

# Learning Path Routes
@server.get("/api/learning-plan/{subject_id}/{level}", response_model=schemas.LearningPath)
def get_learning_path_alt(subject_id: str, level: str, db: Session = Depends(get_db)):
    # Reuse the existing logic by redirecting to the proper endpoint
    return get_learning_path(subject_id, level, db)
@server.get("/api/subjects/{subject_id}/learning-plan/{level}", response_model=schemas.LearningPath)
def get_learning_path(subject_id: str, level: str, db: Session = Depends(get_db)):
    # Your existing implementation
    subject = db.query(models.Subject).filter(models.Subject.id == subject_id).first()
    print(":::subject::: ", subject)
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    print(":::learning_path 1:::")
    learning_path = db.query(models.LearningPath).filter(
        models.LearningPath.subject_id == subject_id,
        models.LearningPath.level == level
    ).first()
    
    print(":::learning_path 2:::", learning_path)
    
    if not learning_path:
        # Generate new learning path if none exists
        print("calling learning_path")
        learning_path_data = ai_service.generate_learning_path(subject.name, level)
        print(":::learning_path_data::: ",learning_path_data)
        
        learning_path = models.LearningPath(
            id=str(uuid.uuid4()),
            subject_id=subject_id,
            level=level,
            structure=learning_path_data
        )
        db.add(learning_path)
        db.commit()
        db.refresh(learning_path)
    print(":::final:::", learning_path)
    print(":::final 2:::", vars(learning_path))
    
    return learning_path.structure

@server.post("/api/subjects/{subject_id}/learning-plan/{level}", response_model=schemas.LearningPath, status_code=status.HTTP_201_CREATED)
def create_learning_path(subject_id: str, level: str, learning_path_data: Dict[str, Any], db: Session = Depends(get_db)):
    """Create a new learning path"""
    # Check if subject exists
    db_subject = db.query(models.Subject).filter(models.Subject.id == subject_id).first()
    if db_subject is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found")
        
    db_learning_path = models.LearningPath(
        id=str(uuid.uuid4()),
        subject_id=subject_id,
        level=level,
        structure=learning_path_data
    )
    db.add(db_learning_path)
    db.commit()
    db.refresh(db_learning_path)
    return db_learning_path

# Chat Routes
@server.post("/api/subjects/{subject_id}/chat", response_model=schemas.ChatMessage, status_code=status.HTTP_201_CREATED)
def save_chat_message(subject_id: str, message: schemas.ChatMessageBase, db: Session = Depends(get_db)):
    """Save a chat message"""
    # Check if subject exists
    db_subject = db.query(models.Subject).filter(models.Subject.id == subject_id).first()
    if db_subject is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found")
        
    db_message = models.ChatMessage(
        id=str(uuid.uuid4()),
        subject_id=subject_id,
        sender=message.sender,
        content=message.content,
        timestamp=datetime.now()
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message

@server.get("/api/subjects/{subject_id}/chat", response_model=List[schemas.ChatMessage])
def get_chat_history(subject_id: str, limit: int = 50, db: Session = Depends(get_db)):
    """Get chat history for a subject"""
    # Check if subject exists
    db_subject = db.query(models.Subject).filter(models.Subject.id == subject_id).first()
    if db_subject is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found")
        
    return db.query(models.ChatMessage).filter(
        models.ChatMessage.subject_id == subject_id
    ).order_by(models.ChatMessage.timestamp.asc()).limit(limit).all()



#Chat response 
@server.post("/api/chat", response_model=schemas.ChatMessage)
def process_chat_message(request: schemas.ChatRequest, db: Session = Depends(get_db)):
    """Process a chat message and return AI response"""
    subject_id = request.subject_id
    
    # Verify subject exists
    db_subject = db.query(models.Subject).filter(models.Subject.id == subject_id).first()
    if db_subject is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found")
    
    # Save user message
    user_message = models.ChatMessage(
        id=str(uuid.uuid4()),
        subject_id=subject_id,
        sender="user",
        content=request.message,
        timestamp=datetime.now()
    )
    db.add(user_message)
    db.commit()
    
    # Get chat history for context
    chat_history = db.query(models.ChatMessage).filter(
        models.ChatMessage.subject_id == subject_id
    ).order_by(models.ChatMessage.timestamp.desc()).limit(10).all()
    
    # Format for AI service
    formatted_history = [
        {"sender": msg.sender, "content": msg.content} 
        for msg in reversed(chat_history)
    ]
    
    # Get AI response
    ai_response = ai_service.get_chat_response(
        subject_name=db_subject.name,
        user_message=request.message,
        chat_history=formatted_history
    )
    
    # Save AI response
    tutor_message = models.ChatMessage(
        id=str(uuid.uuid4()),
        subject_id=subject_id,
        sender="tutor",
        content=ai_response,
        timestamp=datetime.now()
    )
    db.add(tutor_message)
    db.commit()
    db.refresh(tutor_message)
    
    return tutor_message




@server.post("/api/subjects/{subject_id}/chat/response", response_model=schemas.ChatMessage)
def get_ai_tutor_response(
    subject_id: str, 
    request: schemas.ChatRequest, 
    db: Session = Depends(get_db)
):
    """Get AI tutor response for a user message"""
    # Check if subject exists
    db_subject = db.query(models.Subject).filter(models.Subject.id == subject_id).first()
    if db_subject is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found")
    
    # Get recent chat history for context
    chat_history = db.query(models.ChatMessage).filter(
        models.ChatMessage.subject_id == subject_id
    ).order_by(models.ChatMessage.timestamp.desc()).limit(10).all()
    
    # Format chat history for AI service
    formatted_history = [
        {"sender": msg.sender, "content": msg.content} 
        for msg in reversed(chat_history)
    ]
    
    # Get AI response
    ai_response = ai_service.get_chat_response(
        subject_name=db_subject.name,
        user_message=request.message,
        chat_history=formatted_history
    )
    
    # Save AI response to database
    db_message = models.ChatMessage(
        id=str(uuid.uuid4()),
        subject_id=subject_id,
        sender="tutor",
        content=ai_response,
        timestamp=datetime.now()
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    
    return db_message

# User Progress Routes
@server.post("/api/user-progress/", response_model=schemas.UserProgress)
def update_user_progress(progress_data: schemas.UserProgressCreate, db: Session = Depends(get_db)):
    """Update user progress on a learning path"""
    # Check if learning path exists
    db_learning_path = db.query(models.LearningPath).filter(
        models.LearningPath.id == progress_data.learning_path_id
    ).first()
    if db_learning_path is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Learning path not found")
    
    # Check if progress record exists
    existing_progress = db.query(models.UserProgress).filter(
        models.UserProgress.user_id == progress_data.user_id,
        models.UserProgress.learning_path_id == progress_data.learning_path_id
    ).first()
    
    if existing_progress:
        # Update existing record
        existing_progress.progress_data = progress_data.progress_data
        existing_progress.last_updated = datetime.now()
        db.commit()
        db.refresh(existing_progress)
        return existing_progress
    else:
        # Create new record
        db_progress = models.UserProgress(
            id=str(uuid.uuid4()),
            user_id=progress_data.user_id,
            learning_path_id=progress_data.learning_path_id,
            progress_data=progress_data.progress_data,
            last_updated=datetime.now()
        )
        db.add(db_progress)
        db.commit()
        db.refresh(db_progress)
        return db_progress

@server.get("/api/user-progress/{user_id}/{learning_path_id}", response_model=schemas.UserProgress)
def get_user_progress(user_id: str, learning_path_id: str, db: Session = Depends(get_db)):
    """Get user progress for a specific learning path"""
    progress = db.query(models.UserProgress).filter(
        models.UserProgress.user_id == user_id,
        models.UserProgress.learning_path_id == learning_path_id
    ).first()
    
    if progress is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Progress not found")
    
    return progress

