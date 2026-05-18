from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import logging

from database import engine, Base, get_db
from models import StudentDB, ModuleDB, InteractionDB
from schemas import StudentSchema, ModuleSchema, RecommendationResponse
from services.graph_service import GraphService
from services.ml_service import MLService
from services.fusion_service import FusionService
from services.evaluation_service import EvaluationService
from data_generator import generate_sample_data

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Academic Recommendation System",
    description="Hybrid system combining Knowledge Graphs and Machine Learning",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
graph_service = GraphService()
ml_service = MLService()
fusion_service = FusionService(graph_service, ml_service)
evaluation_service = EvaluationService(graph_service, ml_service, fusion_service)

@app.on_event("startup")
async def startup_event():
    """Initialize the system on startup"""
    logger.info("Initializing Academic Recommendation System...")
    
    # Load or generate sample data
    try:
        logger.info("Loading Knowledge Graph and ML models...")
        graph_service.load_ontology()
        logger.info("System initialized successfully")
    except Exception as e:
        logger.warning(f"First run detected. Generating sample data: {e}")
        # Generate sample data on first run
        generate_sample_data()

@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "graph_service": "operational",
            "ml_service": "operational",
            "fusion_service": "operational"
        }
    }

@app.get("/recommendations", response_model=RecommendationResponse, tags=["Recommendations"])
async def get_recommendations(
    student_id: int,
    limit: int = 5,
    use_graph: bool = True,
    use_ml: bool = True,
    db: Session = Depends(get_db)
):
    """
    Get personalized module recommendations for a student.
    
    - **student_id**: ID of the student
    - **limit**: Number of recommendations to return
    - **use_graph**: Include Knowledge Graph recommendations
    - **use_ml**: Include ML-based recommendations
    """
    try:
        # Verify student exists
        student = db.query(StudentDB).filter(StudentDB.id == student_id).first()
        if not student:
            raise HTTPException(status_code=404, detail=f"Student {student_id} not found")
        
        # Get recommendations from fusion service
        recommendations = fusion_service.get_recommendations(
            student_id=student_id,
            limit=limit,
            use_graph=use_graph,
            use_ml=use_ml,
            db=db
        )
        
        return RecommendationResponse(
            student_id=student_id,
            recommendations=recommendations,
            timestamp=datetime.now().isoformat(),
            method="hybrid"
        )
    
    except Exception as e:
        logger.error(f"Error generating recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/recommendations/graph-only", response_model=RecommendationResponse, tags=["Recommendations"])
async def get_graph_recommendations(
    student_id: int,
    limit: int = 5,
    db: Session = Depends(get_db)
):
    """Get recommendations based solely on Knowledge Graph"""
    try:
        student = db.query(StudentDB).filter(StudentDB.id == student_id).first()
        if not student:
            raise HTTPException(status_code=404, detail=f"Student {student_id} not found")
        
        recommendations = graph_service.get_recommendations(student_id, limit, db)
        
        return RecommendationResponse(
            student_id=student_id,
            recommendations=recommendations,
            timestamp=datetime.now().isoformat(),
            method="knowledge_graph"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/recommendations/ml-only", response_model=RecommendationResponse, tags=["Recommendations"])
async def get_ml_recommendations(
    student_id: int,
    limit: int = 5,
    db: Session = Depends(get_db)
):
    """Get recommendations based solely on Machine Learning"""
    try:
        student = db.query(StudentDB).filter(StudentDB.id == student_id).first()
        if not student:
            raise HTTPException(status_code=404, detail=f"Student {student_id} not found")
        
        recommendations = ml_service.get_recommendations(student_id, limit, db)
        
        return RecommendationResponse(
            student_id=student_id,
            recommendations=recommendations,
            timestamp=datetime.now().isoformat(),
            method="machine_learning"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/students", response_model=StudentSchema, tags=["Students"])
async def create_student(student: StudentSchema, db: Session = Depends(get_db)):
    """Create a new student"""
    db_student = StudentDB(**student.dict())
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    return db_student

@app.post("/modules", response_model=ModuleSchema, tags=["Modules"])
async def create_module(module: ModuleSchema, db: Session = Depends(get_db)):
    """Create a new module"""
    db_module = ModuleDB(**module.dict())
    db.add(db_module)
    db.commit()
    db.refresh(db_module)
    return db_module

@app.get("/metrics", tags=["Metrics"])
async def get_metrics(db: Session = Depends(get_db)):
    """Get system performance metrics"""
    student_count = db.query(StudentDB).count()
    module_count = db.query(ModuleDB).count()
    interaction_count = db.query(InteractionDB).count()

    return {
        "students": student_count,
        "modules": module_count,
        "interactions": interaction_count,
        "graph_status": "operational",
        "ml_status": "operational"
    }

@app.get("/evaluate", tags=["Evaluation"])
async def evaluate_system(top_k: int = 5, db: Session = Depends(get_db)):
    """
    Evaluate and compare all three recommendation approaches.
    Uses leave-one-out validation on student interactions.

    - **top_k**: Evaluate recommendation quality at this cutoff
    """
    try:
        logger.info(f"Starting system evaluation with top_k={top_k}...")
        result = evaluation_service.compare_approaches(db, top_k=top_k)

        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "evaluation": result
        }
    except Exception as e:
        logger.error(f"Error during evaluation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
