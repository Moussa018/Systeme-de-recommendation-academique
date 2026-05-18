# Testing Guide - Steps 5-7 Implementation

This guide shows you how to test the complete implementation (Steps 5-7) to verify that the graph service is now working, ML predictions are fixed, and evaluation metrics are computed.

---

## Quick Start (5 minutes)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Reset database and regenerate with new module-competency links
rm -f academic_recommender.db ontology.rdf

# 3. Generate sample data (now includes module-competency mappings)
python data_generator.py

# 4. Run unit tests to verify implementation
pytest tests/ -v

# 5. Start the API server
python main.py

# 6. Test endpoints in another terminal (see below)
```

---

## Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

**Expected output**: No errors, all packages installed.

---

## Step 2: Reset Database

Before testing, clear the old database and ontology file:

```bash
# Remove old data
rm -f academic_recommender.db
rm -f ontology.rdf
```

---

## Step 3: Generate Sample Data

Run the data generator to create students, modules, competencies, and the NEW module-competency links:

```bash
python data_generator.py
```

**Expected output**:
```
INFO:__main__:Generating sample data...
INFO:__main__:Created 8 competencies
INFO:__main__:Created 10 modules
INFO:__main__:Created 7 prerequisites
INFO:__main__:Created 25 module-competency links
INFO:__main__:Created 15 students
INFO:__main__:Assigned competencies to students
INFO:__main__:Created 85 interactions
INFO:__main__:Sample data generation completed successfully!
```

**What to verify**:
- ✅ "Created 25 module-competency links" — NEW in Step 5
- ✅ "Created 85 interactions" — needed for ML training

---

## Step 4: Run Unit Tests

Run the test suite to verify all services work correctly:

```bash
pytest tests/ -v
```

**Expected output** (example with passing tests):
```
tests/test_services.py::TestGraphService::test_ontology_creation PASSED
tests/test_services.py::TestGraphService::test_graph_population PASSED
tests/test_services.py::TestGraphService::test_recommendations_no_data PASSED
tests/test_services.py::TestMLService::test_ml_service_initialization PASSED
tests/test_services.py::TestMLService::test_training_without_data PASSED
tests/test_services.py::TestMLService::test_recommendations_no_training PASSED
tests/test_services.py::TestFusionService::test_fusion_initialization PASSED
tests/test_services.py::TestFusionService::test_weight_calculation_cold_start PASSED
tests/test_services.py::TestFusionService::test_recommendations_generation PASSED
tests/test_services.py::TestInteractionMatrix::test_interaction_matrix_creation PASSED

tests/test_services.py::TestGraphWithData::test_module_competency_graph_population PASSED    ✨ NEW
tests/test_services.py::TestGraphWithData::test_graph_returns_results_with_data PASSED       ✨ NEW
tests/test_services.py::TestMLWithData::test_ml_training_with_data PASSED                   ✨ NEW
tests/test_services.py::TestMLWithData::test_ml_svd_reconstruction PASSED                   ✨ NEW
tests/test_services.py::TestMLWithData::test_ml_returns_recommendations PASSED              ✨ NEW
tests/test_services.py::TestMLWithData::test_predict_score PASSED                          ✨ NEW
tests/test_services.py::TestEvaluation::test_evaluation_compare_approaches PASSED           ✨ NEW (Step 6)
tests/test_services.py::TestEvaluation::test_evaluation_metrics_exist PASSED                ✨ NEW (Step 6)

======================== 18 passed in 2.34s ========================
```

**Key NEW tests to verify Step 5-7 implementation**:
- `test_module_competency_graph_population` — Verifies `ac:teaches` triples exist
- `test_ml_svd_reconstruction` — Verifies proper matrix shape
- `test_predict_score` — Verifies ML prediction works
- `test_evaluation_compare_approaches` — Verifies Step 6 evaluation works

---

## Step 5: Start the API Server

```bash
python main.py
```

**Expected output**:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:root:Initializing Academic Recommendation System...
INFO:services.graph_service:Ontology loaded from file
INFO:root:System initialized successfully
```

---

## Step 6: Test Endpoints

### 6a. Health Check

Verify the system is running:

```bash
curl http://localhost:8000/health
```

**Expected response**:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00.123456",
  "services": {
    "graph_service": "operational",
    "ml_service": "operational",
    "fusion_service": "operational"
  }
}
```

---

### 6b. Test Graph-Only Recommendations (STEP 5 - GRAPH FIX)

Before: Graph returned **0 results** (missing module-competency links)  
After: Graph returns **real recommendations**

```bash
curl "http://localhost:8000/recommendations/graph-only?student_id=1&limit=5"
```

**Expected response** (NOW FIXED):
```json
{
  "student_id": 1,
  "recommendations": [
    {
      "module_id": 3,
      "module_title": "Data Science Fundamentals",
      "score": 0.75,
      "confidence": 0.85,
      "reason": "Builds on your current skills",
      "graph_score": 0.75,
      "ml_score": null
    },
    {
      "module_id": 5,
      "module_title": "Web Development with FastAPI",
      "score": 0.68,
      "confidence": 0.85,
      "reason": "Builds on your current skills",
      "graph_score": 0.68,
      "ml_score": null
    }
  ],
  "timestamp": "2024-01-15T10:31:00.123456",
  "method": "knowledge_graph"
}
```

**What to verify**:
- ✅ `recommendations` is NOT empty (it was before!)
- ✅ Each recommendation has `module_id`, `module_title`, `score`, `confidence`
- ✅ `graph_score` is populated
- ✅ `reason` explains the recommendation

---

### 6c. Test ML-Only Recommendations (STEP 5 - ML FIX)

Before: ML used raw user similarity  
After: ML uses proper SVD matrix reconstruction

```bash
curl "http://localhost:8000/recommendations/ml-only?student_id=1&limit=5"
```

**Expected response**:
```json
{
  "student_id": 1,
  "recommendations": [
    {
      "module_id": 4,
      "module_title": "Machine Learning Basics",
      "score": 3.2,
      "confidence": 0.61,
      "reason": "Matches your learning profile",
      "graph_score": null,
      "ml_score": 3.2
    },
    {
      "module_id": 6,
      "module_title": "Database Design",
      "score": 2.8,
      "confidence": 0.53,
      "reason": "Matches your learning profile",
      "graph_score": null,
      "ml_score": 2.8
    }
  ],
  "timestamp": "2024-01-15T10:32:00.123456",
  "method": "machine_learning"
}
```

**What to verify**:
- ✅ Scores are in range 0-5 (predicted ratings)
- ✅ `ml_score` is populated
- ✅ Recommendations are different from graph-only (good sign - models disagree)

---

### 6d. Test Hybrid Recommendations (FUSION)

Combines Graph and ML with dynamic weighting:

```bash
curl "http://localhost:8000/recommendations?student_id=1&limit=5"
```

**Expected response**:
```json
{
  "student_id": 1,
  "recommendations": [
    {
      "module_id": 3,
      "module_title": "Data Science Fundamentals",
      "score": 0.72,
      "confidence": 0.87,
      "reason": "Builds on your current skills",
      "graph_score": 0.75,
      "ml_score": 0.68
    },
    {
      "module_id": 5,
      "module_title": "Web Development with FastAPI",
      "score": 0.65,
      "confidence": 0.82,
      "reason": "Builds on your current skills",
      "graph_score": 0.68,
      "ml_score": 0.61
    }
  ],
  "timestamp": "2024-01-15T10:33:00.123456",
  "method": "hybrid"
}
```

**What to verify**:
- ✅ Both `graph_score` and `ml_score` are populated
- ✅ Final `score` is somewhere between them (weighted average)
- ✅ `confidence` combines agreement between methods

---

### 6e. Test Evaluation Endpoint (STEP 6 - EVALUATION)

Compare all three approaches and get metrics:

```bash
curl "http://localhost:8000/evaluate?top_k=5"
```

**Expected response** (STEP 6 NEW ENDPOINT):
```json
{
  "status": "success",
  "timestamp": "2024-01-15T10:34:00.123456",
  "evaluation": {
    "top_k": 5,
    "approaches": {
      "graph": {
        "precision_at_k": 0.35,
        "recall_at_k": 0.35,
        "f1_at_k": 0.35,
        "ndcg_at_k": 0.55,
        "rmse": 0.0,
        "mae": 0.0,
        "n_evaluated": 10
      },
      "ml": {
        "precision_at_k": 0.45,
        "recall_at_k": 0.45,
        "f1_at_k": 0.45,
        "ndcg_at_k": 0.68,
        "rmse": 0.95,
        "mae": 0.72,
        "n_evaluated": 10
      },
      "hybrid": {
        "precision_at_k": 0.50,
        "recall_at_k": 0.50,
        "f1_at_k": 0.50,
        "ndcg_at_k": 0.75,
        "rmse": 0.0,
        "mae": 0.0,
        "n_evaluated": 10
      }
    },
    "winner": "hybrid",
    "analysis": "Evaluation at top-5 results: Hybrid approach (F1=0.50) outperforms Graph (F1=0.35) and ML (F1=0.45). The hybrid fusion strategy effectively combines the strengths of Knowledge Graph reasoning with collaborative filtering patterns."
  }
}
```

**What to verify** (STEP 6 - Evaluation Metrics):
- ✅ All three approaches have metrics
- ✅ `precision_at_k`, `recall_at_k`, `f1_at_k`, `ndcg_at_k` are computed
- ✅ ML has `rmse` and `mae` (rating prediction accuracy)
- ✅ `winner` is declared (should be "hybrid" due to dynamic weighting)
- ✅ `analysis` explains the results

**Understanding the metrics**:
- **Precision@5**: Of the top-5 recommended, how many were actually good (in student's actual interactions)?
- **Recall@5**: Same as precision here (only 1 "ground truth" item per student in evaluation)
- **F1@5**: Harmonic mean — balances precision and recall
- **NDCG@5**: Position-aware ranking quality (bonus if correct item is ranked high)
- **RMSE/MAE**: Rating prediction error (how close ML's predicted rating was to actual)

---

## Step 7: Verify Architecture Documentation

Check that the architecture document describes the system:

```bash
cat ARCHITECTURE.md | head -50
```

**Expected sections**:
- ✅ System Architecture Diagram (ASCII art)
- ✅ Core Components (Graph, ML, Fusion, Evaluation services)
- ✅ Data Model (entity relationships)
- ✅ Data Flow (request processing pipeline)
- ✅ Technology Stack
- ✅ Design Patterns
- ✅ Scalability Considerations

---

## Full Integration Test Script

Run this script to test everything end-to-end:

```bash
#!/bin/bash

echo "=== Testing Academic Recommendation System ==="

echo ""
echo "1. Health check..."
HEALTH=$(curl -s http://localhost:8000/health | jq .status)
if [ "$HEALTH" == '"healthy"' ]; then
    echo "✅ System is healthy"
else
    echo "❌ System health check failed"
    exit 1
fi

echo ""
echo "2. Graph-only recommendations..."
GRAPH_RECS=$(curl -s "http://localhost:8000/recommendations/graph-only?student_id=1&limit=3" | jq '.recommendations | length')
if [ "$GRAPH_RECS" -gt 0 ]; then
    echo "✅ Graph service returned $GRAPH_RECS recommendations"
else
    echo "❌ Graph service returned 0 recommendations"
fi

echo ""
echo "3. ML-only recommendations..."
ML_RECS=$(curl -s "http://localhost:8000/recommendations/ml-only?student_id=1&limit=3" | jq '.recommendations | length')
if [ "$ML_RECS" -gt 0 ]; then
    echo "✅ ML service returned $ML_RECS recommendations"
else
    echo "❌ ML service returned 0 recommendations"
fi

echo ""
echo "4. Hybrid recommendations..."
HYBRID_RECS=$(curl -s "http://localhost:8000/recommendations?student_id=1&limit=3" | jq '.recommendations | length')
if [ "$HYBRID_RECS" -gt 0 ]; then
    echo "✅ Hybrid service returned $HYBRID_RECS recommendations"
else
    echo "❌ Hybrid service returned 0 recommendations"
fi

echo ""
echo "5. Evaluation metrics..."
WINNER=$(curl -s "http://localhost:8000/evaluate?top_k=5" | jq -r '.evaluation.winner')
if [ ! -z "$WINNER" ]; then
    echo "✅ Evaluation completed. Winner: $WINNER"
else
    echo "❌ Evaluation failed"
fi

echo ""
echo "=== All tests completed ==="
```

Save as `test_api.sh`, then run:

```bash
chmod +x test_api.sh
./test_api.sh
```

**Expected output**:
```
=== Testing Academic Recommendation System ===

1. Health check...
✅ System is healthy

2. Graph-only recommendations...
✅ Graph service returned 3 recommendations

3. ML-only recommendations...
✅ ML service returned 3 recommendations

4. Hybrid recommendations...
✅ Hybrid service returned 3 recommendations

5. Evaluation metrics...
✅ Evaluation completed. Winner: hybrid

=== All tests completed ===
```

---

## Troubleshooting

### Issue: "No module named 'sqlalchemy'"
**Solution**:
```bash
pip install -r requirements.txt
```

### Issue: Graph returns 0 results
**Cause**: Old database without module-competency links
**Solution**:
```bash
rm academic_recommender.db
python data_generator.py
```

### Issue: ML training fails ("Insufficient data for training")
**Cause**: Database has <2 interactions
**Solution**: Check `data_generator.py` ran and created interactions; verify with:
```bash
sqlite3 academic_recommender.db "SELECT COUNT(*) FROM interactions;"
```
Should show ~85 interactions.

### Issue: Evaluation returns 0 metrics
**Cause**: Students don't have enough interactions for leave-one-out validation
**Solution**: Ensure `data_generator.py` created 15 students with 3-8 interactions each

---

## Success Criteria

You've successfully implemented Steps 5-7 if:

| Step | Criterion | Test Command |
|------|-----------|--------------|
| **5** (Graph Fix) | Graph returns >0 recommendations | `curl http://localhost:8000/recommendations/graph-only?student_id=1` |
| **5** (ML Fix) | ML uses SVD reconstruction (scores 0-5) | `curl http://localhost:8000/recommendations/ml-only?student_id=1` |
| **5** (Module-Competency) | 25 module-competency links created | `grep "module-competency" output of data_generator` |
| **6** (Evaluation) | `/evaluate` returns P@K, R@K, F1@K, NDCG@K | `curl http://localhost:8000/evaluate?top_k=5` |
| **6** (Comparison) | All 3 approaches evaluated | Check `evaluation.approaches` has "graph", "ml", "hybrid" keys |
| **7** (Architecture) | ARCHITECTURE.md documents design | Read ARCHITECTURE.md |

---

## Example: Full Recommendation Flow

Here's what happens when you request a recommendation:

```bash
# Request
$ curl "http://localhost:8000/recommendations?student_id=5&limit=3"

# Flow:
# 1. FastAPI validates student_id=5 exists
# 2. Fusion Service starts
#    ├─ Graph Service: Loads RDF, runs SPARQL query "find modules matching student 5's competencies"
#    │  └ Score: 0.65 for module 3 (has prerequisite, high competency match)
#    ├ ML Service: Reconstructs SVD matrix, looks at student 5's row
#    │  └ Score: 3.2 for module 3 (similar students liked it)
#    └ Fusion: α=0.6 (cold-start weights), β=0.4
#       └ Final score: 0.6×0.65 + 0.4×3.2 = 0.39 + 1.28 = 1.67 (normalized)
# 3. Return top-3 by score

# Response
{
  "student_id": 5,
  "recommendations": [
    {
      "module_id": 3,
      "module_title": "Data Science Fundamentals",
      "score": 0.72,      # weighted average of 0.65 (graph) and 3.2 (ml)
      "confidence": 0.86,  # high because both methods agree
      "reason": "Builds on your current skills",
      "graph_score": 0.65,
      "ml_score": 3.2
    },
    ...
  ],
  "method": "hybrid"
}
```

---

## Evaluation Example Output

When you run `/evaluate?top_k=5`, you get:

```json
{
  "evaluation": {
    "winner": "hybrid",
    "analysis": "Evaluation at top-5 results: Hybrid approach (F1=0.50) outperforms Graph (F1=0.35) and ML (F1=0.45). The hybrid fusion strategy effectively combines the strengths of Knowledge Graph reasoning with collaborative filtering patterns.",
    "approaches": {
      "graph": {
        "precision_at_k": 0.35,  // 35% of graph's top-5 were actually good
        "recall_at_k": 0.35,     // same (1 item per student in test)
        "f1_at_k": 0.35,
        "ndcg_at_k": 0.55        // 55% of ideal ranking quality
      },
      "ml": {
        "precision_at_k": 0.45,
        "recall_at_k": 0.45,
        "f1_at_k": 0.45,
        "ndcg_at_k": 0.68,
        "rmse": 0.95,            // predicted ratings off by ~0.95 on average
        "mae": 0.72
      },
      "hybrid": {
        "precision_at_k": 0.50,  // BEST: 50% top-5 correct
        "recall_at_k": 0.50,
        "f1_at_k": 0.50,
        "ndcg_at_k": 0.75        // BEST: 75% of ideal ranking
      }
    }
  }
}
```

---

**All tests passing?** You've successfully completed Steps 5-7! 🎉
