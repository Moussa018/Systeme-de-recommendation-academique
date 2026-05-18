import random
from faker import Faker
from sqlalchemy.orm import Session
from database import SessionLocal, engine
from models import Base, StudentDB, ModuleDB, CompetencyDB, StudentCompetencyDB, InteractionDB, PrerequisiteDB, ModuleCompetencyDB
import logging

logger = logging.getLogger(__name__)
fake = Faker()

def generate_sample_data():
    """Generate comprehensive sample data for testing"""
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    try:
        logger.info("Generating sample data...")
        
        # Check if data already exists
        if db.query(StudentDB).count() > 0:
            logger.info("Sample data already exists")
            return
        
        # 1. Create competencies
        competencies = [
            {"name": "Python Programming", "category": "Programming", "description": "Core Python development skills"},
            {"name": "Data Analysis", "category": "Data Science", "description": "Data manipulation and statistical analysis"},
            {"name": "Machine Learning", "category": "AI", "description": "ML algorithms and implementation"},
            {"name": "Web Development", "category": "Backend", "description": "Web framework and API development"},
            {"name": "Database Design", "category": "Databases", "description": "Database modeling and SQL"},
            {"name": "Cloud Computing", "category": "DevOps", "description": "Cloud infrastructure and deployment"},
            {"name": "Data Visualization", "category": "Data Science", "description": "Creating visual representations of data"},
            {"name": "Natural Language Processing", "category": "AI", "description": "Text processing and NLP techniques"},
        ]
        
        comp_objects = []
        for comp in competencies:
            c = CompetencyDB(**comp)
            db.add(c)
            comp_objects.append(c)
        db.commit()
        logger.info(f"Created {len(comp_objects)} competencies")
        
        # 2. Create modules
        modules_data = [
            {
                "title": "Introduction to Python",
                "code": "CS101",
                "description": "Fundamentals of Python programming",
                "credits": 3,
                "difficulty": "beginner"
            },
            {
                "title": "Advanced Python",
                "code": "CS201",
                "description": "Advanced Python concepts and patterns",
                "credits": 3,
                "difficulty": "intermediate"
            },
            {
                "title": "Data Science Fundamentals",
                "code": "DS101",
                "description": "Introduction to data science and analysis",
                "credits": 4,
                "difficulty": "intermediate"
            },
            {
                "title": "Machine Learning Basics",
                "code": "AI101",
                "description": "Introduction to machine learning algorithms",
                "credits": 4,
                "difficulty": "intermediate"
            },
            {
                "title": "Advanced Machine Learning",
                "code": "AI201",
                "description": "Deep learning and neural networks",
                "credits": 4,
                "difficulty": "advanced"
            },
            {
                "title": "Web Development with FastAPI",
                "code": "WEB201",
                "description": "Building APIs with FastAPI framework",
                "credits": 3,
                "difficulty": "intermediate"
            },
            {
                "title": "Database Design",
                "code": "DB101",
                "description": "Relational database design and SQL",
                "credits": 3,
                "difficulty": "intermediate"
            },
            {
                "title": "Cloud Computing with AWS",
                "code": "CLOUD201",
                "description": "Cloud infrastructure and deployment",
                "credits": 3,
                "difficulty": "intermediate"
            },
            {
                "title": "Natural Language Processing",
                "code": "NLP301",
                "description": "Advanced NLP techniques and applications",
                "credits": 4,
                "difficulty": "advanced"
            },
            {
                "title": "Data Visualization",
                "code": "DV101",
                "description": "Creating effective data visualizations",
                "credits": 2,
                "difficulty": "beginner"
            },
        ]
        
        module_objects = []
        for mod in modules_data:
            m = ModuleDB(**mod)
            db.add(m)
            module_objects.append(m)
        db.commit()
        logger.info(f"Created {len(module_objects)} modules")
        
        # 3. Set up prerequisites
        prerequisites = [
            (module_objects[1].id, module_objects[0].id),  # Advanced Python requires Intro Python
            (module_objects[2].id, module_objects[0].id),  # Data Science requires Python
            (module_objects[3].id, module_objects[2].id),  # ML requires Data Science
            (module_objects[4].id, module_objects[3].id),  # Advanced ML requires Basic ML
            (module_objects[5].id, module_objects[0].id),  # FastAPI requires Python
            (module_objects[7].id, module_objects[5].id),  # Cloud requires Web Dev
            (module_objects[8].id, module_objects[3].id),  # NLP requires ML
        ]
        
        for module_id, prereq_id in prerequisites:
            p = PrerequisiteDB(module_id=module_id, prerequisite_module_id=prereq_id)
            db.add(p)
        db.commit()
        logger.info(f"Created {len(prerequisites)} prerequisites")

        # 3b. Link modules to competencies they teach
        module_competency_map = {
            "CS101": ["Python Programming"],
            "CS201": ["Python Programming"],
            "DS101": ["Data Analysis", "Data Visualization"],
            "AI101": ["Machine Learning", "Data Analysis"],
            "AI201": ["Machine Learning", "Natural Language Processing"],
            "WEB201": ["Web Development", "Python Programming"],
            "DB101": ["Database Design"],
            "CLOUD201": ["Cloud Computing"],
            "NLP301": ["Natural Language Processing", "Machine Learning"],
            "DV101": ["Data Visualization"],
        }

        module_competency_count = 0
        for module in module_objects:
            comp_names = module_competency_map.get(module.code, [])
            for comp_name in comp_names:
                competency = next((c for c in comp_objects if c.name == comp_name), None)
                if competency:
                    mc = ModuleCompetencyDB(module_id=module.id, competency_id=competency.id)
                    db.add(mc)
                    module_competency_count += 1
        db.commit()
        logger.info(f"Created {module_competency_count} module-competency links")

        # 4. Create students
        majors = ["Computer Science", "Data Science", "Software Engineering", "AI & ML"]
        students = []
        for i in range(15):
            student = StudentDB(
                name=fake.name(),
                email=fake.email(),
                major=random.choice(majors),
                year=random.randint(1, 4)
            )
            db.add(student)
            students.append(student)
        db.commit()
        logger.info(f"Created {len(students)} students")
        
        # 5. Assign competencies to students
        for student in students:
            # Each student has varying competency levels
            selected_comps = random.sample(comp_objects, k=random.randint(2, 6))
            for comp in selected_comps:
                student_comp = StudentCompetencyDB(
                    student_id=student.id,
                    competency_id=comp.id,
                    proficiency_level=random.uniform(0.3, 0.9)
                )
                db.add(student_comp)
        db.commit()
        logger.info("Assigned competencies to students")
        
        # 6. Create interactions (student-module interactions)
        interactions = []
        for student in students:
            # Each student has interacted with 3-8 modules
            selected_modules = random.sample(module_objects, k=random.randint(3, 8))
            for module in selected_modules:
                interaction = InteractionDB(
                    student_id=student.id,
                    module_id=module.id,
                    rating=random.uniform(1.0, 5.0),
                    completion_rate=random.uniform(0.4, 1.0) * 100
                )
                db.add(interaction)
                interactions.append(interaction)
        db.commit()
        logger.info(f"Created {len(interactions)} interactions")
        
        logger.info("Sample data generation completed successfully!")
        
    except Exception as e:
        logger.error(f"Error generating sample data: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    generate_sample_data()
