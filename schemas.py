from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime

class StudentSchema(BaseModel):
    name: str
    email: EmailStr
    major: str
    year: int
    
    class Config:
        from_attributes = True

class ModuleSchema(BaseModel):
    title: str
    code: str
    description: str
    credits: int
    difficulty: str  # beginner, intermediate, advanced
    
    class Config:
        from_attributes = True

class CompetencySchema(BaseModel):
    name: str
    description: str
    category: str
    
    class Config:
        from_attributes = True

class InteractionSchema(BaseModel):
    student_id: int
    module_id: int
    rating: float
    completion_rate: float
    
    class Config:
        from_attributes = True

class RecommendationItem(BaseModel):
    module_id: int
    module_title: str
    score: float
    confidence: float
    reason: str
    graph_score: Optional[float] = None
    ml_score: Optional[float] = None

class RecommendationResponse(BaseModel):
    student_id: int
    recommendations: List[RecommendationItem]
    timestamp: str
    method: str  # hybrid, knowledge_graph, machine_learning

class EvaluationMetrics(BaseModel):
    precision: float
    recall: float
    f1_score: float
    rmse: float
    mae: float
    ndcg: float
