import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base
from models import StudentDB, ModuleDB, CompetencyDB, StudentCompetencyDB, InteractionDB
from services.graph_service import GraphService
from services.ml_service import MLService
from services.fusion_service import FusionService

# Use in-memory SQLite for testing
@pytest.fixture(scope="session")
def db_engine():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine

@pytest.fixture(scope="function")
def db_session(db_engine):
    connection = db_engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection)().__enter__()
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def sample_data(db_session):
    """Create sample data for testing"""
    # Create modules
    modules = [
        ModuleDB(title="Python Basics", code="CS101", description="Learn Python", credits=3, difficulty="beginner"),
        ModuleDB(title="Advanced Python", code="CS201", description="Advanced topics", credits=3, difficulty="intermediate"),
        ModuleDB(title="Data Science", code="DS101", description="Data science basics", credits=4, difficulty="intermediate"),
    ]
    db_session.add_all(modules)
    
    # Create students
    students = [
        StudentDB(name="Alice", email="alice@test.com", major="CS", year=1),
        StudentDB(name="Bob", email="bob@test.com", major="CS", year=2),
        StudentDB(name="Charlie", email="charlie@test.com", major="DS", year=2),
    ]
    db_session.add_all(students)
    
    # Create competencies
    competencies = [
        CompetencyDB(name="Python", category="Programming", description="Python skills"),
        CompetencyDB(name="Data Analysis", category="Data Science", description="Data analysis"),
    ]
    db_session.add_all(competencies)
    
    db_session.commit()
    return {
        "modules": modules,
        "students": students,
        "competencies": competencies
    }

class TestGraphService:
    def test_ontology_creation(self):
        service = GraphService()
        service.create_ontology()
        assert len(service.g) > 0
    
    def test_graph_population(self, db_session, sample_data):
        service = GraphService()
        service.create_ontology()
        service.populate_graph(db_session)
        assert len(service.g) > 0
    
    def test_recommendations_no_data(self, db_session):
        service = GraphService()
        service.create_ontology()
        recs = service.get_recommendations(999, 5, db_session)
        assert isinstance(recs, list)

class TestMLService:
    def test_ml_service_initialization(self):
        service = MLService(n_factors=10)
        assert service.n_factors == 10
        assert not service.model_trained
    
    def test_training_without_data(self, db_session):
        service = MLService()
        result = service.train(db_session)
        assert not result  # Should fail with empty database
    
    def test_recommendations_no_training(self, db_session):
        service = MLService()
        recs = service.get_recommendations(1, 5, db_session)
        assert isinstance(recs, list)

class TestFusionService:
    def test_fusion_initialization(self):
        graph_service = GraphService()
        ml_service = MLService()
        fusion_service = FusionService(graph_service, ml_service)
        assert fusion_service.graph_service is not None
        assert fusion_service.ml_service is not None
    
    def test_weight_calculation_cold_start(self, db_session, sample_data):
        graph_service = GraphService()
        ml_service = MLService()
        fusion_service = FusionService(graph_service, ml_service)
        
        student_id = sample_data["students"][0].id
        alpha, beta = fusion_service._calculate_weights(student_id, db_session)
        
        # Cold start should have higher alpha
        assert alpha > beta
    
    def test_recommendations_generation(self, db_session, sample_data):
        graph_service = GraphService()
        ml_service = MLService()
        fusion_service = FusionService(graph_service, ml_service)
        
        student_id = sample_data["students"][0].id
        recs = fusion_service.get_recommendations(
            student_id=student_id,
            limit=5,
            use_graph=True,
            use_ml=True,
            db=db_session
        )
        
        assert isinstance(recs, list)

class TestInteractionMatrix:
    def test_interaction_matrix_creation(self, db_session, sample_data):
        service = MLService()
        service.students = sample_data["students"]
        service.modules = sample_data["modules"]
        
        # Add some interactions
        interaction = InteractionDB(
            student_id=sample_data["students"][0].id,
            module_id=sample_data["modules"][0].id,
            rating=4.5,
            completion_rate=85.0
        )
        db_session.add(interaction)
        db_session.commit()
        
        interactions = db_session.query(InteractionDB).all()
        matrix = service._create_interaction_matrix(interactions)
        
        assert matrix.shape[0] == len(sample_data["students"])
        assert matrix.shape[1] == len(sample_data["modules"])

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
