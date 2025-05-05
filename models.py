from sqlalchemy import Column, String, Integer, ForeignKey, JSON, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class Subject(Base):
    __tablename__ = "subjects"
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    category = Column(String)
    icon_url = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class LearningPath(Base):
    __tablename__ = "learning_paths"
    
    id = Column(String, primary_key=True)
    subject_id = Column(String, ForeignKey("subjects.id"))
    level = Column(String, nullable=False)  # beginner, intermediate, advanced
    structure = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    id = Column(String, primary_key=True)
    subject_id = Column(String, ForeignKey("subjects.id"))
    sender = Column(String, nullable=False)  # user or tutor
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    related_topic_id = Column(String, nullable=True)

class UserProgress(Base):
    __tablename__ = "user_progress"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False)  # Could link to auth system
    learning_path_id = Column(String, ForeignKey("learning_paths.id"))
    progress_data = Column(JSON, nullable=False)
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())