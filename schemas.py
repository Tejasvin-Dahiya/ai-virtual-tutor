from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime


class SubjectBase(BaseModel):
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    icon_url: Optional[str] = None

class SubjectCreate(SubjectBase):
    pass

class Subject(SubjectBase):
    id: str
    created_at: Optional[datetime] = None
    
    class Config:
        orm_mode = True

class LearningModule(BaseModel):
    id: int
    title: str
    description: str
    objectives: List[str]
    estimatedTime: str
    resources: List[str]
    prerequisites: List[str]

class LearningPath(BaseModel):
    subject: str
    level: str
    totalEstimatedTime: str
    modules: List[LearningModule]
    # structure: Dict[str, Any]
    
    class Config:
        orm_mode = True

class ChatMessageBase(BaseModel):
    content: str
    subject_id: Optional[str] = None      
    related_topic_id: Optional[str] = None

class ChatRequest(BaseModel):
    subject_id: str
    message: str

class ChatMessage(ChatMessageBase):
    id: str
    sender: str  # 'user' or 'tutor'
    timestamp: datetime
    
    class Config:
        orm_mode = True

class UserProgressBase(BaseModel):
    user_id: str
    learning_path_id: str
    progress_data: Dict[str, Any]

class UserProgressCreate(UserProgressBase):
    pass

class UserProgress(UserProgressBase):
    id: str
    last_updated: datetime
    
    class Config:
        orm_mode = True