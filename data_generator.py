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
        
        # 2. Create modules (30 courses total)
        modules_data = [
            {"title": "Introduction to Python", "code": "CS101", "description": "Fundamentals of Python programming", "credits": 3, "difficulty": "beginner"},
            {"title": "Advanced Python", "code": "CS201", "description": "Advanced Python concepts and patterns", "credits": 3, "difficulty": "intermediate"},
            {"title": "Data Science Fundamentals", "code": "DS101", "description": "Introduction to data science and analysis", "credits": 4, "difficulty": "intermediate"},
            {"title": "Machine Learning Basics", "code": "AI101", "description": "Introduction to machine learning algorithms", "credits": 4, "difficulty": "intermediate"},
            {"title": "Advanced Machine Learning", "code": "AI201", "description": "Deep learning and neural networks", "credits": 4, "difficulty": "advanced"},
            {"title": "Web Development with FastAPI", "code": "WEB201", "description": "Building APIs with FastAPI framework", "credits": 3, "difficulty": "intermediate"},
            {"title": "Database Design", "code": "DB101", "description": "Relational database design and SQL", "credits": 3, "difficulty": "intermediate"},
            {"title": "Cloud Computing with AWS", "code": "CLOUD201", "description": "Cloud infrastructure and deployment", "credits": 3, "difficulty": "intermediate"},
            {"title": "Natural Language Processing", "code": "NLP301", "description": "Advanced NLP techniques and applications", "credits": 4, "difficulty": "advanced"},
            {"title": "Data Visualization", "code": "DV101", "description": "Creating effective data visualizations", "credits": 2, "difficulty": "beginner"},
            {"title": "JavaScript Essentials", "code": "WEB101", "description": "Core JavaScript programming for web development", "credits": 3, "difficulty": "beginner"},
            {"title": "React.js Development", "code": "WEB301", "description": "Building modern UIs with React", "credits": 4, "difficulty": "intermediate"},
            {"title": "Node.js Backend Development", "code": "WEB302", "description": "Server-side JavaScript with Node.js", "credits": 4, "difficulty": "intermediate"},
            {"title": "Statistics for Data Science", "code": "DS201", "description": "Statistical methods for data analysis", "credits": 3, "difficulty": "intermediate"},
            {"title": "Deep Learning Advanced", "code": "AI301", "description": "Neural networks and advanced deep learning", "credits": 4, "difficulty": "advanced"},
            {"title": "Computer Vision", "code": "AI302", "description": "Image processing and computer vision applications", "credits": 4, "difficulty": "advanced"},
            {"title": "Software Engineering Principles", "code": "CS301", "description": "Design patterns and software architecture", "credits": 3, "difficulty": "intermediate"},
            {"title": "Microservices Architecture", "code": "ARCH201", "description": "Designing scalable microservices systems", "credits": 4, "difficulty": "advanced"},
            {"title": "DevOps Fundamentals", "code": "DEVOPS101", "description": "CI/CD, containerization, and deployment", "credits": 3, "difficulty": "intermediate"},
            {"title": "Kubernetes & Container Orchestration", "code": "DEVOPS201", "description": "Managing containerized applications at scale", "credits": 4, "difficulty": "advanced"},
            {"title": "PostgreSQL Advanced", "code": "DB201", "description": "Advanced SQL and database optimization", "credits": 3, "difficulty": "intermediate"},
            {"title": "NoSQL Databases", "code": "DB301", "description": "MongoDB, Cassandra, and distributed databases", "credits": 3, "difficulty": "intermediate"},
            {"title": "Big Data Processing", "code": "DS301", "description": "Apache Spark and distributed data processing", "credits": 4, "difficulty": "advanced"},
            {"title": "Time Series Analysis", "code": "DS302", "description": "Forecasting and temporal data analysis", "credits": 3, "difficulty": "intermediate"},
            {"title": "Reinforcement Learning", "code": "AI401", "description": "Learning through agent interactions and rewards", "credits": 4, "difficulty": "advanced"},
            {"title": "Recommender Systems", "code": "AI402", "description": "Collaborative filtering and personalization", "credits": 4, "difficulty": "advanced"},
            {"title": "Cybersecurity Essentials", "code": "SEC101", "description": "Security fundamentals and best practices", "credits": 3, "difficulty": "intermediate"},
            {"title": "Cryptography", "code": "SEC201", "description": "Encryption, hashing, and secure communication", "credits": 3, "difficulty": "advanced"},
            {"title": "Mobile App Development", "code": "MOB101", "description": "Cross-platform mobile development", "credits": 3, "difficulty": "intermediate"},
            {"title": "Blockchain Technology", "code": "CHAIN101", "description": "Blockchain fundamentals and smart contracts", "credits": 4, "difficulty": "advanced"},
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
            "WEB101": ["Web Development"],
            "WEB301": ["Web Development"],
            "WEB302": ["Web Development", "Python Programming"],
            "DS201": ["Data Analysis"],
            "AI301": ["Machine Learning"],
            "AI302": ["Machine Learning"],
            "CS301": ["Python Programming"],
            "ARCH201": ["Web Development", "Cloud Computing"],
            "DEVOPS101": ["Cloud Computing"],
            "DEVOPS201": ["Cloud Computing"],
            "DB201": ["Database Design"],
            "DB301": ["Database Design"],
            "DS302": ["Data Analysis"],
            "DS301": ["Data Analysis"],
            "AI401": ["Machine Learning"],
            "AI402": ["Machine Learning"],
            "SEC101": ["Database Design"],
            "SEC201": ["Database Design"],
            "MOB101": ["Web Development"],
            "CHAIN101": ["Database Design"],
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
        
        # 5. Assign competencies to students (track proficiency per student for rating logic)
        student_proficiency = {}  # {student_id: {competency_id: proficiency_level}}
        for student in students:
            # Each student has varying competency levels
            selected_comps = random.sample(comp_objects, k=random.randint(3, 6))
            student_proficiency[student.id] = {}
            for comp in selected_comps:
                level = random.uniform(0.4, 0.95)
                student_comp = StudentCompetencyDB(
                    student_id=student.id,
                    competency_id=comp.id,
                    proficiency_level=level
                )
                db.add(student_comp)
                student_proficiency[student.id][comp.id] = level
        db.commit()
        logger.info("Assigned competencies to students")

        # Build module -> competency ids lookup (so ratings can reflect real alignment)
        module_comp_ids = {}  # {module_id: [competency_id, ...]}
        for module in module_objects:
            comp_names = module_competency_map.get(module.code, [])
            ids = [c.id for c in comp_objects if c.name in comp_names]
            module_comp_ids[module.id] = ids

        def compute_rating(student, module):
            """
            Generate a realistic, structured rating.
            A student rates a module higher when they are strong in the
            competencies the module teaches. This gives the SVD a real
            pattern to learn instead of pure noise.
            """
            prof = student_proficiency.get(student.id, {})
            comp_ids = module_comp_ids.get(module.id, [])

            if comp_ids:
                # Average proficiency the student has in this module's competencies
                # (missing competency counts as a small baseline interest)
                levels = [prof.get(cid, 0.15) for cid in comp_ids]
                affinity = sum(levels) / len(levels)
            else:
                affinity = 0.3  # No competency mapping -> neutral interest

            # Map affinity (0..1) to a realistic, positive-skewed rating band:
            #   affinity 0.0 -> ~2.6,  affinity 1.0 -> ~4.8
            base = 2.6 + affinity * 2.2
            rating = base + random.gauss(0, 0.35)
            rating = max(1.5, min(5.0, rating))
            rating = round(rating * 2) / 2  # snap to nearest 0.5 for realism

            # Completion correlates with how much they liked it, plus noise
            completion = 45 + (rating / 5.0) * 50 + random.gauss(0, 8)
            completion = max(30.0, min(100.0, completion))

            return rating, completion

        # 6. Create interactions (student-module interactions)
        interactions = []
        for student in students:
            # Each student starts with 3-8 interactions; structured ratings via affinity.
            # With 30 courses there's still plenty left to explore.
            selected_modules = random.sample(module_objects, k=random.randint(3, 8))
            for module in selected_modules:
                rating, completion = compute_rating(student, module)
                interaction = InteractionDB(
                    student_id=student.id,
                    module_id=module.id,
                    rating=rating,
                    completion_rate=completion
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
