from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class StudentDB(Base):
    __tablename__ = "students"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), index=True)
    email = Column(String(255), unique=True, index=True)
    major = Column(String(255))
    year = Column(Integer)  # Academic year
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    interactions = relationship("InteractionDB", back_populates="student")
    competencies = relationship("StudentCompetencyDB", back_populates="student")

class ModuleDB(Base):
    __tablename__ = "modules"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), index=True)
    code = Column(String(50), unique=True)
    description = Column(Text)
    credits = Column(Integer)
    difficulty = Column(String(50))  # beginner, intermediate, advanced
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    interactions = relationship("InteractionDB", back_populates="module")
    prerequisites = relationship("PrerequisiteDB", foreign_keys="PrerequisiteDB.module_id", back_populates="module")
    competencies = relationship("ModuleCompetencyDB", back_populates="module")
    

class InteractionDB(Base):
    __tablename__ = "interactions"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), index=True)
    module_id = Column(Integer, ForeignKey("modules.id"), index=True)
    rating = Column(Float)  # Rating given by student (0-5)
    completion_rate = Column(Float)  # 0-100
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    student = relationship("StudentDB", back_populates="interactions")
    module = relationship("ModuleDB", back_populates="interactions")

class CompetencyDB(Base):
    __tablename__ = "competencies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True)
    description = Column(Text)
    category = Column(String(100))

    # Relationships
    student_competencies = relationship("StudentCompetencyDB", back_populates="competency")
    module_competencies = relationship("ModuleCompetencyDB", back_populates="competency")

class StudentCompetencyDB(Base):
    __tablename__ = "student_competencies"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), index=True)
    competency_id = Column(Integer, ForeignKey("competencies.id"), index=True)
    proficiency_level = Column(Float)  # 0-1 scale
    
    # Relationships
    student = relationship("StudentDB", back_populates="competencies")
    competency = relationship("CompetencyDB", back_populates="student_competencies")

class PrerequisiteDB(Base):
    __tablename__ = "prerequisites"

    id = Column(Integer, primary_key=True, index=True)
    module_id = Column(Integer, ForeignKey("modules.id"), index=True)
    prerequisite_module_id = Column(Integer, ForeignKey("modules.id"))

    # Relationships
    module = relationship("ModuleDB", foreign_keys=[module_id], back_populates="prerequisites")

class ModuleCompetencyDB(Base):
    __tablename__ = "module_competencies"

    id = Column(Integer, primary_key=True, index=True)
    module_id = Column(Integer, ForeignKey("modules.id"), index=True)
    competency_id = Column(Integer, ForeignKey("competencies.id"), index=True)

    # Relationships
    module = relationship("ModuleDB", back_populates="competencies")
    competency = relationship("CompetencyDB", back_populates="module_competencies")
