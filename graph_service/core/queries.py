NS = "http://ensias.ma/academic#"

PREFIXES = """
    PREFIX academic: <http://ensias.ma/academic#>
    PREFIX rdf:      <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX rdfs:     <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX xsd:      <http://www.w3.org/2001/XMLSchema#>
"""

# ─────────────────────────────────────────────
# Query 1 – Modules whose prerequisites are all
#           satisfied by the student's mastered skills
# ─────────────────────────────────────────────
GET_RECOMMENDATIONS = PREFIXES + """
SELECT DISTINCT ?module ?moduleName ?difficultyLevel ?credits
WHERE {
    # All modules in the graph
    ?module rdf:type academic:Module .
    ?module academic:moduleName ?moduleName .
    OPTIONAL { ?module academic:difficultyLevel ?difficultyLevel . }
    OPTIONAL { ?module academic:credits ?credits . }

    # The student has NOT already completed this module
    FILTER NOT EXISTS {
        ?student academic:studentId ?sid .
        FILTER(?sid = ?studentId)
        ?student academic:hasCompletedModule ?module .
    }

    # Every required skill for this module must be mastered by the student
    FILTER NOT EXISTS {
        ?module academic:requiresSkill ?reqSkill .
        FILTER NOT EXISTS {
            ?student academic:studentId ?sid2 .
            FILTER(?sid2 = ?studentId)
            ?student academic:hasMasteredSkill ?reqSkill .
        }
    }
}
ORDER BY ?difficultyLevel
"""

# ─────────────────────────────────────────────
# Query 2 – Full student profile
# ─────────────────────────────────────────────
GET_STUDENT_PROFILE = PREFIXES + """
SELECT DISTINCT ?studentName ?enrollmentYear ?skill ?skillName ?completedModule ?moduleName
WHERE {
    ?student rdf:type academic:Student .
    ?student academic:studentId ?sid .
    FILTER(?sid = ?studentId)
    OPTIONAL { ?student academic:studentName  ?studentName . }
    OPTIONAL { ?student academic:enrollmentYear ?enrollmentYear . }
    OPTIONAL {
        ?student academic:hasMasteredSkill ?skill .
        OPTIONAL { ?skill academic:skillName ?skillName . }
    }
    OPTIONAL {
        ?student academic:hasCompletedModule ?completedModule .
        OPTIONAL { ?completedModule academic:moduleName ?moduleName . }
    }
}
"""

# ─────────────────────────────────────────────
# Query 3 – All modules with full metadata
# ─────────────────────────────────────────────
GET_ALL_MODULES = PREFIXES + """
SELECT DISTINCT ?module ?moduleId ?moduleName ?difficultyLevel ?credits
WHERE {
    ?module rdf:type academic:Module .
    OPTIONAL { ?module academic:moduleId       ?moduleId . }
    OPTIONAL { ?module academic:moduleName     ?moduleName . }
    OPTIONAL { ?module academic:difficultyLevel ?difficultyLevel . }
    OPTIONAL { ?module academic:credits        ?credits . }
}
ORDER BY ?difficultyLevel ?moduleName
"""

# ─────────────────────────────────────────────
# Query 4 – Prerequisites chain for a module
# ─────────────────────────────────────────────
GET_MODULE_PREREQUISITES = PREFIXES + """
SELECT DISTINCT ?prereqModule ?prereqName ?prereqDifficulty
WHERE {
    ?targetModule rdf:type academic:Module .
    ?targetModule academic:moduleId ?mid .
    FILTER(?mid = ?moduleId)

    ?prereqModule academic:isPrerequisiteOf ?targetModule .
    OPTIONAL { ?prereqModule academic:moduleName      ?prereqName . }
    OPTIONAL { ?prereqModule academic:difficultyLevel ?prereqDifficulty . }
}
ORDER BY ?prereqDifficulty
"""

# ─────────────────────────────────────────────
# Query 5 – Modules that teach a given skill
# ─────────────────────────────────────────────
GET_MODULES_BY_SKILL = PREFIXES + """
SELECT DISTINCT ?module ?moduleName ?difficultyLevel
WHERE {
    ?skill rdf:type academic:Skill .
    ?skill academic:skillName ?sname .
    FILTER(LCASE(?sname) = LCASE(?skillName))
    ?module academic:teachesSkill ?skill .
    OPTIONAL { ?module academic:moduleName     ?moduleName . }
    OPTIONAL { ?module academic:difficultyLevel ?difficultyLevel . }
}
ORDER BY ?difficultyLevel
"""

# ─────────────────────────────────────────────
# Query 6 – All students (for admin / ML loader)
# ─────────────────────────────────────────────
GET_ALL_STUDENTS = PREFIXES + """
SELECT DISTINCT ?student ?studentId ?studentName ?enrollmentYear
WHERE {
    ?student rdf:type academic:Student .
    OPTIONAL { ?student academic:studentId     ?studentId . }
    OPTIONAL { ?student academic:studentName   ?studentName . }
    OPTIONAL { ?student academic:enrollmentYear ?enrollmentYear . }
}
ORDER BY ?studentId
"""