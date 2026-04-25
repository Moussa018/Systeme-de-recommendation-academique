from fastapi import FastAPI
from core.engine import GraphEngine
from data.loader import populate_graph

app = FastAPI(title="ENSIAS Academic Graph Service")

# Initialisation
engine = GraphEngine()

@app.on_event("startup")
async def startup_event():
    # On peuple le graphe au démarrage pour avoir des données de test
    populate_graph(engine)

@app.get("/recommendations/{student_id}")
async def recommend(student_id: str):
    """Retourne des recommandations basées sur le Knowledge Graph [cite: 27]"""
    results = engine.get_recommendations(student_id)
    return {
        "status": "success",
        "student_id": student_id,
        "results": results
    }