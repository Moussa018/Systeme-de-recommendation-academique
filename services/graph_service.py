import logging
from typing import List, Dict, Tuple
from sqlalchemy.orm import Session
from rdflib import Graph, Namespace, Literal, URIRef, RDF, RDFS
from rdflib.namespace import XSD
import os

from models import StudentDB, ModuleDB, StudentCompetencyDB, PrerequisiteDB, ModuleCompetencyDB, CompetencyDB, InteractionDB
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
            # Idempotency guard — don't repopulate if already done
            if len(self.g) > 20:
                logger.debug("Graph already populated, skipping populate_graph")
                return

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

            # Add module-competency (teaches) relationships
            module_competencies = db.query(ModuleCompetencyDB).all()
            for mc in module_competencies:
                module_uri = self.ac[f"module_{mc.module_id}"]
                competency_uri = self.ac[f"competency_{mc.competency_id}"]
                self.g.add((module_uri, self.ac.teaches, competency_uri))

            # Add competencies
            student_competencies = db.query(StudentCompetencyDB).all()
            for comp in student_competencies:
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
        Strategy: Find modules that teach competencies the student has or needs
        """
        try:
            # Ensure graph is populated
            self.populate_graph(db)

            recommendations = []

            # Get modules student has already taken
            taken_modules = db.query(InteractionDB.module_id).filter(
                InteractionDB.student_id == student_id
            ).all()
            taken_module_ids = {m[0] for m in taken_modules}

            # Query 1: Find modules that teach competencies the student already has
            query1 = f"""
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

            results1 = self.g.query(query1)

            scored_modules = {}
            for row in results1:
                module_uri = str(row.module)
                module_id = int(module_uri.split("_")[-1])

                # Skip already taken modules
                if module_id not in taken_module_ids and module_id not in scored_modules:
                    score = self._calculate_semantic_score(student_id, module_id, db)
                    scored_modules[module_id] = {
                        "title": str(row.label),
                        "score": score,
                        "reason": "Builds on your current skills"
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

        # Get module and its competencies
        module = db.query(ModuleDB).filter(ModuleDB.id == module_id).first()
        if module:
            # Check prerequisites
            prerequisites = db.query(PrerequisiteDB).filter(
                PrerequisiteDB.module_id == module_id
            ).all()

            if not prerequisites:
                score += 0.2  # No prerequisites boost score slightly
            else:
                # Check if student has completed prerequisites (completion_rate > 0.8)
                completed_prereqs = 0
                for prereq in prerequisites:
                    interaction = db.query(InteractionDB).filter(
                        InteractionDB.student_id == student_id,
                        InteractionDB.module_id == prereq.prerequisite_module_id
                    ).first()
                    if interaction and interaction.completion_rate > 80.0:
                        completed_prereqs += 1

                # Prerequisite bonus: 0.2 if all met, proportional otherwise
                if len(prerequisites) > 0:
                    score += (completed_prereqs / len(prerequisites)) * 0.2

            # Check competency alignment: boost if student has high proficiency in related skills
            module_competencies = db.query(ModuleCompetencyDB).filter(
                ModuleCompetencyDB.module_id == module_id
            ).all()

            if module_competencies:
                total_alignment = 0.0
                for mc in module_competencies:
                    student_comp = db.query(StudentCompetencyDB).filter(
                        StudentCompetencyDB.student_id == student_id,
                        StudentCompetencyDB.competency_id == mc.competency_id
                    ).first()
                    if student_comp:
                        total_alignment += student_comp.proficiency_level

                if total_alignment > 0:
                    avg_alignment = total_alignment / len(module_competencies)
                    score += avg_alignment * 0.3

        return min(score, 1.0)
    
    def add_student(self, student_id: int, db: Session):
        """Incrementally add a newly registered student and their competencies to
        the in-memory graph, so recommendations work without a server restart.
        RDF triples are a set, so this is safe even if populate_graph later runs."""
        try:
            student = db.query(StudentDB).filter(StudentDB.id == student_id).first()
            if not student:
                return

            student_uri = self.ac[f"student_{student.id}"]
            self.g.add((student_uri, RDF.type, self.ac.Student))
            self.g.add((student_uri, RDFS.label, Literal(student.name)))

            competencies = db.query(StudentCompetencyDB).filter(
                StudentCompetencyDB.student_id == student_id
            ).all()
            for comp in competencies:
                competency_uri = self.ac[f"competency_{comp.competency_id}"]
                self.g.add((student_uri, self.ac.hasCompetency, competency_uri))
                self.g.add((
                    student_uri,
                    self.ac.hasLevel,
                    Literal(comp.proficiency_level, datatype=XSD.float)
                ))

            logger.info(f"Added student {student_id} to graph ({len(competencies)} competencies)")
        except Exception as e:
            logger.error(f"Error adding student to graph: {str(e)}")

    def load_ontology(self):
        """Load ontology from file or create new"""
        if os.path.exists(self.ontology_path):
            self.g.parse(self.ontology_path, format="xml")
            logger.info("Ontology loaded from file")
        else:
            self.create_ontology()
            self.g.serialize(destination=self.ontology_path, format="xml")
            logger.info("Ontology created and saved")
