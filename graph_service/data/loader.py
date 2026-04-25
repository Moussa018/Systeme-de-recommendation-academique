from __future__ import annotations

import random
import logging
from faker import Faker

log = logging.getLogger(__name__)
fake = Faker("fr_FR")
random.seed(42)


# ── Static curriculum ──────────────────────────────────────────────────────

SKILLS = [
    ("sk01", "Python"),
    ("sk02", "Mathématiques"),
    ("sk03", "Algèbre Linéaire"),
    ("sk04", "Probabilités & Statistiques"),
    ("sk05", "Bases de Données"),
    ("sk06", "Algorithmique"),
    ("sk07", "Machine Learning"),
    ("sk08", "Deep Learning"),
    ("sk09", "Traitement du Langage Naturel"),
    ("sk10", "Systèmes Distribués"),
    ("sk11", "Java"),
    ("sk12", "Réseaux"),
    ("sk13", "Sécurité Informatique"),
    ("sk14", "Data Engineering"),
    ("sk15", "Cloud Computing"),
]

# (id, name, difficulty, credits, [required_skill_ids], [taught_skill_ids])
MODULES = [
    ("m01", "Introduction à Python",           1, 3, [],                        ["sk01"]),
    ("m02", "Mathématiques Fondamentales",      1, 4, [],                        ["sk02"]),
    ("m03", "Algorithmique et Structures",      1, 4, ["sk01"],                  ["sk06"]),
    ("m04", "Bases de Données Relationnelles",  1, 3, ["sk01"],                  ["sk05"]),
    ("m05", "Algèbre Linéaire Appliquée",       2, 3, ["sk02"],                  ["sk03"]),
    ("m06", "Probabilités et Statistiques",     2, 3, ["sk02"],                  ["sk04"]),
    ("m07", "Réseaux Informatiques",            2, 3, ["sk06"],                  ["sk12"]),
    ("m08", "Introduction au Machine Learning", 2, 4, ["sk01", "sk03", "sk04"],  ["sk07"]),
    ("m09", "Java Avancé & Patterns",           2, 3, ["sk01"],                  ["sk11"]),
    ("m10", "Sécurité des Systèmes",            2, 3, ["sk12"],                  ["sk13"]),
    ("m11", "Deep Learning avec PyTorch",       3, 4, ["sk07", "sk03"],          ["sk08"]),
    ("m12", "Traitement du Langage Naturel",    3, 4, ["sk08"],                  ["sk09"]),
    ("m13", "Systèmes Distribués",              3, 3, ["sk05", "sk12"],          ["sk10"]),
    ("m14", "Data Engineering & Pipelines",     3, 4, ["sk05", "sk01"],          ["sk14"]),
    ("m15", "Cloud & MLOps",                    3, 3, ["sk14", "sk07"],          ["sk15"]),
]

# (prereq_module_id, module_id)
PREREQUISITES = [
    ("m01", "m03"), ("m01", "m04"), ("m01", "m08"), ("m01", "m09"),
    ("m02", "m05"), ("m02", "m06"),
    ("m03", "m07"),
    ("m05", "m08"),
    ("m06", "m08"),
    ("m07", "m10"), ("m07", "m13"),
    ("m08", "m11"), ("m08", "m15"),
    ("m11", "m12"),
    ("m04", "m13"), ("m04", "m14"),
    ("m14", "m15"),
]

NUM_STUDENTS = 50


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