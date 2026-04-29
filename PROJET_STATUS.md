# Système de Recommandation Académique Hybride — État du Projet

> Document de travail — basé sur le Rapport de Conception et le code produit dans `graph_service`.

---

## Vue d'ensemble du projet

Le projet vise à construire un système de recommandation hybride pour les étudiants de l'ENSIAS, combinant deux axes :

- **Axe sémantique** : un Knowledge Graph RDF/OWL interrogé via SPARQL, capable de raisonner sur les prérequis et les compétences.
- **Axe prédictif** : un moteur de Machine Learning (SVD baseline + Neural Collaborative Filtering) qui découvre des patterns comportementaux cachés.

Le score final est une combinaison pondérée dynamique :

```
Score_Final = α × Score_Graphe + β × Score_ML
```

où α et β s'adaptent selon la maturité du profil étudiant — α domine pour les nouveaux utilisateurs (cold start), β monte graduellement quand l'historique est suffisant.

L'architecture cible est microservices : **Graph Service** / **ML Service** / **Fusion Service** / **API REST**.

---

## Plan en 7 étapes (extrait du rapport)

| # | Étape | Statut |
|---|-------|--------|
| 1 | Collecte & Préparation des données | **Fait** |
| 2 | Modélisation Ontologique (OWL) | **Fait** |
| 3 | Implémentation du Knowledge Graph (rdflib + SPARQL) | **Fait** |
| 4 | Développement ML — SVD baseline | Non démarré |
| 5 | Moteurs de recommandation ML (NCF) + Fusion | Non démarré |
| 6 | Évaluation & Comparaison (Precision, Recall, RMSE, NDCG) | Non démarré |
| 7 | Déploiement API (FastAPI microservices) | **Partiel** (Graph Service opérationnel) |

---

## Étape 1 — Collecte & Préparation des données

### Ce qui a été fait

Le curriculum ENSIAS a été modélisé manuellement sous forme de données structurées statiques, complétées par une génération synthétique de profils étudiants via `Faker`.

#### Compétences modélisées (35 skills)

| ID | Compétence | Groupe |
|----|-----------|--------|
| sk01 | Python | Fondamentaux |
| sk02 | Mathématiques | Fondamentaux |
| sk03 | Algèbre Linéaire | Fondamentaux |
| sk04 | Probabilités & Statistiques | Fondamentaux |
| sk05 | Bases de Données Relationnelles | Fondamentaux |
| sk06 | Algorithmique | Fondamentaux |
| sk07 | Machine Learning | ML / IA classique |
| sk08 | Deep Learning | ML / IA classique |
| sk09 | Traitement du Langage Naturel | ML / IA classique |
| sk10 | Systèmes Distribués | ML / IA classique |
| sk11 | Java | Langages |
| sk12 | Réseaux Informatiques | Langages |
| sk13 | Sécurité Informatique | Langages |
| sk14 | Data Engineering | Data & Cloud |
| sk15 | Cloud Computing | Data & Cloud |
| sk16 | Programmation R | Langages |
| sk17 | Scala & Programmation Fonctionnelle | Langages |
| sk18 | C/C++ & Programmation Système | Langages |
| sk19 | Statistiques Bayésiennes | Mathématiques avancées |
| sk20 | Optimisation Mathématique | Mathématiques avancées |
| sk21 | Théorie des Graphes | Mathématiques avancées |
| sk22 | Traitement d'Images | Vision par ordinateur |
| sk23 | Vision par Ordinateur | Vision par ordinateur |
| sk24 | Apprentissage par Renforcement | IA avancée |
| sk25 | Séries Temporelles & Prévision | IA avancée |
| sk26 | Bases de Données NoSQL | Infrastructure data |
| sk27 | Big Data & Spark | Infrastructure data |
| sk28 | Conteneurisation & DevOps | Infrastructure data |
| sk29 | Architecture Microservices | Infrastructure data |
| sk30 | ETL & Web Scraping | Infrastructure data |
| sk31 | Visualisation de Données | Appliqué & Spécialisé |
| sk32 | Fouille de Texte Avancée | Appliqué & Spécialisé |
| sk33 | Cybersécurité Avancée | Appliqué & Spécialisé |
| sk34 | Blockchain & Systèmes Décentralisés | Appliqué & Spécialisé |
| sk35 | Génie Logiciel & Agilité | Appliqué & Spécialisé |

#### Modules du curriculum (35 modules, 3 niveaux de difficulté)

**Difficulté 1 — Introductoire**

| ID | Module | ECTS | Prérequis (skills) | Enseigne |
|----|--------|------|-------------------|----------|
| m01 | Introduction à Python | 3 | — | sk01 |
| m02 | Mathématiques Fondamentales | 4 | — | sk02 |
| m03 | Algorithmique et Structures | 4 | sk01 | sk06 |
| m04 | Bases de Données Relationnelles | 3 | sk01 | sk05 |
| m05 | Programmation R pour la Data Science | 3 | — | sk16 |
| m06 | C/C++ & Programmation Système | 4 | sk06 | sk18 |

**Difficulté 2 — Intermédiaire**

| ID | Module | ECTS | Prérequis (skills) | Enseigne |
|----|--------|------|-------------------|----------|
| m07 | Algèbre Linéaire Appliquée | 3 | sk02 | sk03 |
| m08 | Probabilités et Statistiques | 3 | sk02 | sk04 |
| m09 | Réseaux Informatiques | 3 | sk06 | sk12 |
| m10 | Introduction au Machine Learning | 4 | sk01, sk03, sk04 | sk07 |
| m11 | Java Avancé & Patterns | 3 | sk01 | sk11 |
| m12 | Sécurité des Systèmes | 3 | sk12 | sk13 |
| m13 | Théorie des Graphes | 3 | sk02, sk06 | sk21 |
| m14 | Bases de Données NoSQL | 3 | sk05 | sk26 |
| m15 | Visualisation de Données | 2 | sk01, sk04 | sk31 |
| m16 | Développement d'APIs REST | 3 | sk01, sk11 | sk29 |
| m17 | ETL & Web Scraping | 3 | sk01, sk05 | sk30 |
| m18 | Scala & Prog. Fonctionnelle | 3 | sk01, sk11 | sk17 |
| m19 | Génie Logiciel & Méthodes Agiles | 3 | sk06, sk11 | sk35 |
| m20 | Traitement d'Images | 3 | sk07, sk03 | sk22 |

**Difficulté 3 — Avancé**

| ID | Module | ECTS | Prérequis (skills) | Enseigne |
|----|--------|------|-------------------|----------|
| m21 | Deep Learning avec PyTorch | 4 | sk07, sk03 | sk08 |
| m22 | Traitement du Langage Naturel | 4 | sk08 | sk09 |
| m23 | Systèmes Distribués | 3 | sk05, sk12 | sk10 |
| m24 | Data Engineering & Pipelines | 4 | sk05, sk01 | sk14 |
| m25 | Cloud & MLOps | 3 | sk14, sk07 | sk15 |
| m26 | Statistiques Bayésiennes | 4 | sk04, sk02 | sk19 |
| m27 | Optimisation Mathématique | 4 | sk03, sk02 | sk20 |
| m28 | Big Data avec Spark | 4 | sk10, sk26 | sk27 |
| m29 | Vision par Ordinateur | 4 | sk08, sk22 | sk23 |
| m30 | Séries Temporelles & Prévision | 4 | sk04, sk01 | sk25 |
| m31 | Apprentissage par Renforcement | 4 | sk07, sk03 | sk24 |
| m32 | Fouille de Texte Avancée | 4 | sk09, sk04 | sk32 |
| m33 | Conteneurisation & DevOps | 3 | sk15, sk10 | sk28 |
| m34 | Cybersécurité Avancée & Pentest | 4 | sk13, sk12 | sk33 |
| m35 | Blockchain & Systèmes Décentralisés | 4 | sk13, sk10 | sk34 |

#### Graphe de prérequis entre modules (plus de 40 relations)

```
── Track fondamental ──────────────────────────────────
m01 ──► m03, m04, m10, m11, m15, m17, m24
m02 ──► m07, m08
m03 ──► m06, m09, m13
m04 ──► m14, m17, m23, m24

── Track ML / IA ──────────────────────────────────────
m07 ──► m10
m08 ──► m10, m26, m30
m10 ──► m20, m21, m25, m31
m07 ──► m20, m21, m25, m27
m20 ──► m29
m21 ──► m22, m29
m22 ──► m32

── Track Vision & NLP ─────────────────────────────────
m20 ──► m29   (Images → Vision par Ordinateur)
m21 ──► m29   (Deep Learning → Vision)
m22 ──► m32   (NLP → Fouille de Texte Avancée)

── Track Data & Infrastructure ────────────────────────
m09 ──► m23
m23 ──► m28, m33, m35
m14 ──► m28
m24 ──► m25
m25 ──► m33
m05 ──► m15   (R → Visualisation)

── Track Sécurité / JVM / Blockchain ──────────────────
m09 ──► m12
m12 ──► m34, m35
m11 ──► m16, m18, m19
```

Cela forme un DAG cohérent avec plusieurs chemins longs. Par exemple, pour atteindre `m29 (Vision par Ordinateur)`, un étudiant doit avoir traversé : Python → ML → Traitement d'Images ET Deep Learning. Pour `m28 (Big Data)` : Bases de Données → NoSQL ET Systèmes Distribués.

#### Étudiants synthétiques (100 profils)

Générés avec `Faker(fr_FR)` et `random.seed(42)` pour la reproductibilité :
- Chaque étudiant a un nom francophone aléatoire, une année d'inscription entre 2020 et 2024.
- Il complète entre 2 et 6 modules tirés aléatoirement.
- Ses compétences maîtrisées = union des skills enseignés par ses modules complétés + 0 à 2 skills bonus aléatoires.
- Les grades sont dans [8, 20] (système marocain sur 20).

### Ce qui est présentable

- Un curriculum académique réaliste structuré en DAG avec 15 modules, 15 compétences et 17 relations de prérequis.
- Un pipeline de génération de données synthétiques reproductible (`seed=42`), prêt à alimenter le ML.
- Les données sont directement injectées dans le Knowledge Graph, pas stockées à plat — c'est déjà intégré à l'architecture.

---

## Étape 2 — Modélisation Ontologique

### Ce qui a été fait

Une ontologie OWL formelle a été définie dans `core/ontology.owl` (namespace : `http://ensias.ma/academic#`).

#### Classes

| Classe | Description |
|--------|-------------|
| `academic:Student` | Un étudiant inscrit à l'ENSIAS |
| `academic:Module` | Un cours ou module du curriculum |
| `academic:Skill` | Une compétence technique ou académique |

#### Propriétés d'objets (Object Properties)

| Propriété | Domaine → Portée | Sémantique |
|-----------|-----------------|------------|
| `hasMasteredSkill` | Student → Skill | L'étudiant maîtrise cette compétence |
| `hasCompletedModule` | Student → Module | L'étudiant a suivi et validé ce module |
| `requiresSkill` | Module → Skill | Le module exige cette compétence en entrée |
| `teachesSkill` | Module → Skill | Le module enseigne et confère cette compétence |
| `isPrerequisiteOf` | Module → Module | Ce module doit être validé avant l'autre |

#### Propriétés de données (Datatype Properties)

| Propriété | Domaine | Type XSD |
|-----------|---------|----------|
| `studentId` | Student | xsd:string |
| `studentName` | Student | xsd:string |
| `enrollmentYear` | Student | xsd:integer |
| `moduleId` | Module | xsd:string |
| `moduleName` | Module | xsd:string |
| `difficultyLevel` | Module | xsd:integer |
| `credits` | Module | xsd:integer |
| `skillName` | Skill | xsd:string |

### Pourquoi cette ontologie est significative

L'ontologie capture les relations sémantiques fondamentales d'un parcours académique dans un formalisme standard (OWL/RDF), ce qui permet :

1. **Raisonnement automatique** : via OWL-RL (bibliothèque `owlrl`), le moteur peut inférer des relations non explicitement encodées.
2. **Interopérabilité** : le format OWL est un standard W3C, les données peuvent être interrogées par n'importe quel triplestore SPARQL.
3. **Explicabilité** : contrairement à un modèle ML boîte noire, une recommandation issue du graphe peut être justifiée formellement ("ce module est recommandé car l'étudiant maîtrise toutes les compétences requises").

### Ce qui est présentable

- Un diagramme OWL avec 3 classes, 5 object properties et 8 datatype properties.
- La propriété `isPrerequisiteOf` encode explicitement le DAG de progression académique.
- Le lien `requiresSkill` / `teachesSkill` crée un pont sémantique entre le savoir d'un étudiant et les portes d'entrée des modules.
- L'ontologie est chargée au démarrage du service et enrichie par OWL-RL reasoning avant les premières requêtes.

---

## graph_service — Analyse détaillée

### Description générale

`graph_service` est un **microservice FastAPI complet et fonctionnel** qui implémente les étapes 1, 2 et 3 du plan de conception, ainsi que la couche API (étape 7, partielle). Ce n'est **pas un squelette** : le service démarre, raisonne et répond à des requêtes réelles.

### Architecture interne

```
graph_service/
├── main.py              # FastAPI app + 6 endpoints REST
├── requirements.txt     # dépendances Python
├── core/
│   ├── ontology.owl     # Ontologie OWL/RDF formelle
│   ├── engine.py        # GraphEngine — cœur du service
│   └── queries.py       # 6 requêtes SPARQL nommées
├── data/
│   └── loader.py        # Curriculum + génération étudiants synthétiques
└── test/
    └── test_graph.py    # Suite pytest (7 tests)
```

### GraphEngine (core/engine.py)

C'est le composant central. Son cycle de vie au démarrage :

1. Charge l'ontologie OWL depuis le disque (`ontology.owl`).
2. Reçoit les données du loader (`populate_graph`).
3. Applique la **fermeture déductive OWL-RL** (`owlrl.DeductiveClosure`) — le graphe s'enrichit de triples inférés.
4. Répond aux requêtes SPARQL via `rdflib`.

Méthodes de population du graphe :
- `add_student`, `add_module`, `add_skill`
- `link_student_skill`, `link_student_module_completed`
- `link_module_requires_skill`, `link_module_teaches_skill`
- `link_prerequisite`

Méthodes de requête :
- `get_recommendations(student_id)` — modules accessibles selon les skills maîtrisés
- `get_student_profile(student_id)` — profil complet (skills + modules complétés)
- `get_all_modules()` — catalogue avec métadonnées
- `get_module_prerequisites(module_id)` — chaîne de prérequis
- `get_modules_by_skill(skill_name)` — modules enseignant un skill donné
- `get_all_students()` — liste admin

### Logique de recommandation (SPARQL)

La requête de recommandation est sémantiquement correcte et non triviale. Elle filtre :

1. Les modules déjà complétés par l'étudiant (`FILTER NOT EXISTS { hasCompletedModule }`).
2. Les modules dont au moins un skill requis n'est **pas** maîtrisé (`FILTER NOT EXISTS { requiresSkill ... FILTER NOT EXISTS { hasMasteredSkill } }`).

Résultat : uniquement les modules dont **tous** les prérequis sont satisfaits et qui n'ont pas encore été validés. Les résultats sont triés par niveau de difficulté croissant.

Le `score` est actuellement fixé à `1.0` — tous les modules éligibles sont équivalents du point de vue du graphe. C'est le bon comportement : la pondération fine est réservée à la couche de fusion qui n'est pas encore construite.

### Endpoints REST disponibles

| Méthode | Route | Description |
|---------|-------|-------------|
| GET | `/health` | Statut du service + nombre de triples |
| GET | `/recommend/{student_id}` | Recommandations pour un étudiant |
| GET | `/student/{student_id}/profile` | Profil complet (skills + modules) |
| GET | `/modules` | Catalogue des modules |
| GET | `/modules/{module_id}/prerequisites` | Prérequis d'un module |
| GET | `/students` | Liste de tous les étudiants |
| GET | `/skills/{skill_name}/modules` | Modules enseignant un skill |

### Suite de tests (test/test_graph.py)

7 tests pytest couvrant :
- Vérification du nombre de triples après chargement (> 100)
- 15 modules chargés, 50 étudiants chargés
- Profil d'un étudiant existant et d'un inconnu
- Structure des résultats de recommandation
- Les modules recommandés ne sont pas déjà complétés (test d'intégrité sémantique)
- Deep Learning a bien des prérequis, Intro Python n'en a pas

### Évaluation : squelette ou implémentation réelle ?

**Implémentation réelle.** Le service est:

- **Démarrable** : `uvicorn main:app` fonctionne dès que les dépendances sont installées.
- **Correct sémantiquement** : la logique de recommandation respecte le contrat défini dans le rapport (prérequis sémantiques via SPARQL).
- **Testé** : suite pytest fonctionnelle avec des assertions non triviales.
- **Structuré pour l'intégration** : les `score=1.0` et la source `"knowledge_graph"` dans les résultats sont des points d'extension explicites pour la couche de fusion.

Ce qui **manque** pour être complet selon le rapport :
- Le service ML (SVD / NCF) — étape 4 et 5.
- Le service de fusion dynamique (calcul de α et β selon le profil).
- La connexion à PostgreSQL pour les données persistantes (actuellement tout est en mémoire).
- Les métriques d'évaluation — étape 6.

---

## Ce qui reste à faire

| Composant | Description |
|-----------|-------------|
| `ml_service/` | SVD baseline avec `surprise`, puis NCF avec PyTorch |
| `fusion_service/` | Calcul `α × Score_Graphe + β × Score_ML` avec adaptation dynamique |
| PostgreSQL | Persistance des profils et des interactions |
| Évaluation | Precision@K, Recall@K, NDCG, RMSE sur un jeu de test hold-out |
| Déploiement | Docker Compose pour orchestrer les 3 microservices |
