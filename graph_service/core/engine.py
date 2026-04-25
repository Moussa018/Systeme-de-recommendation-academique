from rdflib import Graph, Namespace, URIRef
from core.queries import GET_RECOMMENDATIONS_SPARQL

class GraphEngine:
    def __init__(self):
        self.g = Graph()
        self.NS = Namespace("http://ensias.ma/academic#")
        self.load_ontology()

    def load_ontology(self):
        try:
            self.g.parse("core/ontology.owl", format="xml")
            print(f"Ontologie chargée : {len(self.g)} triplets.")
        except Exception as e:
            print(f"Erreur de chargement de l'ontologie : {e}")

    def get_recommendations(self, student_id: str):
        # On injecte l'ID de l'étudiant dans la requête SPARQL
        query = GET_RECOMMENDATIONS_SPARQL.replace("{student_id}", student_id)
        qres = self.g.query(query)
        
        recommendations = []
        for row in qres:
            recommendations.append({
                "module_uri": str(row.module),
                "module_name": str(row.moduleName),
                "score_graphe": 1.0  # Score initial pour le cold start [cite: 18]
            })
        return recommendations