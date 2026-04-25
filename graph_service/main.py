from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from core.engine import GraphEngine
from data.loader import populate_graph

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(name)s  %(message)s")
log = logging.getLogger(__name__)

# ── Singleton engine ──────────────────────────────────────────────────────
engine: GraphEngine | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global engine
    log.info("Starting up Graph Service …")
    engine = GraphEngine()
    populate_graph(engine)
    log.info("Graph Service ready ✓  (%d triples)", engine.triple_count)
    yield
    log.info("Graph Service shutting down.")


app = FastAPI(
    title="ENSIAS Academic Graph Service",
    description="Knowledge-Graph microservice – RDF/OWL + SPARQL recommendations",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Pydantic schemas ──────────────────────────────────────────────────────

class RecommendationItem(BaseModel):
    module_id: str
    module_name: str
    difficulty_level: int
    credits: int
    source: str
    score: float


class RecommendationResponse(BaseModel):
    status: str
    student_id: str
    results: list[RecommendationItem]
    total: int


class StudentProfileResponse(BaseModel):
    status: str
    student_id: str
    profile: dict[str, Any]


# ── Endpoints ─────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    """Service health check."""
    return {
        "status": "healthy",
        "service": "graph_service",
        "triple_count": engine.triple_count if engine else 0,
    }


@app.get("/recommend/{student_id}", response_model=RecommendationResponse)
async def recommend(student_id: str):
    """
    Retourne des recommandations basées sur le Knowledge Graph [cite: 27]
    Les modules suggérés satisfont tous les prérequis sémantiques de l'étudiant.
    """
    if engine is None:
        raise HTTPException(status_code=503, detail="Engine not ready")

    results = engine.get_recommendations(student_id)
    return RecommendationResponse(
        status="success",
        student_id=student_id,
        results=results,
        total=len(results),
    )


@app.get("/student/{student_id}/profile", response_model=StudentProfileResponse)
async def student_profile(student_id: str):
    """Retourne le profil complet d'un étudiant (skills, modules complétés)."""
    if engine is None:
        raise HTTPException(status_code=503, detail="Engine not ready")

    profile = engine.get_student_profile(student_id)
    if not profile["student_name"]:
        raise HTTPException(status_code=404, detail=f"Student {student_id!r} not found")

    return StudentProfileResponse(status="success", student_id=student_id, profile=profile)


@app.get("/modules")
async def list_modules():
    """Liste tous les modules du curriculum."""
    if engine is None:
        raise HTTPException(status_code=503, detail="Engine not ready")
    return {"status": "success", "modules": engine.get_all_modules(), "total": len(engine.get_all_modules())}


@app.get("/modules/{module_id}/prerequisites")
async def module_prerequisites(module_id: str):
    """Retourne la chaîne de prérequis d'un module."""
    if engine is None:
        raise HTTPException(status_code=503, detail="Engine not ready")
    prereqs = engine.get_module_prerequisites(module_id)
    return {"status": "success", "module_id": module_id, "prerequisites": prereqs}


@app.get("/students")
async def list_students():
    """Liste tous les étudiants (admin)."""
    if engine is None:
        raise HTTPException(status_code=503, detail="Engine not ready")
    students = engine.get_all_students()
    return {"status": "success", "students": students, "total": len(students)}


@app.get("/skills/{skill_name}/modules")
async def modules_by_skill(skill_name: str):
    """Modules qui enseignent un skill donné."""
    if engine is None:
        raise HTTPException(status_code=503, detail="Engine not ready")
    modules = engine.get_modules_by_skill(skill_name)
    return {"status": "success", "skill": skill_name, "modules": modules}