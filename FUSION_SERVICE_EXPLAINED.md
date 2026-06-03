# Fusion Service Deep Dive: Combining Graph & ML Intelligently

**Document Purpose**: Complete explanation of how Graph and ML services are intelligently combined with dynamic weighting.

---

## Table of Contents

1. [The Big Picture](#the-big-picture)
2. [The Philosophy: Why Hybrid?](#the-philosophy-why-hybrid)
3. [Dynamic Weighting Strategy](#dynamic-weighting-strategy)
4. [Code Walkthrough](#code-walkthrough)
5. [Confidence Calculation](#confidence-calculation)
6. [Visual Examples](#visual-examples)
7. [Design Patterns](#design-patterns)

---

## The Big Picture

### What Does the Fusion Service Do?

The Fusion Service is the **conductor of an orchestra** 🎼

Imagine an orchestra with two musicians:
- **Graph Service**: A classical violinist who plays from sheet music (explicit rules)
- **ML Service**: A jazz improviser who plays from intuition (learned patterns)

The Fusion Service decides **who should lead** based on the situation:
- **New orchestra** (few rehearsals): Let the violinist (Graph) lead 80% - they follow the score
- **Experienced orchestra** (many rehearsals): Let the jazz player (ML) lead 70% - they know the vibe

### Core Job

```
Graph Recommendations (semantic, rule-based)
            ↓
         FUSE  ← Fusion Service
            ↓
ML Recommendations (statistical, pattern-based)

With dynamic weighting: final_score = α × graph_score + β × ml_score
```

---

## The Philosophy: Why Hybrid?

### The Problem with Pure Approaches

#### Graph Service Alone
**Pros**:
- Excellent for new students (no history needed)
- Transparent and explainable
- Uses domain knowledge (ontology)

**Cons**:
- Can only find "obvious" recommendations
- Miss patterns humans don't explicitly encode
- Limited discovery capability

#### ML Service Alone
**Pros**:
- Discovers hidden patterns
- Better accuracy with enough data
- Finds non-obvious connections

**Cons**:
- Fails completely for new students (no history = no patterns)
- "Black box" - hard to explain why
- Needs lots of interactions to work

#### Hybrid (Fusion) Approach ✨
**Combines**:
- Graph's strength: Works from day 1
- ML's strength: Gets smarter with more data
- Adapts: Shifts trust gradually as student accumulates history

**Result**: **Best of both worlds at every stage**

---

## Dynamic Weighting Strategy

### The Core Concept

Instead of **choosing** between Graph and ML, we **blend** them with **adaptive weights** that change as the student accumulates data.

### The Three Phases

```
┌─────────────────────────────────────────────────────────────┐
│          STUDENT INTERACTION JOURNEY                        │
└─────────────────────────────────────────────────────────────┘

Phase 1: COLD START
Interactions: 0-4
Graph: 80% ████████░░
ML:    20% ██░░░░░░░░
Reason: ML has no signal (too sparse)
        Graph is the reliable source
        
        │
        ▼

Phase 2: TRANSITION
Interactions: 5-19
Graph: 80% → 30% (gradually decreases)
ML:    20% → 70% (gradually increases)
Reason: ML builds strength as data accumulates
        Graph still provides stability
        
        │
        ▼

Phase 3: MATURE
Interactions: 20+
Graph: 30% ███░░░░░░░
ML:    70% ███████░░░
Reason: ML has strong signal
        Graph adds diversity
        Trust the patterns!
```

### The Math Behind Transitions

#### Phase 1: Cold Start (<5 interactions)
```python
alpha = 0.8
beta = 0.2
```

#### Phase 2: Transition (5-19 interactions)
```python
progress = (interaction_count - 5) / 15
alpha = 0.8 - (0.5 * progress)
beta = 0.2 + (0.5 * progress)
```

**How it works**:
- `progress` ranges from 0.0 to 1.0 as interactions go from 5 to 20
- When `progress = 0` (5 interactions): alpha=0.8, beta=0.2
- When `progress = 0.5` (12 interactions): alpha=0.55, beta=0.45 (balanced!)
- When `progress = 1.0` (20 interactions): alpha=0.3, beta=0.7

#### Phase 3: Mature (≥20 interactions)
```python
alpha = 0.3
beta = 0.7
```

### Why These Specific Numbers?

| Threshold | Reasoning |
|-----------|-----------|
| **5 interactions** | ML needs minimum signal to be reliable |
| **20 interactions** | ML becomes dominant, but Graph still adds value |
| **80% Graph** | Graph is highly trustworthy for cold-start |
| **70% ML** | ML is good but Graph adds diversity in mature phase |
| **30% Graph** | Even with mature ML, Graph prevents overfitting to patterns |

---

## Code Walkthrough

### File: `services/fusion_service.py`

---

### Section 1: Initialization (Lines 16-18)

```python
def __init__(self, graph_service, ml_service):
    self.graph_service = graph_service
    self.ml_service = ml_service
```

**What it does**:
Stores references to both Graph and ML services for later use.

**Pattern**: **Dependency Injection**
- Services are passed in (not created here)
- Allows testing with mock services
- Decouples services from each other

**Why this design**:
- Flexibility: Can swap implementations
- Testability: Can inject test doubles
- Clean architecture: No hard dependencies

---

### Section 2: The Main Method (Lines 20-111)

#### 2.1: Get Recommendations from Both Services (Lines 42-69)

```python
recommendations_by_module = {}

# Get graph-based recommendations
if use_graph:
    graph_recs = self.graph_service.get_recommendations(student_id, limit * 2, db)
    for rec in graph_recs:
        if rec.module_id not in recommendations_by_module:
            recommendations_by_module[rec.module_id] = {
                "module_id": rec.module_id,
                "module_title": rec.module_title,
                "graph_score": rec.graph_score or rec.score,
                "ml_score": None,
                "graph_reason": rec.reason
            }
        else:
            recommendations_by_module[rec.module_id]["graph_score"] = rec.graph_score or rec.score

# Get ML-based recommendations
if use_ml:
    ml_recs = self.ml_service.get_recommendations(student_id, limit * 2, db)
    for rec in ml_recs:
        if rec.module_id not in recommendations_by_module:
            recommendations_by_module[rec.module_id] = {
                "module_id": rec.module_id,
                "module_title": rec.module_title,
                "graph_score": None,
                "ml_score": rec.ml_score or rec.score,
                "ml_reason": rec.reason
            }
        else:
            recommendations_by_module[rec.module_id]["ml_score"] = rec.ml_score or rec.score
```

**What it does**:
1. Calls Graph Service → gets top recommendations
2. Calls ML Service → gets top recommendations
3. Merges them into a **union** (not intersection)

**Key detail: `limit * 2`**

Why request 2× the limit?

**Example**: User asks for top 5

```
Graph recommends (top 10):
  Module A: 0.8
  Module B: 0.7
  Module C: 0.6
  Module D: 0.5
  ...

ML recommends (top 10):
  Module B: 0.9    ← Same as Graph!
  Module E: 0.8    ← New!
  Module C: 0.7    ← Same as Graph
  Module F: 0.6
  ...

After merging (union):
  Module A: {graph: 0.8, ml: None}
  Module B: {graph: 0.7, ml: 0.9}  ← Both methods agree!
  Module C: {graph: 0.6, ml: 0.7}  ← Both methods agree!
  Module D: {graph: 0.5, ml: None}
  Module E: {graph: None, ml: 0.8}
  Module F: {graph: None, ml: 0.6}
  ...
  (6 total modules)

After fusing and sorting, return top 5
```

**Why fetch 2×limit?**
- Some modules appear in both lists (agreement)
- Some appear in only one list
- By fetching more, we get better coverage
- After fusion, we trim to exact limit

#### 2.2: Calculate Dynamic Weights (Line 72)

```python
alpha, beta = self._calculate_weights(student_id, db)
```

Calls the weighting method based on student's interaction count. (Detailed below)

#### 2.3: Fuse Scores (Lines 75-101)

```python
fused_recommendations = []
for module_id, data in recommendations_by_module.items():
    graph_score = data.get("graph_score", 0) or 0
    ml_score = data.get("ml_score", 0) or 0
    
    # Handle cold start vs. mature profile
    if use_graph and use_ml:
        final_score = alpha * graph_score + beta * ml_score
    elif use_graph:
        final_score = graph_score
    else:
        final_score = ml_score
    
    # Determine reason
    reason = "Hybrid recommendation"
    if data.get("graph_reason"):
        reason = data["graph_reason"]
    
    fused_recommendations.append(RecommendationItem(
        module_id=module_id,
        module_title=data["module_title"],
        score=float(final_score),
        confidence=self._calculate_confidence(graph_score, ml_score, alpha, beta),
        reason=reason,
        graph_score=graph_score if use_graph else None,
        ml_score=ml_score if use_ml else None
    ))
```

**THE FUSION FORMULA**:

```python
final_score = alpha * graph_score + beta * ml_score
```

**What it does**:
- Takes weighted average of two scores
- `alpha` = weight for Graph
- `beta` = weight for ML
- Result = single fused score

**Example with cold-start student** (alpha=0.8, beta=0.2):

```
Module A:
  graph_score = 0.75
  ml_score = 0.50
  final_score = 0.8 × 0.75 + 0.2 × 0.50
              = 0.60 + 0.10
              = 0.70  ← Graph dominates

Module B:
  graph_score = 0.40
  ml_score = 0.80
  final_score = 0.8 × 0.40 + 0.2 × 0.80
              = 0.32 + 0.16
              = 0.48  ← Still favors Graph

Graph wins because alpha=0.8!
```

**Example with mature student** (alpha=0.3, beta=0.7):

```
Same modules:

Module A:
  final_score = 0.3 × 0.75 + 0.7 × 0.50
              = 0.225 + 0.35
              = 0.575  ← ML has more influence

Module B:
  final_score = 0.3 × 0.40 + 0.7 × 0.80
              = 0.12 + 0.56
              = 0.68  ← ML dominates (0.80 wins!)

ML wins because beta=0.7!
```

**Handling edge cases**:
```python
if use_graph and use_ml:
    final_score = alpha * graph_score + beta * ml_score
elif use_graph:
    final_score = graph_score
else:
    final_score = ml_score
```

Allows calling with flags:
- `use_graph=True, use_ml=True`: Full fusion
- `use_graph=True, use_ml=False`: Graph only
- `use_graph=False, use_ml=True`: ML only

#### 2.4: Sort and Return (Lines 104-111)

```python
fused_recommendations.sort(key=lambda x: x.score, reverse=True)

logger.info(
    f"Generated {len(fused_recommendations[:limit])} hybrid recommendations "
    f"for student {student_id} (α={alpha:.2f}, β={beta:.2f})"
)

return fused_recommendations[:limit]
```

**What it does**:
1. Sorts by fused score (highest first)
2. Logs the weights used (for debugging)
3. Returns top `limit` recommendations

---

### Section 3: Calculate Weights (Lines 117-156)

```python
def _calculate_weights(self, student_id: int, db: Session) -> tuple:
    """
    Calculate dynamic weights based on student data maturity.
    """
    try:
        from models import InteractionDB
        
        # Count student interactions
        interaction_count = db.query(InteractionDB).filter(
            InteractionDB.student_id == student_id
        ).count()
        
        # Dynamic weighting based on interaction count
        if interaction_count < 5:
            # Cold start profile
            alpha = 0.8
            beta = 0.2
        elif interaction_count < 20:
            # Transition phase
            progress = (interaction_count - 5) / 15
            alpha = 0.8 - (0.5 * progress)
            beta = 0.2 + (0.5 * progress)
        else:
            # Mature profile
            alpha = 0.3
            beta = 0.7
        
        return (alpha, beta)
    
    except Exception as e:
        logger.warning(f"Error calculating weights: {str(e)}, using default")
        return (0.5, 0.5)
```

**What it does**:
1. Counts how many modules this student has interacted with
2. Maps interaction count → weighting phase
3. Returns (alpha, beta) tuple

**The three phases explained**:

**Phase 1: Cold Start** (< 5 interactions)
```python
if interaction_count < 5:
    alpha = 0.8
    beta = 0.2
```
- Student is brand new or barely started
- Not enough data for ML to find patterns
- Trust Graph 80% of the time

**Phase 2: Transition** (5-19 interactions)
```python
elif interaction_count < 20:
    progress = (interaction_count - 5) / 15
    alpha = 0.8 - (0.5 * progress)
    beta = 0.2 + (0.5 * progress)
```

**Let's compute some examples**:

```
At 5 interactions:
  progress = (5 - 5) / 15 = 0 / 15 = 0.0
  alpha = 0.8 - (0.5 × 0.0) = 0.8
  beta = 0.2 + (0.5 × 0.0) = 0.2
  (Same as cold-start, transition begins)

At 12 interactions (midpoint):
  progress = (12 - 5) / 15 = 7 / 15 = 0.467
  alpha = 0.8 - (0.5 × 0.467) = 0.8 - 0.233 = 0.567
  beta = 0.2 + (0.5 × 0.467) = 0.2 + 0.233 = 0.433
  (Almost balanced!)

At 19 interactions:
  progress = (19 - 5) / 15 = 14 / 15 = 0.933
  alpha = 0.8 - (0.5 × 0.933) = 0.8 - 0.467 = 0.333
  beta = 0.2 + (0.5 × 0.933) = 0.2 + 0.467 = 0.667
  (Approaching mature)

At 20 interactions:
  (Enters Phase 3)
```

**Visualization**:
```
      alpha (Graph)        beta (ML)
      │                    │
  0.8 ├─────────┐          │  0.8
      │         │╲         │    ╱
  0.6 │         │ ╲────────┼──╱  0.6
      │         │         ╲│╱
  0.4 │         │          ✕      0.4
      │         │         ╱│╲
  0.2 │─────────┴────────╱ │  ╲   0.2
      │ Phase1 │ Phase 2  │ Phase 3
      0    5         20        interactions
      
Graph starts at 80%, gradually drops to 30%
ML starts at 20%, gradually rises to 70%
```

**Phase 3: Mature** (≥ 20 interactions)
```python
else:
    alpha = 0.3
    beta = 0.7
```
- Student has taken 20+ modules
- ML has strong signal from history
- Trust ML 70%, Graph 30%
- Graph still helps with serendipity/diversity

**Default fallback**:
```python
except Exception as e:
    logger.warning(f"Error calculating weights: {str(e)}, using default")
    return (0.5, 0.5)
```

If anything fails (can't query DB, etc.), use balanced 50-50 weights.

---

### Section 4: Calculate Confidence (Lines 158-168)

```python
def _calculate_confidence(self, graph_score: float, ml_score: float, alpha: float, beta: float) -> float:
    """Calculate confidence score for the recommendation"""
    if graph_score and ml_score:
        # Both methods agree - high confidence
        agreement = 1 - abs(graph_score - ml_score)
        return float(min(0.95, 0.7 + agreement * 0.25))
    elif graph_score or ml_score:
        # Only one method available
        return float(min(0.85, 0.6 + max(graph_score, ml_score) * 0.25))
    else:
        return 0.5
```

**What it does**:
Computes confidence (0.0-0.95) based on whether Graph and ML agree.

**The Logic**:

#### Case 1: Both Methods Have Scores

```python
agreement = 1 - abs(graph_score - ml_score)
confidence = min(0.95, 0.7 + agreement * 0.25)
```

**What it means**: "How much do Graph and ML agree?"

**Example 1: Perfect agreement**
```
graph_score = 0.80
ml_score = 0.80
agreement = 1 - abs(0.80 - 0.80) = 1 - 0 = 1.0
confidence = min(0.95, 0.7 + 1.0 × 0.25)
           = min(0.95, 0.95)
           = 0.95  ← Very confident! (95%)
```

**Interpretation**: Both methods predicted the same score → Trust it!

**Example 2: Partial agreement**
```
graph_score = 0.80
ml_score = 0.60
agreement = 1 - abs(0.80 - 0.60) = 1 - 0.20 = 0.80
confidence = min(0.95, 0.7 + 0.80 × 0.25)
           = min(0.95, 0.7 + 0.20)
           = min(0.95, 0.90)
           = 0.90  ← Fairly confident (90%)
```

**Interpretation**: Methods somewhat agree → Pretty sure, but not 100%

**Example 3: Disagreement**
```
graph_score = 0.95
ml_score = 0.10
agreement = 1 - abs(0.95 - 0.10) = 1 - 0.85 = 0.15
confidence = min(0.95, 0.7 + 0.15 × 0.25)
           = min(0.95, 0.7 + 0.0375)
           = min(0.95, 0.7375)
           = 0.7375  ← Less confident (73%)
```

**Interpretation**: Methods disagree wildly → Be skeptical, but still recommend

#### Case 2: Only One Method Has Score

```python
elif graph_score or ml_score:
    return float(min(0.85, 0.6 + max(graph_score, ml_score) * 0.25))
```

**When does this happen?**
- Cold-start student: Only Graph has score
- New module: Only ML might have score
- Data issues: One service failed

**Example**:
```
graph_score = 0.80
ml_score = None (not available)

confidence = min(0.85, 0.6 + max(0.80, None) × 0.25)
           = min(0.85, 0.6 + 0.80 × 0.25)
           = min(0.85, 0.6 + 0.20)
           = min(0.85, 0.80)
           = 0.80  ← 80% confident
```

**Why capped at 0.85?** Less confident than when both methods agree.

#### Case 3: Neither Method Has Score

```python
else:
    return 0.5
```

Shouldn't happen in practice, but defensive coding → return neutral confidence.

---

## Confidence Calculation Formula

### Agreement-Based Confidence (Both methods present)

```
agreement = 1 - |graph_score - ml_score|
confidence = min(0.95, 0.7 + 0.25 × agreement)

Range: [0.70, 0.95]
- agreement=0.0 (total disagreement) → confidence=0.70
- agreement=1.0 (perfect agreement) → confidence=0.95
```

### Single-Method Confidence (One method missing)

```
confidence = min(0.85, 0.6 + 0.25 × max(graph_score, ml_score))

Range: [0.60, 0.85]
- score=0.0 → confidence=0.60
- score=1.0 → confidence=0.85
```

### Why These Numbers?

| Threshold | Meaning |
|-----------|---------|
| **0.70** | Minimum confidence (both disagree) |
| **0.85** | Cap for single method |
| **0.95** | Maximum confidence (perfect agreement) |
| **0.6** | Base confidence without score |
| **0.25** | Confidence gain from agreement |

**Philosophy**: Never claim 100% certainty. Humility is important! 🙏

---

## Visual Examples

### Example 1: Cold-Start Student (0 interactions)

**Scenario**: Alice just enrolled, hasn't taken anything yet.

**Weights calculated**:
```python
interaction_count = 0
alpha = 0.8
beta = 0.2
```

**Service calls**:
- Graph Service: "Based on your competencies, try Data Analysis" (score: 0.75)
- ML Service: "Can't predict, no history" (no score)

**Fusion process**:
```python
graph_score = 0.75
ml_score = None → treated as 0

final_score = 0.8 × 0.75 + 0.2 × 0
            = 0.60 + 0
            = 0.60

confidence = min(0.85, 0.6 + max(0.75) × 0.25)
           = min(0.85, 0.6 + 0.19)
           = min(0.85, 0.79)
           = 0.79  (79% confident)
```

**Result**: "Data Analysis (score: 0.60, confidence: 79%)"

**Why this makes sense**:
- Graph dominates (80%) because Alice has no history
- Confidence is high (79%) because Graph is reliable for cold-start
- Alice gets personalized recommendations on day 1

---

### Example 2: Transition Student (12 interactions)

**Scenario**: Bob has taken 12 courses. ML is getting stronger.

**Weights calculated**:
```python
interaction_count = 12
progress = (12 - 5) / 15 = 0.467
alpha = 0.8 - (0.5 × 0.467) = 0.567
beta = 0.2 + (0.5 × 0.467) = 0.433
```

**Service calls**:
- Graph Service: "Machine Learning" (score: 0.70)
- ML Service: "Machine Learning" (score: 0.82)

**Both methods recommend the same module! 🎉**

**Fusion process**:
```python
graph_score = 0.70
ml_score = 0.82

final_score = 0.567 × 0.70 + 0.433 × 0.82
            = 0.397 + 0.355
            = 0.752

agreement = 1 - abs(0.70 - 0.82) = 1 - 0.12 = 0.88
confidence = min(0.95, 0.7 + 0.88 × 0.25)
           = min(0.95, 0.7 + 0.22)
           = min(0.95, 0.92)
           = 0.92  (92% confident!)
```

**Result**: "Machine Learning (score: 0.752, confidence: 92%)"

**Why high confidence?**
- Both methods recommend it
- Agreement is strong (0.88)
- We can trust this recommendation!

---

### Example 3: Mature Student (25 interactions)

**Scenario**: Carol has taken 25 courses. ML is now the leader.

**Weights calculated**:
```python
interaction_count = 25
alpha = 0.3
beta = 0.7
```

**Service calls**:
- Graph Service: "Web Development" (score: 0.60)
- ML Service: "Web Development" (score: 0.75)

**ML scores higher, Graph provides backup.**

**Fusion process**:
```python
graph_score = 0.60
ml_score = 0.75

final_score = 0.3 × 0.60 + 0.7 × 0.75
            = 0.18 + 0.525
            = 0.705

agreement = 1 - abs(0.60 - 0.75) = 1 - 0.15 = 0.85
confidence = min(0.95, 0.7 + 0.85 × 0.25)
           = min(0.95, 0.7 + 0.2125)
           = min(0.95, 0.9125)
           = 0.9125  (91% confident)
```

**Result**: "Web Development (score: 0.705, confidence: 91%)"

**Why this works**:
- ML dominates (70%) because Carol has strong history
- Graph still adds 30% for diversity
- Even though they disagree (0.60 vs 0.75), we're confident because both recommend it

---

### Example 4: Conflicting Recommendations

**Scenario**: David has 15 interactions. Methods disagree.

**Weights**: (alpha=0.65, beta=0.35)

**Service calls**:
- Graph Service: "Python Basics" (score: 0.85)
- ML Service: "Advanced AI" (score: 0.90)

**Different modules recommended!**

**Fusion must decide...**

**For Python Basics**:
```python
graph_score = 0.85
ml_score = None (not recommended by ML)

final_score = 0.65 × 0.85 + 0.35 × 0
            = 0.5525

confidence = min(0.85, 0.6 + max(0.85) × 0.25)
           = min(0.85, 0.6 + 0.2125)
           = min(0.85, 0.8125)
           = 0.8125  (81%)
```

**For Advanced AI**:
```python
graph_score = None (not recommended by Graph)
ml_score = 0.90

final_score = 0.65 × 0 + 0.35 × 0.90
            = 0.315

confidence = min(0.85, 0.6 + max(0.90) × 0.25)
           = min(0.85, 0.6 + 0.225)
           = min(0.85, 0.825)
           = 0.825  (83%)
```

**After fusion and sorting**:
1. Python Basics: 0.553 (81%)
2. Advanced AI: 0.315 (83%)

**Rank**: Python Basics wins! (higher fused score)

**Why?**
- Python: Graph supports + moderate ML weight = 0.553
- Advanced AI: Only ML recommends + lower weight = 0.315
- Graph's strong support for Python outweighs ML's preference for AI

---

## Design Patterns

### Pattern 1: Dependency Injection

```python
def __init__(self, graph_service, ml_service):
    self.graph_service = graph_service
    self.ml_service = ml_service
```

**What it means**: Services are injected, not created.

**Benefit**:
- Easy to test (inject mock services)
- Easy to swap implementations
- Loose coupling

**Alternative (bad)**:
```python
# BAD: Hard-coded dependency
self.graph_service = GraphService()
self.ml_service = MLService()
```

---

### Pattern 2: Adaptive Algorithm

```python
# Behavior changes based on input (interaction count)
if interaction_count < 5:
    alpha, beta = 0.8, 0.2
elif interaction_count < 20:
    # Linear interpolation
    alpha = 0.8 - (0.5 * progress)
    beta = 0.2 + (0.5 * progress)
else:
    alpha, beta = 0.3, 0.7
```

**What it means**: Algorithm adapts to student maturity.

**Benefit**:
- Contextual behavior (cold-start vs. mature)
- Smooth transitions (no jumps)
- Self-improving system

---

### Pattern 3: Graceful Degradation

```python
if use_graph and use_ml:
    final_score = alpha * graph_score + beta * ml_score
elif use_graph:
    final_score = graph_score
else:
    final_score = ml_score
```

**What it means**: Works even if one service is disabled.

**Benefit**:
- Robust to failures
- Testable in isolation
- Flexible deployment

---

### Pattern 4: Confidence-Based Uncertainty

```python
# Different confidence based on agreement
if graph_score and ml_score:
    agreement = 1 - abs(graph_score - ml_score)
    confidence = min(0.95, 0.7 + agreement * 0.25)
```

**What it means**: Confidence reflects how much methods agree.

**Benefit**:
- Honest about uncertainty
- Users trust more when both agree
- Basis for A/B testing ("should we trust this?")

---

## The Algorithm in Plain English

```
1. Get the student
2. Call Graph Service → get top 10 recommendations
3. Call ML Service → get top 10 recommendations
4. Merge them into a pool of unique modules
5. Calculate weights based on student's interaction count:
   - New student? 80% Graph, 20% ML
   - Experienced? 30% Graph, 70% ML
   - In-between? Smoothly transition
6. For each module:
   a. Fuse scores: final = (weight_graph × graph_score) + (weight_ml × ml_score)
   b. Calculate confidence based on whether both methods agree
   c. Create recommendation object
7. Sort by fused score (highest first)
8. Return top K recommendations
```

---

## Why This Design Works

### Problem It Solves

**Without Fusion**:
- New student: ML fails (no data) → Bad recommendations
- Experienced student: Graph is too rigid → Misses patterns
- Can't choose one approach for all students

**With Fusion**:
- New student: Graph carries the day
- Experienced student: ML discovers patterns, Graph adds diversity
- Perfect for all stages of student journey

### Trade-offs Made

| Choice | Pro | Con |
|--------|-----|-----|
| **Hard weights (80/20)** | Simple, predictable | Not adaptive |
| **Soft weights (transition)** | Adaptive, smooth | More complex |
| **(We chose soft)** | ✅ Better UX | More code |
| **Request 2× limit** | Better coverage | Slightly slower |
| **Confidence by agreement** | Honest uncertainty | Takes more computation |

### Inspiration

This approach is inspired by **ensemble methods** in machine learning:
- Random Forests: Combine many decision trees
- Gradient Boosting: Combine weak learners
- **Fusion Service**: Combine two strong reasoners

---

## Summary Table

| Aspect | Cold-Start | Transition | Mature |
|--------|-----------|-----------|--------|
| **Interactions** | < 5 | 5-19 | ≥ 20 |
| **Alpha (Graph)** | 0.80 | 0.80→0.30 | 0.30 |
| **Beta (ML)** | 0.20 | 0.20→0.70 | 0.70 |
| **Best at** | New users | Balanced | Discovering patterns |
| **Confidence** | High (Graph reliable) | Moderate | High (if methods agree) |
| **Use case** | Day 1 recommendations | Growing user | Long-term retention |

---

**Document Complete**: The Fusion Service explained from architecture to implementation!

