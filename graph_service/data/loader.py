from rdflib import URIRef, Literal, RDF
from faker import Faker
from core.engine import GraphEngine

fake = Faker()

def populate_graph(engine: GraphEngine):
    NS = engine.NS
    
    # 1. Créer 5 Modules de base
    modules = []
    for i in range(5):
        m_uri = URIRef(f"{NS}module_{i}")
        engine.g.add((m_uri, RDF.type, NS.Module))
        engine.g.add((m_uri, NS.hasName, Literal(fake.job() + " Basics")))
        modules.append(m_uri)

    # 2. Créer 10 Étudiants
    for i in range(10):
        s_uri = URIRef(f"{NS}student_{i}")
        engine.g.add((s_uri, RDF.type, NS.Student))
        engine.g.add((s_uri, NS.hasName, Literal(fake.name())))

    print(f"Peuplement terminé : {len(engine.g)} triplets au total.")