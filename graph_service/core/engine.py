from __future__ import annotations

import os
import logging
from typing import Any

from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, RDFS, OWL, XSD
import owlrl

from .queries import (
    GET_RECOMMENDATIONS,
    GET_STUDENT_PROFILE,
    GET_ALL_MODULES,
    GET_MODULE_PREREQUISITES,
    GET_MODULES_BY_SKILL,
    GET_ALL_STUDENTS,
    NS,
)

log = logging.getLogger(__name__)

ACADEMIC = Namespace(NS)
OWL_PATH = os.path.join(os.path.dirname(__file__), "ontology.owl")


class GraphEngine:
    """
    Central knowledge-graph engine.

    Lifecycle
    ---------
    1.  Load OWL ontology from disk.
    2.  Populate with instance data (called by data.loader.populate_graph).
    3.  Apply OWL-RL closure so that inferred triples are available.
    4.  Answer SPARQL queries.
    """

    def __init__(self) -> None:
        self.g: Graph = Graph()
        self.g.bind("academic", ACADEMIC)
        self._load_ontology()
        log.info("GraphEngine initialised (ontology loaded).")

    # ──────────────────────────── Private helpers ────────────────────────────

    def _load_ontology(self) -> None:
        if os.path.exists(OWL_PATH):
            self.g.parse(OWL_PATH, format="xml")
            log.info("Ontology loaded from %s (%d triples)", OWL_PATH, len(self.g))
        else:
            log.warning("Ontology file not found at %s", OWL_PATH)

    def _apply_reasoning(self) -> None:
        """Apply OWL-RL deductive closure over the current graph."""
        owlrl.DeductiveClosure(owlrl.OWLRL_Semantics).expand(self.g)
        log.info("OWL-RL reasoning applied (%d triples after closure)", len(self.g))

    @staticmethod
    def _uri(local: str) -> URIRef:
        return URIRef(f"{NS}{local}")

    # ──────────────────────────── Graph population ───────────────────────────

    def add_student(self, student_id: str, name: str, enrollment_year: int = 2024) -> None:
        s = self._uri(f"student_{student_id}")
        self.g.add((s, RDF.type, ACADEMIC.Student))
        self.g.add((s, ACADEMIC.studentId,      Literal(student_id, datatype=XSD.string)))
        self.g.add((s, ACADEMIC.studentName,    Literal(name,       datatype=XSD.string)))
        self.g.add((s, ACADEMIC.enrollmentYear, Literal(enrollment_year, datatype=XSD.integer)))

    def add_module(self, module_id: str, name: str, difficulty: int = 1, credits: int = 3) -> None:
        m = self._uri(f"module_{module_id}")
        self.g.add((m, RDF.type,                ACADEMIC.Module))
        self.g.add((m, ACADEMIC.moduleId,       Literal(module_id,  datatype=XSD.string)))
        self.g.add((m, ACADEMIC.moduleName,     Literal(name,       datatype=XSD.string)))
        self.g.add((m, ACADEMIC.difficultyLevel,Literal(difficulty, datatype=XSD.integer)))
        self.g.add((m, ACADEMIC.credits,        Literal(credits,    datatype=XSD.integer)))

    def add_skill(self, skill_id: str, name: str) -> None:
        sk = self._uri(f"skill_{skill_id}")
        self.g.add((sk, RDF.type,            ACADEMIC.Skill))
        self.g.add((sk, ACADEMIC.skillName,  Literal(name, datatype=XSD.string)))

    def link_student_skill(self, student_id: str, skill_id: str) -> None:
        self.g.add((
            self._uri(f"student_{student_id}"),
            ACADEMIC.hasMasteredSkill,
            self._uri(f"skill_{skill_id}"),
        ))

    def link_student_module_completed(self, student_id: str, module_id: str, grade: float = 12.0) -> None:
        self.g.add((
            self._uri(f"student_{student_id}"),
            ACADEMIC.hasCompletedModule,
            self._uri(f"module_{module_id}"),
        ))

    def link_module_requires_skill(self, module_id: str, skill_id: str) -> None:
        self.g.add((
            self._uri(f"module_{module_id}"),
            ACADEMIC.requiresSkill,
            self._uri(f"skill_{skill_id}"),
        ))

    def link_module_teaches_skill(self, module_id: str, skill_id: str) -> None:
        self.g.add((
            self._uri(f"module_{module_id}"),
            ACADEMIC.teachesSkill,
            self._uri(f"skill_{skill_id}"),
        ))

    def link_prerequisite(self, prereq_module_id: str, module_id: str) -> None:
        """prereq_module_id isPrerequisiteOf module_id"""
        self.g.add((
            self._uri(f"module_{prereq_module_id}"),
            ACADEMIC.isPrerequisiteOf,
            self._uri(f"module_{module_id}"),
        ))

    def finalize(self) -> None:
        """Call after all data has been loaded to trigger OWL-RL reasoning."""
        self._apply_reasoning()

    # ──────────────────────────── SPARQL query methods ───────────────────────

    def get_recommendations(self, student_id: str) -> list[dict[str, Any]]:
        """
        Return modules the student can take next, based on mastered skills
        satisfying all prerequisites. The student must not have completed them yet.
        """
        results = self.g.query(
            GET_RECOMMENDATIONS,
            initBindings={"studentId": Literal(student_id, datatype=XSD.string)},
        )
        recs: list[dict[str, Any]] = []
        for row in results:
            module_uri = str(row.module)
            recs.append({
                "module_id":        module_uri.split("#")[-1].replace("module_", ""),
                "module_name":      str(row.moduleName)     if row.moduleName      else "Unknown",
                "difficulty_level": int(row.difficultyLevel) if row.difficultyLevel else 1,
                "credits":          int(row.credits)         if row.credits         else 3,
                "source":           "knowledge_graph",
                "score":            1.0,  # all are fully eligible; fusion layer will weight
            })
        return recs

    def get_student_profile(self, student_id: str) -> dict[str, Any]:
        results = self.g.query(
            GET_STUDENT_PROFILE,
            initBindings={"studentId": Literal(student_id, datatype=XSD.string)},
        )
        skills: list[str]            = []
        completed: list[str]         = []
        name            = None
        enrollment_year = None

        for row in results:
            if row.studentName   and name is None:
                name = str(row.studentName)
            if row.enrollmentYear and enrollment_year is None:
                enrollment_year = int(row.enrollmentYear)
            if row.skillName:
                sn = str(row.skillName)
                if sn not in skills:
                    skills.append(sn)
            if row.moduleName:
                mn = str(row.moduleName)
                if mn not in completed:
                    completed.append(mn)

        return {
            "student_id":        student_id,
            "student_name":      name,
            "enrollment_year":   enrollment_year,
            "mastered_skills":   skills,
            "completed_modules": completed,
        }

    def get_all_modules(self) -> list[dict[str, Any]]:
        results = self.g.query(GET_ALL_MODULES)
        modules = []
        seen = set()
        for row in results:
            mid = str(row.moduleId) if row.moduleId else str(row.module).split("#")[-1]
            if mid in seen:
                continue
            seen.add(mid)
            modules.append({
                "module_id":        mid,
                "module_name":      str(row.moduleName)      if row.moduleName      else "Unknown",
                "difficulty_level": int(row.difficultyLevel) if row.difficultyLevel else 1,
                "credits":          int(row.credits)          if row.credits         else 3,
            })
        return modules

    def get_module_prerequisites(self, module_id: str) -> list[dict[str, Any]]:
        results = self.g.query(
            GET_MODULE_PREREQUISITES,
            initBindings={"moduleId": Literal(module_id, datatype=XSD.string)},
        )
        prereqs = []
        for row in results:
            prereqs.append({
                "prereq_id":   str(row.prereqModule).split("#")[-1].replace("module_", ""),
                "prereq_name": str(row.prereqName)       if row.prereqName       else "Unknown",
                "difficulty":  int(row.prereqDifficulty) if row.prereqDifficulty else 1,
            })
        return prereqs

    def get_modules_by_skill(self, skill_name: str) -> list[dict[str, Any]]:
        results = self.g.query(
            GET_MODULES_BY_SKILL,
            initBindings={"skillName": Literal(skill_name, datatype=XSD.string)},
        )
        modules = []
        for row in results:
            modules.append({
                "module_id":        str(row.module).split("#")[-1].replace("module_", ""),
                "module_name":      str(row.moduleName)      if row.moduleName      else "Unknown",
                "difficulty_level": int(row.difficultyLevel) if row.difficultyLevel else 1,
            })
        return modules

    def get_all_students(self) -> list[dict[str, Any]]:
        results = self.g.query(GET_ALL_STUDENTS)
        students = []
        seen = set()
        for row in results:
            sid = str(row.studentId) if row.studentId else str(row.student).split("#")[-1]
            if sid in seen:
                continue
            seen.add(sid)
            students.append({
                "student_id":      sid,
                "student_name":    str(row.studentName)    if row.studentName    else "Unknown",
                "enrollment_year": int(row.enrollmentYear) if row.enrollmentYear else 2024,
            })
        return students

    @property
    def triple_count(self) -> int:
        return len(self.g)