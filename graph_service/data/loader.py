from __future__ import annotations

import random
import logging
from faker import Faker

log = logging.getLogger(__name__)
fake = Faker("fr_FR")
random.seed(42)


# ── Static curriculum ──────────────────────────────────────────────────────

SKILLS = [
    # --- Core foundations ---
    ("sk01", "Python"),
    ("sk02", "Mathématiques"),
    ("sk03", "Algèbre Linéaire"),
    ("sk04", "Probabilités & Statistiques"),
    ("sk05", "Bases de Données Relationnelles"),
    ("sk06", "Algorithmique"),
    # --- Classical ML & AI ---
    ("sk07", "Machine Learning"),
    ("sk08", "Deep Learning"),
    ("sk09", "Traitement du Langage Naturel"),
    ("sk10", "Systèmes Distribués"),
    # --- Languages ---
    ("sk11", "Java"),
    ("sk12", "Réseaux Informatiques"),
    ("sk13", "Sécurité Informatique"),
    # --- Data & Cloud ---
    ("sk14", "Data Engineering"),
    ("sk15", "Cloud Computing"),
    # --- New: Languages & Systems ---
    ("sk16", "Programmation R"),
    ("sk17", "Scala & Programmation Fonctionnelle"),
    ("sk18", "C/C++ & Programmation Système"),
    # --- New: Advanced Math ---
    ("sk19", "Statistiques Bayésiennes"),
    ("sk20", "Optimisation Mathématique"),
    ("sk21", "Théorie des Graphes"),
    # --- New: Computer Vision ---
    ("sk22", "Traitement d'Images"),
    ("sk23", "Vision par Ordinateur"),
    # --- New: Advanced AI ---
    ("sk24", "Apprentissage par Renforcement"),
    ("sk25", "Séries Temporelles & Prévision"),
    # --- New: Data Infrastructure ---
    ("sk26", "Bases de Données NoSQL"),
    ("sk27", "Big Data & Spark"),
    ("sk28", "Conteneurisation & DevOps"),
    ("sk29", "Architecture Microservices"),
    ("sk30", "ETL & Web Scraping"),
    # --- New: Applied & Specialized ---
    ("sk31", "Visualisation de Données"),
    ("sk32", "Fouille de Texte Avancée"),
    ("sk33", "Cybersécurité Avancée"),
    ("sk34", "Blockchain & Systèmes Décentralisés"),
    ("sk35", "Génie Logiciel & Agilité"),
]

# (id, name, difficulty, credits, [required_skill_ids], [taught_skill_ids])
MODULES = [
    # ── Difficulty 1 — Introductory ───────────────────────────────────────
    ("m01", "Introduction à Python",            1, 3, [],                             ["sk01"]),
    ("m02", "Mathématiques Fondamentales",       1, 4, [],                             ["sk02"]),
    ("m03", "Algorithmique et Structures",       1, 4, ["sk01"],                       ["sk06"]),
    ("m04", "Bases de Données Relationnelles",   1, 3, ["sk01"],                       ["sk05"]),
    ("m05", "Programmation R pour la Data Sci.", 1, 3, [],                             ["sk16"]),
    ("m06", "C/C++ & Programmation Système",     1, 4, ["sk06"],                       ["sk18"]),
    # ── Difficulty 2 — Intermediate ───────────────────────────────────────
    ("m07", "Algèbre Linéaire Appliquée",        2, 3, ["sk02"],                       ["sk03"]),
    ("m08", "Probabilités et Statistiques",      2, 3, ["sk02"],                       ["sk04"]),
    ("m09", "Réseaux Informatiques",             2, 3, ["sk06"],                       ["sk12"]),
    ("m10", "Introduction au Machine Learning",  2, 4, ["sk01", "sk03", "sk04"],       ["sk07"]),
    ("m11", "Java Avancé & Patterns",            2, 3, ["sk01"],                       ["sk11"]),
    ("m12", "Sécurité des Systèmes",             2, 3, ["sk12"],                       ["sk13"]),
    ("m13", "Théorie des Graphes",               2, 3, ["sk02", "sk06"],               ["sk21"]),
    ("m14", "Bases de Données NoSQL",            2, 3, ["sk05"],                       ["sk26"]),
    ("m15", "Visualisation de Données",          2, 2, ["sk01", "sk04"],               ["sk31"]),
    ("m16", "Développement d'APIs REST",         2, 3, ["sk01", "sk11"],               ["sk29"]),
    ("m17", "ETL & Web Scraping",                2, 3, ["sk01", "sk05"],               ["sk30"]),
    ("m18", "Scala & Prog. Fonctionnelle",       2, 3, ["sk01", "sk11"],               ["sk17"]),
    ("m19", "Génie Logiciel & Méthodes Agiles",  2, 3, ["sk06", "sk11"],               ["sk35"]),
    ("m20", "Traitement d'Images",               2, 3, ["sk07", "sk03"],               ["sk22"]),
    # ── Difficulty 3 — Advanced ───────────────────────────────────────────
    ("m21", "Deep Learning avec PyTorch",        3, 4, ["sk07", "sk03"],               ["sk08"]),
    ("m22", "Traitement du Langage Naturel",     3, 4, ["sk08"],                       ["sk09"]),
    ("m23", "Systèmes Distribués",               3, 3, ["sk05", "sk12"],               ["sk10"]),
    ("m24", "Data Engineering & Pipelines",      3, 4, ["sk05", "sk01"],               ["sk14"]),
    ("m25", "Cloud & MLOps",                     3, 3, ["sk14", "sk07"],               ["sk15"]),
    ("m26", "Statistiques Bayésiennes",          3, 4, ["sk04", "sk02"],               ["sk19"]),
    ("m27", "Optimisation Mathématique",         3, 4, ["sk03", "sk02"],               ["sk20"]),
    ("m28", "Big Data avec Spark",               3, 4, ["sk10", "sk26"],               ["sk27"]),
    ("m29", "Vision par Ordinateur",             3, 4, ["sk08", "sk22"],               ["sk23"]),
    ("m30", "Séries Temporelles & Prévision",    3, 4, ["sk04", "sk01"],               ["sk25"]),
    ("m31", "Apprentissage par Renforcement",    3, 4, ["sk07", "sk03"],               ["sk24"]),
    ("m32", "Fouille de Texte Avancée",          3, 4, ["sk09", "sk04"],               ["sk32"]),
    ("m33", "Conteneurisation & DevOps",         3, 3, ["sk15", "sk10"],               ["sk28"]),
    ("m34", "Cybersécurité Avancée & Pentest",   3, 4, ["sk13", "sk12"],               ["sk33"]),
    ("m35", "Blockchain & Systèmes Décent.",     3, 4, ["sk13", "sk10"],               ["sk34"]),
]

# (prereq_module_id, module_id)
PREREQUISITES = [
    # Foundations → Intermediate
    ("m01", "m03"), ("m01", "m04"), ("m01", "m10"), ("m01", "m11"),
    ("m01", "m15"), ("m01", "m17"),
    ("m02", "m07"), ("m02", "m08"),
    ("m03", "m06"), ("m03", "m09"), ("m03", "m13"),
    ("m04", "m14"), ("m04", "m17"), ("m04", "m23"),
    ("m05", "m15"),
    ("m11", "m16"), ("m11", "m18"), ("m11", "m19"),
    # Intermediate → Advanced ML track
    ("m07", "m10"), ("m08", "m10"),
    ("m07", "m20"), ("m10", "m20"),
    ("m10", "m21"), ("m10", "m31"),
    ("m07", "m21"),
    ("m21", "m22"), ("m21", "m29"),
    ("m20", "m29"),
    ("m22", "m32"),
    ("m08", "m26"), ("m08", "m30"),
    ("m07", "m27"), ("m07", "m25"),
    ("m10", "m25"),
    # Data & infrastructure track
    ("m04", "m24"), ("m01", "m24"),
    ("m24", "m25"),
    ("m09", "m23"), ("m23", "m28"),
    ("m14", "m28"),
    ("m15", "m25"),                 # R → Visualisation before MLOps
    ("m25", "m33"),
    ("m23", "m33"), ("m23", "m35"),
    # Security track
    ("m09", "m12"), ("m12", "m34"), ("m12", "m35"),
    # Functional / JVM track
    ("m11", "m18"),
    ("m23", "m28"),
]

NUM_STUDENTS = 100


def populate_graph(engine) -> None:
    """
    Fill *engine* (a GraphEngine instance) with:
    • skills
    • modules (with skill links & prerequisites)
    • synthetic students with completed modules & mastered skills
    """
    log.info("Populating knowledge graph …")

    # 1. Skills
    for sid, sname in SKILLS:
        engine.add_skill(sid, sname)

    # 2. Modules
    for mid, mname, diff, cred, req_skills, taught_skills in MODULES:
        engine.add_module(mid, mname, diff, cred)
        for rsid in req_skills:
            engine.link_module_requires_skill(mid, rsid)
        for tsid in taught_skills:
            engine.link_module_teaches_skill(mid, tsid)

    # 3. Prerequisites
    for pre, post in PREREQUISITES:
        engine.link_prerequisite(pre, post)

    # 4. Synthetic students
    skill_ids    = [s[0] for s in SKILLS]
    module_ids   = [m[0] for m in MODULES]

    for i in range(1, NUM_STUDENTS + 1):
        student_id = f"STU{i:03d}"
        name       = fake.name()
        year       = random.randint(2020, 2024)
        engine.add_student(student_id, name, year)

        # Each student completes 2-6 random modules
        n_completed = random.randint(2, 6)
        completed   = random.sample(module_ids, n_completed)
        for mid in completed:
            engine.link_student_module_completed(student_id, mid, grade=round(random.uniform(8, 20), 1))

        # Mastered skills = taught_skills of completed modules + 0-2 random skills
        mastered: set[str] = set()
        m_lookup = {m[0]: m[5] for m in MODULES}  # mid -> taught_skills
        for mid in completed:
            mastered.update(m_lookup.get(mid, []))
        extra = random.sample(skill_ids, random.randint(0, 2))
        mastered.update(extra)

        for skid in mastered:
            engine.link_student_skill(student_id, skid)

    # 5. OWL-RL closure
    engine.finalize()
    log.info(
        "Graph populated: %d triples total",
        engine.triple_count,
    )