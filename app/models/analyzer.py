from pydantic import BaseModel, Field, validator , EmailStr
from datetime import datetime
from typing import Optional


from app.utils.mongo import db
from bson import ObjectId   


class CreateCandidate(BaseModel):
    candidate_name: Optional[str] = Field(None)
    user_id: str
    email: Optional[EmailStr] = Field(None)    
    phone: Optional[str] = Field(None)
    hr_name: Optional[str] = Field(None)
    job_position: Optional[str] = Field(None)

class AddCandidate(CreateCandidate):
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_deleted: bool = Field(default=False)


class AnalyzedData(BaseModel):
    candidate_id: str
    user_id: str
    resume_text: str
    job_description: str
    analyze_answer_response: Optional[dict] = Field(None)


class AddAnalyzedData(AnalyzedData):
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_deleted: bool = Field(default=False)


class QuizQuestion(BaseModel):
    candidate_id: str
    question: str = Field(description="Quiz question text")
    options: list[str] = Field(description="List of 4 options")
    correct_answer: str = Field(description="Correct answer for the question")

class AddQuizQuestions(QuizQuestion):
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_deleted: bool = Field(default=False)


class SingleQuizQuestion(BaseModel):
    type: str
    quiz_id: str
    candidate_uid: str
    user_answer: str