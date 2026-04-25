GET_RECOMMENDATIONS_SPARQL = """
PREFIX ac: <http://ensias.ma/academic#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

SELECT ?module ?moduleName WHERE {
    ?module rdf:type ac:Module .
    ?module ac:hasName ?moduleName .
    
    # Vérifier que l'étudiant ne suit pas déjà ce module
    FILTER NOT EXISTS { 
        <http://ensias.ma/academic#student_{student_id}> ac:enrolledIn ?module 
    }
    
    # Logique de filtrage par prérequis (Simplifiée pour le début)
    OPTIONAL { ?module ac:hasPrerequisite ?pre . }
}
LIMIT 10
"""