# Step 7: System Architecture Design

## Overview

The Academic Recommendation System is built using a **hybrid microservices architecture** that combines Knowledge Graph reasoning with Machine Learning collaborative filtering. This document describes the system design, component responsibilities, and integration patterns.

---

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         FastAPI REST Layer                          │
│  (Health, Recommendations, Evaluation Endpoints)                    │
└────────────────────────┬────────────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  Graph       │  │  ML          │  │  Fusion      │
│  Service     │  │  Service     │  │  Service     │
│  (RDF/SPARQL)│  │  (SVD)       │  │  (Hybrid)    │
└──────────────┘  └──────────────┘  └──────────────┘
        │                │                │
        │                │                │
        ▼                ▼                ▼
┌──────────────────────────────────────────────────┐
│         Evaluation Service                       │
│  (Precision, Recall, F1, NDCG Metrics)          │
└──────────────────────────────────────────────────┘
        │
        ▼
┌──────────────────────────────────────────────────┐
│    Database Layer (SQLAlchemy ORM)               │
│  - Students, Modules, Competencies               │
│  - Interactions, Prerequisites                    │
│  - Module-Competency Links                       │
└──────────────────────────────────────────────────┘
        │
        ▼
  [SQLite or PostgreSQL]
```

---

## Core Components

### 1. Graph Service (Knowledge Graph)

**File**: `services/graph_service.py`

**Responsibility**: Content-based recommendations using semantic relationships.

**Key Features**:
- **RDF/OWL Ontology**: Defines academic entities (Student, Module, Competency, Instructor)
- **SPARQL Queries**: Intelligent semantic queries for module discovery
- **Semantic Scoring**: Rates recommendations based on:
  - Prerequisite completion (0.2 max points)
  - Competency alignment with student proficiency levels (0.3 max points)
  - Base score (0.5)
- **Idempotency Guard**: Prevents duplicate triple population on repeated calls

**Core Methods**:
- `create_ontology()`: Builds RDF/OWL structure
- `populate_graph(db)`: Converts database records to RDF triples
- `get_recommendations(student_id, limit, db)`: Returns SPARQL-based recommendations
- `_calculate_semantic_score(student_id, module_id, db)`: Scores based on prerequisites + competency alignment

**Advantages**:
- Transparent reasoning (can explain why)
- Handles cold-start (new students with only competency profiles)
- Captures prerequisite logic
- No data sparsity issues

**Limitations**:
- Cannot discover non-obvious patterns
- Requires well-structured domain ontology

---

### 2. ML Service (Collaborative Filtering)

**File**: `services/ml_service.py`

**Responsibility**: Pattern-based recommendations using student interaction history.

**Key Features**:
- **Matrix Factorization (SVD)**: Decomposes student-module interaction matrix
- **SVD Reconstruction**: Predicts missing ratings via `user_factors @ item_factors.T`
- **Latent Factors**: 10 implicit user and item factors (configurable)
- **Score Weighting**: Interaction score = `rating × 0.6 + completion_rate × 0.4`

**Core Methods**:
- `train(db)`: Fits SVD model on interaction matrix
- `_create_interaction_matrix(interactions)`: Builds sparse (students × modules) matrix
- `get_recommendations(student_id, limit, db)`: Returns top-K predicted high scores
- `predict_score(student_id, module_id, db)`: Estimates rating for any pair

**Advantages**:
- Discovers hidden patterns (e.g., "similar to you, users also liked X")
- Scales to large datasets
- Fast inference (matrix multiplication)
- Provides confidence-sortable scores

**Limitations**:
- Cold-start problem (new students, new modules)
- Requires sufficient interaction data
- Less interpretable ("why this module?")

---

### 3. Fusion Service (Hybrid)

**File**: `services/fusion_service.py`

**Responsibility**: Intelligently combines Graph and ML approaches.

**Key Features**:
- **Dynamic Weighting**: Adapts Graph-vs-ML balance based on student data maturity
  - **Cold start** (<5 interactions): 80% Graph, 20% ML
  - **Transition** (5-20 interactions): Linear interpolation
  - **Mature** (>20 interactions): 30% Graph, 70% ML
- **Confidence Scoring**: Combines method agreement into confidence metric
- **Flexible Mode**: Can use graph-only, ML-only, or hybrid

**Core Methods**:
- `get_recommendations(student_id, limit, use_graph, use_ml, db)`: Fuses both signals
- `_calculate_weights(student_id, db)`: Returns (alpha, beta) pair for dynamic weighting
- `_calculate_confidence(graph_score, ml_score, alpha, beta)`: Produces confidence 0-1

**Design Rationale**:
- Exploits strengths of each approach at the right time
- Graph dominates when historical data is sparse
- ML dominates when enough signal exists

---

### 4. Evaluation Service (Step 6)

**File**: `services/evaluation_service.py`

**Responsibility**: Quantitative comparison of recommendation quality.

**Key Features**:
- **Leave-One-Out Validation**: Holds out each student's last interaction as ground truth
- **Ranking Metrics**:
  - **Precision@K**: % of top-K that match held-out item
  - **Recall@K**: Same as precision (only 1 relevant item per student)
  - **F1@K**: Harmonic mean of precision and recall
  - **NDCG@K**: Discounted cumulative gain (position-aware ranking quality)
- **Rating Metrics** (ML only):
  - **RMSE**: Root mean squared error of predicted vs. actual ratings
  - **MAE**: Mean absolute error

**Core Methods**:
- `evaluate_approach(approach, db, top_k)`: Scores "graph", "ml", or "hybrid"
- `compare_approaches(db, top_k)`: Runs all three and declares winner
- `_compute_ndcg(ground_truth_id, recommended_ids, k)`: Computes position-aware metric
- `_generate_analysis(results, winner, top_k)`: Human-readable summary

**Example Output**:
```json
{
  "top_k": 5,
  "approaches": {
    "graph": {
      "precision_at_k": 0.40,
      "recall_at_k": 0.40,
      "f1_at_k": 0.40,
      "ndcg_at_k": 0.63,
      "n_evaluated": 10
    },
    "ml": {
      "precision_at_k": 0.50,
      "recall_at_k": 0.50,
      "f1_at_k": 0.50,
      "ndcg_at_k": 0.71,
      "rmse": 0.82,
      "mae": 0.60,
      "n_evaluated": 10
    },
    "hybrid": {
      "precision_at_k": 0.60,
      "recall_at_k": 0.60,
      "f1_at_k": 0.60,
      "ndcg_at_k": 0.80,
      "n_evaluated": 10
    }
  },
  "winner": "hybrid",
  "analysis": "..."
}
```

---

## Data Model

### Core Tables

```
┌──────────────┐
│ students     │  Student profiles
└──────────────┘
       │
       ├─→ [1:N] student_competencies → competencies
       ├─→ [1:N] interactions → modules
       └─→ [1:N] prerequisites (reverse lookup)
       
┌──────────────┐
│ modules      │  Academic courses
└──────────────┘
       │
       ├─→ [1:N] interactions → students
       ├─→ [1:N] module_competencies → competencies
       └─→ [1:N] prerequisites

┌──────────────┐
│ competencies │  Skills/knowledge areas
└──────────────┘
       │
       ├─→ [1:N] student_competencies
       └─→ [1:N] module_competencies

┌──────────────────────┐
│ module_competencies  │  Courses teach skills
└──────────────────────┘

┌──────────────┐
│ interactions │  Student-module history (ratings, completion)
└──────────────┘

┌──────────────┐
│ prerequisites│  Module dependencies
└──────────────┘
```

---

## Data Flow

### Recommendation Request

```
Client Request: GET /recommendations?student_id=1&limit=5
    │
    ▼
FastAPI Endpoint (main.py)
    │
    ├─→ Query Student from DB
    │
    ├─→ Fusion Service
    │    ├─→ Graph Service.get_recommendations()
    │    │    ├─→ populate_graph(db) [if needed]
    │    │    ├─→ SPARQL query on RDF triples
    │    │    └─→ Score via _calculate_semantic_score()
    │    │
    │    ├─→ ML Service.get_recommendations()
    │    │    ├─→ train(db) [if not yet trained]
    │    │    ├─→ Reconstruct: predicted = user_factors @ item_factors.T
    │    │    └─→ Top-K by predicted score
    │    │
    │    └─→ Fuse: final_score = α × graph_score + β × ml_score
    │
    ├─→ Return: List[RecommendationItem]
    │
    ▼
JSON Response to Client
```

### Evaluation Request

```
Client Request: GET /evaluate?top_k=5
    │
    ▼
FastAPI Endpoint (main.py)
    │
    ├─→ Evaluation Service.compare_approaches()
    │
    ├─→ For each approach in ["graph", "ml", "hybrid"]:
    │    ├─→ evaluate_approach(approach, db, top_k=5)
    │    │    ├─→ For each student with 2+ interactions:
    │    │    │    ├─→ Hold out last interaction
    │    │    │    ├─→ Get top-K recommendations
    │    │    │    ├─→ Compute: Precision@K, Recall@K, F1@K, NDCG@K
    │    │    │    └─→ Average across all students
    │    │    └─→ Return metrics dict
    │    │
    │    └─→ Store results
    │
    ├─→ Determine winner by highest F1@K
    ├─→ Generate analysis string
    │
    ▼
JSON Response with all three approach metrics + winner
```

---

## Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **API** | FastAPI, Uvicorn | REST endpoints, async handling |
| **Web Framework** | Pydantic | Request/response validation |
| **Database** | SQLAlchemy ORM | Database-agnostic models |
| **Database Engine** | SQLite (dev), PostgreSQL (prod) | Data persistence |
| **Knowledge Graph** | RDFLib, SPARQL | Semantic reasoning |
| **ML / Linear Algebra** | scikit-learn, NumPy | SVD matrix factorization |
| **Testing** | pytest | Unit + integration tests |
| **Deployment** | Docker, Docker Compose | Containerized microservices |

---

## Design Patterns

### 1. Service Layer Pattern
Each recommendation engine (Graph, ML, Fusion) is a standalone service with consistent interface:
- `get_recommendations(student_id: int, limit: int, db: Session) -> List[RecommendationItem]`

### 2. Dependency Injection
Services receive their dependencies (graph_service, ml_service) via constructor, not global state.

### 3. Idempotency Guard
Graph service caches ontology state; repeated calls don't rebuild RDF graph.

### 4. Leave-One-Out Validation
Evaluation service avoids data leakage by strictly separating training and test splits.

### 5. Dynamic Weighting
Fusion service adapts behavior based on student data maturity (cold-start heuristic).

---

## Scalability Considerations

### Horizontal Scaling
- **Graph Service**: Stateless; can run in parallel instances (minimal startup overhead)
- **ML Service**: Shared trained model (singleton); expensive to retrain; scale by caching model on disk/Redis
- **Fusion Service**: Stateless orchestrator; trivial to horizontally scale

### Vertical Scaling
- **SVD Training**: O(min(n_students, n_modules) × n_factors²) time and memory
  - Current: 15 students, 10 modules → milliseconds
  - 1M students, 10K modules → minutes (acceptable for offline training)
- **SPARQL Queries**: Depends on RDF graph size; currently ~100-200 triples (negligible)
- **Evaluation**: O(n_students × k × n_approaches); can be parallelized

### Optimization Strategies
1. **Cache ML Models**: Pickle trained SVD model; reload on next request (skip training if fresh)
2. **Cache SPARQL Results**: Store query results with TTL; invalidate on data changes
3. **Database Indexing**: Add indices on frequently queried fields (student_id, module_id, completion_rate)
4. **Batch Evaluation**: Evaluate off-hours; store results in cache layer

---

## Future Enhancements

| Feature | Priority | Effort | Impact |
|---------|----------|--------|--------|
| **Neural Collaborative Filtering** | High | Medium | Better accuracy than SVD |
| **Real-time Model Updates** | Medium | Medium | Fresher recommendations |
| **Recommendation Explanations** | High | Low | Better UX |
| **A/B Testing Framework** | Medium | High | Validate improvements |
| **PostgreSQL Migration** | Medium | Low | Production-ready |
| **Kubernetes Deployment** | Low | High | Cloud-ready |
| **Difficulty-based Filtering** | Low | Low | Personalized difficulty |
| **Learning Path Tracking** | Low | Medium | Longer-term goals |

---

## Deployment

### Local Development
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python data_generator.py
python main.py
# Visit http://localhost:8000/docs
```

### Docker
```bash
docker-compose up -d
curl http://localhost:8000/health
```

### Production Checklist
- [ ] Use PostgreSQL instead of SQLite
- [ ] Set environment variables for secrets
- [ ] Enable HTTPS (reverse proxy with nginx/Apache)
- [ ] Set up logging/monitoring (ELK, Datadog)
- [ ] Enable CORS selectively
- [ ] Rate limiting on evaluation endpoint
- [ ] Batch ML model training (cron job)
- [ ] Database backups

---

## Summary

This hybrid microservices architecture provides:
- **Transparency** (Knowledge Graph explains reasoning)
- **Pattern Discovery** (ML finds non-obvious links)
- **Robustness** (Fusion adapts to data maturity)
- **Scalability** (Stateless services, optional caching)
- **Testability** (Modular services with clear contracts)

The system successfully bridges symbolic reasoning (graphs) and statistical learning (SVD), demonstrating that the best recommendation systems combine **what things mean** (semantics) with **what users like** (patterns).
