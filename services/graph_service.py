import logging
from typing import List, Dict, Tuple
from sqlalchemy.orm import Session
from rdflib import Graph, Namespace, Literal, URIRef, RDF, RDFS
from rdflib.namespace import XSD
import os

from models import StudentDB, ModuleDB, StudentCompetencyDB, PrerequisiteDB
from schemas import RecommendationItem

logger = logging.getLogger(__name__)

class GraphService:
    """
    Knowledge Graph Service for content-based recommendations.
    Uses RDF/OWL ontology to model academic relationships.
    """
    
    def __init__(self):
        self.g = Graph()
        self.ac = Namespace("http://academic.example.org/")
        self.g.bind("ac", self.ac)
        self.ontology_path = "ontology.rdf"
    
    def create_ontology(self):
        """Create the academic ontology with classes and properties"""
        # Define classes
        self.g.add((self.ac.Student, RDF.type, RDFS.Class))
        self.g.add((self.ac.Module, RDF.type, RDFS.Class))
        self.g.add((self.ac.Competency, RDF.type, RDFS.Class))
        
        # Define properties
        self.g.add((self.ac.hasCompetency, RDF.type, RDF.Property))
        self.g.add((self.ac.hasCompetency, RDFS.domain, self.ac.Student))
        self.g.add((self.ac.hasCompetency, RDFS.range, self.ac.Competency))
        
        self.g.add((self.ac.teaches, RDF.type, RDF.Property))
        self.g.add((self.ac.teaches, RDFS.domain, self.ac.Module))
        self.g.add((self.ac.teaches, RDFS.range, self.ac.Competency))
        
        self.g.add((self.ac.prerequisite, RDF.type, RDF.Property))
        self.g.add((self.ac.prerequisite, RDFS.domain, self.ac.Module))
        self.g.add((self.ac.prerequisite, RDFS.range, self.ac.Module))
        
        self.g.add((self.ac.hasLevel, RDF.type, RDF.Property))
        self.g.add((self.ac.hasLevel, RDFS.domain, self.ac.Student))
        
        logger.info("Ontology created successfully")
    
    def populate_graph(self, db: Session):
        """Populate the graph with data from database"""
        try:
            # Add students
            students = db.query(StudentDB).all()
            for student in students:
                student_uri = self.ac[f"student_{student.id}"]
                self.g.add((student_uri, RDF.type, self.ac.Student))
                self.g.add((student_uri, RDFS.label, Literal(student.name)))
            
            # Add modules
            modules = db.query(ModuleDB).all()
            for module in modules:
                module_uri = self.ac[f"module_{module.id}"]
                self.g.add((module_uri, RDF.type, self.ac.Module))
                self.g.add((module_uri, RDFS.label, Literal(module.title)))
                self.g.add((module_uri, RDFS.comment, Literal(module.description)))
            
            # Add competencies
            competencies = db.query(StudentCompetencyDB).all()
            for comp in competencies:
                student_uri = self.ac[f"student_{comp.student_id}"]
                competency_uri = self.ac[f"competency_{comp.competency_id}"]
                self.g.add((student_uri, self.ac.hasCompetency, competency_uri))
                self.g.add((
                    student_uri,
                    self.ac.hasLevel,
                    Literal(comp.proficiency_level, datatype=XSD.float)
                ))
            
            # Add prerequisites
            prerequisites = db.query(PrerequisiteDB).all()
            for prereq in prerequisites:
                module_uri = self.ac[f"module_{prereq.module_id}"]
                prereq_uri = self.ac[f"module_{prereq.prerequisite_module_id}"]
                self.g.add((module_uri, self.ac.prerequisite, prereq_uri))
            
            logger.info(f"Graph populated with {len(self.g)} triples")
        except Exception as e:
            logger.error(f"Error populating graph: {str(e)}")
            raise
    
    def get_recommendations(self, student_id: int, limit: int, db: Session) -> List[RecommendationItem]:
        """
        Get recommendations using SPARQL queries on the Knowledge Graph.
        Strategy: Find modules that teach competencies needed for advancement
        """
        try:
            # Ensure graph is populated
            self.populate_graph(db)
            
            recommendations = []
            student_uri = f"http://academic.example.org/student_{student_id}"
            
            # Query: Find modules related to student's competencies
            query = f"""
            PREFIX ac: <http://academic.example.org/>
            SELECT ?module ?label ?description
            WHERE {{
                ac:student_{student_id} ac:hasCompetency ?competency .
                ?module ac:teaches ?competency .
                ?module rdf:type ac:Module .
                ?module rdfs:label ?label .
                ?module rdfs:comment ?description .
            }}
            """
            
            results = self.g.query(query)
            
            # Process results
            scored_modules = {}
            for row in results:
                module_uri = str(row.module)
                module_id = int(module_uri.split("_")[-1])
                
                # Avoid modules already taken
                existing = db.query(StudentDB).filter(
                    StudentDB.id == student_id
                ).first()
                
                if module_id not in scored_modules:
                    # Score based on competency alignment
                    score = self._calculate_semantic_score(student_id, module_id, db)
                    scored_modules[module_id] = {
                        "title": str(row.label),
                        "score": score,
                        "reason": "Aligns with your competencies"
                    }
            
            # Sort and limit
            sorted_modules = sorted(
                scored_modules.items(),
                key=lambda x: x[1]["score"],
                reverse=True
            )[:limit]
            
            for module_id, data in sorted_modules:
                recommendations.append(RecommendationItem(
                    module_id=module_id,
                    module_title=data["title"],
                    score=data["score"],
                    confidence=0.85,
                    reason=data["reason"],
                    graph_score=data["score"]
                ))
            
            return recommendations
        
        except Exception as e:
            logger.error(f"Error in graph recommendations: {str(e)}")
            return []
    
    def _calculate_semantic_score(self, student_id: int, module_id: int, db: Session) -> float:
        """Calculate recommendation score based on semantic relationships"""
        score = 0.5  # Base score
        
        # Add points for prerequisite satisfaction
        module = db.query(ModuleDB).filter(ModuleDB.id == module_id).first()
        if module:
            prerequisites = db.query(PrerequisiteDB).filter(
                PrerequisiteDB.module_id == module_id
            ).all()
            
            if not prerequisites:
                score += 0.3  # No prerequisites boost score
            else:
                # Check if student has completed prerequisites
                completed_prereqs = 0
                for prereq in prerequisites:
                    # Check interactions to see if student completed prerequisite
                    from models import InteractionDB
                    interaction = db.query(InteractionDB).filter(
                        InteractionDB.student_id == student_id,
                        InteractionDB.module_id == prereq.prerequisite_module_id
                    ).first()
                    if interaction and interaction.completion_rate > 0.8:
                        completed_prereqs += 1
                
                score += (completed_prereqs / len(prerequisites)) * 0.3
        
        return min(score, 1.0)
    
    def load_ontology(self):
        """Load ontology from file or create new"""
        if os.path.exists(self.ontology_path):
            self.g.parse(self.ontology_path, format="xml")
            logger.info("Ontology loaded from file")
        else:
            self.create_ontology()
            self.g.serialize(destination=self.ontology_path, format="xml")
            logger.info("Ontology created and saved")
