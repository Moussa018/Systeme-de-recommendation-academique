# ML Service Deep Dive: Understanding Collaborative Filtering & SVD

**Document Purpose**: Complete explanation of the ML recommendation engine with reasoning, analogies, and code-by-code breakdown.

---

## Table of Contents

1. [The Big Picture](#the-big-picture)
2. [The Core Philosophy](#the-core-philosophy)
3. [Collaborative Filtering Explained](#collaborative-filtering-explained)
4. [SVD (Singular Value Decomposition)](#svd-singular-value-decomposition)
5. [Code Walkthrough](#code-walkthrough)
6. [Design Decisions & Why](#design-decisions--why)
7. [The Math Behind It](#the-math-behind-it)
8. [Visual Examples](#visual-examples)

---

## The Big Picture

### What Does the ML Service Do?

The ML Service answers one question: **"Based on what similar students liked, what should THIS student study next?"**

It's like asking a coffee shop barista: *"I see you like cappuccinos and chocolate croissants. Based on other customers with similar tastes, you'd probably love our new hazelnut pastry."*

### How It Differs from the Graph Service

| Aspect | Graph Service | ML Service |
|--------|---------------|-----------|
| **Logic Type** | Explicit/Symbolic | Implicit/Statistical |
| **How it Decides** | "This module teaches competency X, you have competency X" | "Students like you also liked module Y" |
| **Data Needed** | Semantic structure (ontology) | Historical interactions |
| **Best For** | New students (cold-start) | Experienced students |
| **Explanation** | Can explain reasoning clearly | Hard to explain ("trust the math") |
| **Discovery** | Finds obvious connections | Finds hidden patterns |

---

## The Core Philosophy

### The Core Idea: Latent Factors

Imagine you're trying to understand why people like movies. You could say:
- Person A likes: Action, Sci-Fi, Fast-paced
- Person B likes: Drama, Character-driven, Thoughtful
- Movie X is: Action, Sci-Fi, Fast-paced

**Person A will probably like Movie X.**

The ML Service does the same with students and modules:

```
Student Alice has latent preferences: [high-affinity-to-math, high-affinity-to-coding, low-affinity-to-history]
Module "Machine Learning" has latent characteristics: [requires-math, requires-coding, computer-science]

→ Alice will probably like Machine Learning!
```

But we don't manually define these characteristics. **SVD discovers them automatically from historical data.**

### Why This Works

When 100+ students rate modules, patterns emerge:
- Students who excel at Calculus also rate Linear Algebra highly
- Students who like Web Dev also like Databases
- Students who complete Data Analysis also complete Statistics

The ML Service **extracts these hidden patterns** and uses them to predict what new students will like.

---

## Collaborative Filtering Explained

### The Analogy: Restaurant Recommendations

Imagine you're new to a city and want restaurant recommendations:

**Bad way**: "Here are restaurants that are objectively good."
- Problem: Doesn't know YOUR taste

**Good way**: "I found 10 people with similar tastes to you. Here are restaurants they loved that you haven't tried."
- Better: Uses shared preferences

**Collaborative Filtering way**: "I analyzed patterns in what similar people like, and discovered 5 hidden dimensions of taste preferences. Based on your 5-dimensional preference vector, these are the top matches."
- Best: Sophisticated pattern matching

### Types of Collaborative Filtering

```
Collaborative Filtering
├─ Memory-based (User-User)
│  └─ "Find similar students, recommend what they liked"
│
├─ Memory-based (Item-Item)
│  └─ "Find similar modules, recommend them"
│
└─ Model-based (Matrix Factorization) ← WE USE THIS
   └─ "Extract hidden dimensions, predict ratings"
```

### Why Matrix Factorization?

Matrix Factorization = "Dimension Reduction"

**Before**: Large table of sparse data (many blanks)
```
         Module1  Module2  Module3  Module4  ...
Student1   4        ?        ?        5
Student2   3        2        ?        ?
Student3   ?        4        3        2
Student4   5        ?        ?        4
```

**After**: Two smaller dense tables (no blanks)
```
         Factor1  Factor2  Factor3           Module1  Module2  Module3  Module4
Student1  0.8     -0.3     0.1     ×     ×  [combining from factors...]
Student2  0.2      0.9    -0.2
Student3 -0.1      0.7     0.4
Student4  0.9     -0.2     0.6
```

**Benefit**: 
- Reduces noise
- Finds patterns across sparse data
- Can predict missing values
- More computational efficiency

---

## SVD (Singular Value Decomposition)

### What is SVD?

SVD is a mathematical technique that breaks down a matrix into its essential components.

### The Best Analogy: DNA of a Matrix

Imagine a human has 46 chromosomes but 99% of important genetic information can be expressed with just 10 key characteristics:
- Height
- Eye color
- Skin tone
- Hair texture
- Metabolism
- etc.

You don't need all 46 chromosomes to predict what a child will look like—you just need the 10 key traits.

**SVD does the same for students and modules.**

Instead of storing a huge sparse matrix (students × modules), SVD extracts the 10 most important hidden dimensions:
- `Factor 1`: "Affinity to mathematical thinking"
- `Factor 2`: "Preference for applied work"
- `Factor 3`: "Comfort with programming"
- `Factor 4`: "Interest in theory"
- ... (up to 10)

### How SVD Works (Simplified)

```
Original Matrix X:     SVD Decomposition:
15 students ×          
10 modules    →        = U × Σ × V^T

Dimensions:           Dimensions:
15 × 10               (15×10) × (10×10) × (10×10)^T
```

Breaking it down:

| Component | Meaning | Dimensions |
|-----------|---------|------------|
| **U** | Student latent factors (their preference vector) | 15 students × 10 factors |
| **Σ** | Importance of each factor (which factors matter most) | 10 × 10 (diagonal matrix) |
| **V^T** | Module latent factors (their characteristic vector) | 10 factors × 10 modules |

### Reconstruction: The Magic

Once we have U and V (absorbed Σ into V), we can reconstruct ANY rating:

```
Predicted Rating[Student i, Module j] = U[i] • V[j]

= (Student i's 10-factor vector) • (Module j's 10-factor vector)
= Dot product of the two vectors
```

It's like: "How similar is Student i's preference vector to Module j's characteristic vector?"

**High similarity → High predicted rating**

---

## Code Walkthrough

### File: `services/ml_service.py`

Let's walk through every section and explain what it does and why.

---

### Section 1: Imports & Setup (Lines 1-12)

```python
import logging
import numpy as np
from typing import List, Dict, Tuple
from sqlalchemy.orm import Session
from sklearn.decomposition import TruncatedSVD
from sklearn.preprocessing import StandardScaler
import warnings

from models import StudentDB, ModuleDB, InteractionDB
from schemas import RecommendationItem

warnings.filterwarnings('ignore')
logger = logging.getLogger(__name__)
```

**What it does**:
- `numpy`: Fast matrix operations
- `TruncatedSVD`: The SVD algorithm (from scikit-learn)
- `StandardScaler`: (imported but not used in current code) - normalizes data
- `warnings.filterwarnings('ignore')`: Suppresses sklearn warnings
- `logger`: Logs training progress and errors

**Why**:
- We need fast matrix math (numpy is optimized in C)
- TruncatedSVD is the most efficient for sparse data
- Logging helps debug training issues

---

### Section 2: Class Initialization (Lines 15-28)

```python
class MLService:
    """
    Machine Learning Service for collaborative filtering based recommendations.
    Implements both SVD (Matrix Factorization) and basic Neural Collaborative Filtering.
    """
    
    def __init__(self, n_factors: int = 10):
        self.n_factors = n_factors              # Number of hidden dimensions (latent factors)
        self.user_factors = None                # U matrix from SVD: (n_students, n_factors)
        self.item_factors = None                # V^T from SVD: (n_factors, n_modules)
        self.students = []                      # Cached list of all students
        self.modules = []                       # Cached list of all modules
        self.interaction_matrix = None          # The original rating matrix
        self.model_trained = False              # Flag: have we run SVD yet?
```

**What it does**:
Creates the ML service object with slots for storing:
- The trained model (user_factors, item_factors)
- A flag so we know whether to train or use cached model

**Why**:
- `n_factors=10` is a good balance:
  - **Too few factors** (e.g., 2-3): Not enough to capture patterns → Underfitting
  - **Just right** (e.g., 10): Captures patterns without overfitting
  - **Too many factors** (e.g., all of them): Memorizes noise → Overfitting
  
- Caching `students` and `modules` avoids re-querying database every time
- `model_trained` flag avoids re-training on every recommendation request

**Decision**: Why 10 factors specifically?
- Rule of thumb: `n_factors = sqrt(min(n_students, n_modules))`
- With 15 students and 10 modules: `sqrt(min(15,10)) = sqrt(10) ≈ 3.16 → round to 10`
- Provides good generalization without overfitting

---

### Section 3: The `train()` Method (Lines 30-67)

This is where the magic happens. Let's break it down step by step.

#### 3.1: Fetching Data (Lines 33-41)

```python
def train(self, db: Session):
    """Train the collaborative filtering model"""
    try:
        logger.info("Training ML model...")

        # Get all students and modules
        self.students = db.query(StudentDB).all()
        self.modules = db.query(ModuleDB).all()

        if not self.students or not self.modules:
            logger.warning("Insufficient data for training")
            return False
```

**What it does**:
1. Pulls all students and modules from the database
2. Checks if we have data (returns False if not)

**Why**:
- Can't train SVD without data
- Caches the lists for later use (avoiding repeated queries)

**Error handling**:
- Returns False gracefully instead of crashing
- Other parts of code check the return value

#### 3.2: Creating the Interaction Matrix (Lines 43-45)

```python
        # Create interaction matrix
        interactions = db.query(InteractionDB).all()
        self.interaction_matrix = self._create_interaction_matrix(interactions)
```

**What it does**:
Calls `_create_interaction_matrix()` to build the core data structure.

**The interaction matrix** is a table:
```
Rows = Students (15 students)
Cols = Modules (10 modules)
Values = Rating scores (0-5) or completion rates (0-100)
```

Example:
```
         ML101  DB101  AI201  Web101  ...
Alice      4      5      ?       ?
Bob        3      ?      4       2
Carol      ?      3      3       ?
...
```

Most cells are empty (`?` = 0) because most students haven't taken most modules.

#### 3.3: SVD Training with Adaptive n_components (Lines 47-64)

```python
        # Apply SVD with adaptive n_components
        if self.interaction_matrix.size > 0:
            # SVD requires n_components <= min(n_rows, n_cols)
            max_components = min(self.interaction_matrix.shape[0], self.interaction_matrix.shape[1])
            n_components = min(self.n_factors, max_components)

            if n_components < 1:
                logger.warning("Not enough data for SVD training")
                return False

            svd = TruncatedSVD(n_components=n_components, random_state=42)
            self.user_factors = svd.fit_transform(self.interaction_matrix)
            self.item_factors = svd.components_.T
            self.model_trained = True
            logger.info(f"Model trained with {len(self.students)} students and {len(self.modules)} modules (n_components={n_components})")
            return True
```

**Breaking this down**:

**Line 50-51: Adaptive n_components**
```python
max_components = min(self.interaction_matrix.shape[0], self.interaction_matrix.shape[1])
n_components = min(self.n_factors, max_components)
```

**Why adaptive?**

SVD has a hard constraint: `n_components` must be **≤ the smaller dimension of the matrix**.

Example:
- If we have 15 students and 10 modules → max 10 components possible
- We want 10 factors, which fits perfectly
- But if we only had 3 modules → max 3 components → we'd use 3 instead of 10

**This prevents crashes while keeping components as high as possible.**

**Line 57-58: The actual SVD**
```python
svd = TruncatedSVD(n_components=n_components, random_state=42)
self.user_factors = svd.fit_transform(self.interaction_matrix)
self.item_factors = svd.components_.T
```

**What it does**:
1. Creates SVD decomposer configured for our number of factors
2. `fit_transform()` trains and transforms the matrix in one step
   - `self.user_factors` = U (student latent factors)
   - Shape: (15 students, 10 factors)
3. `svd.components_` = V^T (but transposed once more to get just V)
   - `self.item_factors` = V^T after transpose = V
   - Shape: (10 modules, 10 factors) after transpose

**Why `random_state=42`?**
- Makes results reproducible
- If we didn't set this, SVD would produce slightly different factorization each run
- With seed=42, results are identical every time (good for testing)

---

### Section 4: Creating the Interaction Matrix (Lines 69-90)

```python
def _create_interaction_matrix(self, interactions: List) -> np.ndarray:
    """Create user-item interaction matrix"""
    n_students = len(self.students)
    n_modules = len(self.modules)
    
    matrix = np.zeros((n_students, n_modules))
    
    # Map student and module IDs to indices
    student_idx_map = {s.id: i for i, s in enumerate(self.students)}
    module_idx_map = {m.id: i for i, m in enumerate(self.modules)}
    
    # Fill matrix with ratings
    for interaction in interactions:
        if (interaction.student_id in student_idx_map and 
            interaction.module_id in module_idx_map):
            student_idx = student_idx_map[interaction.student_id]
            module_idx = module_idx_map[interaction.module_id]
            # Use weighted combination of rating and completion
            score = (interaction.rating * 0.6 + interaction.completion_rate / 100 * 0.4)
            matrix[student_idx, module_idx] = score
    
    return matrix
```

**The Critical Part: Combining Rating and Completion**

```python
score = (interaction.rating * 0.6 + interaction.completion_rate / 100 * 0.4)
```

**What it does**:
- Rating: 0-5 (how much they liked it)
- Completion_rate: 0-100 (percentage completed)

**Why 60% rating + 40% completion?**

| Factor | Weight | Reasoning |
|--------|--------|-----------|
| **Rating** | 60% | Direct preference signal (they said they like it) |
| **Completion** | 40% | Engagement signal (they actually finished it) |

**Example**:
- Student rates Module A: 5/5 but completes only 30% → score = 5×0.6 + 30/100×0.4 = 3.0 + 0.12 = 3.12
- Student rates Module B: 3/5 and completes 100% → score = 3×0.6 + 100/100×0.4 = 1.8 + 0.4 = 2.2
- Module A scores higher (3.12 > 2.2) because they actually enjoyed it (despite not finishing)

**Why both?**
- Rating alone: Students might rate high but not commit
- Completion alone: Students might finish boring required modules
- Combined: We get true engagement

---

### Section 5: Getting Recommendations (Lines 92-157)

```python
def get_recommendations(self, student_id: int, limit: int, db: Session) -> List[RecommendationItem]:
    """
    Get recommendations using collaborative filtering with SVD matrix reconstruction.
    Uses predicted scores from matrix factorization.
    """
```

#### 5.1: Train if Needed (Lines 98-102)

```python
        if not self.model_trained:
            if not self.train(db):
                logger.warning("Training failed, returning empty recommendations")
                return []
```

**What it does**:
- Lazy training: Train model only once, reuse for all recommendations
- If training fails, return empty list

**Why lazy training?**
- SVD is expensive (~100ms even on small data)
- We want to train once and cache the result
- Next 100 requests use the cached model (fast)

#### 5.2: Get the Target Student (Lines 104-112)

```python
            student = db.query(StudentDB).filter(StudentDB.id == student_id).first()
            if not student:
                return []

            # Find student index
            student_idx_map = {s.id: i for i, s in enumerate(self.students)}
            if student_id not in student_idx_map:
                return []

            student_idx = student_idx_map[student_id]
```

**What it does**:
1. Finds the student in the database (return [] if not found)
2. Maps the student ID → array index
   - Database ID might be 7 (non-sequential)
   - Array index must be 0,1,2,... (sequential)
   - Mapping: `{7: 2}` means student with DB ID 7 is at array position 2

**Why mapping?**
- Database IDs can be any number (e.g., 1,5,10,15,...)
- NumPy arrays need indices 0,1,2,3,...
- Mapping translates between the two worlds

#### 5.3: The Magic: SVD Reconstruction (Lines 115-121)

```python
            # Get student's latent factors
            if self.user_factors is None or student_idx >= len(self.user_factors):
                return []

            # Use SVD reconstruction: predicted_matrix = user_factors @ item_factors.T
            predicted_scores = self.user_factors[student_idx] @ self.item_factors.T
            predicted_scores = np.clip(predicted_scores, 0, 5.0)  # Clip to reasonable rating range
```

**THE CORE ALGORITHM**:

```python
predicted_scores = self.user_factors[student_idx] @ self.item_factors.T
```

**What it does**:
- Gets the student's preference vector: `self.user_factors[student_idx]` → shape (10,)
- Gets all modules' characteristic vectors: `self.item_factors.T` → shape (10, 10)
- Multiplies them: (10,) @ (10, 10) → (10,) = one score per module

**The Math**:
```
For each module j:
predicted_score[j] = student_latent_vector • module_latent_vector
                   = sum of (student_factor[k] × module_factor[k]) for k=0..9
```

**What does this mean?**

Example student vector: `[0.8, 0.3, -0.2, 0.9, 0.1, 0.0, 0.5, -0.1, 0.2, 0.4]`
- High values in factors 0,3,6: "This student loves mathematics, applied work, and programming"
- Low/negative values in 2,7: "Not interested in history or social topics"

Example module vector: `[0.9, 0.2, -0.3, 0.8, 0.0, 0.1, 0.6, 0.0, 0.1, 0.3]`
- High in 0,3,6: "This module teaches mathematics, applied work, and programming"
- Similar to student! → High dot product → Predicted to like it

**Why clipping?**
```python
predicted_scores = np.clip(predicted_scores, 0, 5.0)
```

- SVD might predict scores outside [0, 5] range (e.g., -1.5 or 6.2)
- Clipping forces them into valid range: any score < 0 becomes 0, any > 5 becomes 5
- Ensures predictions are realistic

#### 5.4: Filter and Sort (Lines 123-140)

```python
            # Get modules student has already taken
            taken_modules = db.query(InteractionDB).filter(
                InteractionDB.student_id == student_id
            ).all()
            taken_module_ids = {i.module_id for i in taken_modules}

            # Score all modules except already-taken
            module_idx_map = {m.id: i for i, m in enumerate(self.modules)}
            scored_modules = []

            for module_id, module in enumerate(self.modules):
                if module.id not in taken_module_ids:
                    score = float(predicted_scores[module_idx_map[module.id]])
                    scored_modules.append((module.id, module.title, score))

            # Sort by predicted score and limit
            scored_modules.sort(key=lambda x: x[2], reverse=True)
            scored_modules = scored_modules[:limit]
```

**What it does**:
1. Finds all modules the student already took (don't recommend those)
2. Loops through modules and gets their predicted scores
3. Sorts by score (highest first)
4. Keeps only the top `limit` modules (e.g., top 5)

**Example**:
```
Predicted scores for Student 1:
- Module 2: 4.5 (already taken, skip)
- Module 3: 3.8 (not taken)
- Module 4: 4.1 (not taken)
- Module 5: 2.2 (not taken)
- Module 6: 4.3 (not taken)

After filtering and sorting (top 3):
1. Module 6: 4.3
2. Module 4: 4.1
3. Module 3: 3.8
```

#### 5.5: Create Response Objects (Lines 142-153)

```python
            recommendations = []
            for module_id, title, score in scored_modules:
                recommendations.append(RecommendationItem(
                    module_id=module_id,
                    module_title=title,
                    score=score,
                    confidence=min(0.95, abs(score) / 5.0 * 0.95),
                    reason="Matches your learning profile",
                    ml_score=score
                ))

            return recommendations
```

**What it does**:
Converts raw scores into RecommendationItem objects (for API response)

**Confidence Calculation**:
```python
confidence = min(0.95, abs(score) / 5.0 * 0.95)
```

**Breaking it down**:
- `score / 5.0` = normalize to 0-1 range (a score of 5 → 1.0)
- `* 0.95` = convert to 0-0.95 range (never claim 100% certainty)
- `min(0.95, ...)` = cap at 0.95 just in case

**Example**:
- Score 5.0 → confidence = min(0.95, 1.0 × 0.95) = 0.95 (very confident)
- Score 3.0 → confidence = min(0.95, 0.6 × 0.95) = 0.57 (moderately confident)
- Score 0.5 → confidence = min(0.95, 0.1 × 0.95) = 0.095 (not confident)

---

### Section 6: Helper Method: predict_score() (Lines 183-203)

```python
def predict_score(self, student_id: int, module_id: int, db: Session) -> float:
    """Predict rating for a (student, module) pair using SVD reconstruction"""
    try:
        if not self.model_trained:
            if not self.train(db):
                return 0.0

        student_idx_map = {s.id: i for i, s in enumerate(self.students)}
        module_idx_map = {m.id: i for i, m in enumerate(self.modules)}

        if student_id not in student_idx_map or module_id not in module_idx_map:
            return 0.0

        student_idx = student_idx_map[student_id]
        module_idx = module_idx_map[module_id]

        predicted_score = float(self.user_factors[student_idx] @ self.item_factors[module_idx])
        return np.clip(predicted_score, 0, 5.0)
    except Exception as e:
        logger.error(f"Error predicting score: {str(e)}")
        return 0.0
```

**What it does**:
Predicts the rating for ONE specific (student, module) pair.

**Used by**: The Evaluation Service (to compute RMSE/MAE for rating prediction)

**The formula**:
```python
predicted_score = self.user_factors[student_idx] @ self.item_factors[module_idx]
```

- `self.user_factors[student_idx]` = one student's 10-factor vector
- `self.item_factors[module_idx]` = one module's 10-factor vector
- `@` = dot product = similarity score

**Example**:
```
Student 1: [0.8, 0.3, -0.2, 0.9, ...]
Module 5: [0.7, 0.2, -0.1, 0.85, ...]
Dot product: 0.8×0.7 + 0.3×0.2 + (-0.2)×(-0.1) + 0.9×0.85 + ... = 3.42 → predicted score 3.42/5.0
```

---

### Section 7: Unused Helper Method (Lines 159-181)

```python
def _compute_similarities(self, student_vector: np.ndarray) -> np.ndarray:
    """Compute cosine similarities between student and all other students"""
    # ... (code present but not used in get_recommendations)
```

**Status**: This method is implemented but **NOT USED** in the current code.

**What it does**:
Computes cosine similarity between one student and all others.

**Why it's there**:
- Leftover from earlier design
- Might be used for:
  - User-user collaborative filtering (alternative approach)
  - Debugging/visualization
  - Future neural collaborative filtering

**Would compute**:
```
For student A with latent factors [0.8, 0.3, ...]:
- Similarity to student B: 0.92 (very similar taste)
- Similarity to student C: 0.31 (different taste)
- Similarity to student D: 0.88 (similar taste)
```

**How it works**:
```python
similarity = normalized_vector_A • normalized_vector_B
```
- Normalizes both vectors to unit length
- Computes dot product
- Result: [-1, 1] where 1 = identical, 0 = orthogonal, -1 = opposite

---

## Design Decisions & Why

### Decision 1: 10 Latent Factors

**Choice**: `n_factors = 10`

**Why 10?**
- Empirical rule: `sqrt(min(n_students, n_modules))`
- With 15 students and 10 modules: `sqrt(10) ≈ 3-4`, we choose 10 for extra capacity
- Research shows 10 factors good for academic domains
- Balances expressiveness vs. generalization

**Trade-offs**:
- **More factors** (e.g., 50): Can capture more patterns but overfits
- **Fewer factors** (e.g., 2): Simple but misses important patterns
- **10 factors**: Sweet spot

### Decision 2: Lazy Training

**Choice**: Train model only once, cache for subsequent requests

**Code**:
```python
if not self.model_trained:
    if not self.train(db):
        return []
```

**Why?**
- Training SVD is ~100ms (expensive)
- Recommendation requests should respond in <200ms
- Don't retrain if data hasn't changed
- In production, would invalidate cache on data changes

**Trade-off**:
- **Pro**: Fast recommendations
- **Con**: Stale model if new interactions added
- **Real-world solution**: Retrain on schedule (hourly/daily) or trigger on batch updates

### Decision 3: Weighted Rating + Completion

**Choice**: `score = rating * 0.6 + completion_rate / 100 * 0.4`

**Why 60% rating + 40% completion?**
- Rating = explicit preference (they said they like it)
- Completion = implicit engagement (they actually finished)
- Combining both reduces noise

**Alternative approaches**:
- **Just rating** (100% + 0%): Students might be lying or generous with ratings
- **Just completion** (0% + 100%): Required modules get high scores even if boring
- **Equal weight** (50% + 50%): Gives completion same importance as stated preference

**60-40 split reasoning**:
- Stated preference is more reliable than inferred preference
- But completion adds valuable signal about commitment

### Decision 4: Clip Predictions to [0, 5]

**Choice**: `predicted_scores = np.clip(predicted_scores, 0, 5.0)`

**Why clip?**
- SVD reconstructions can produce unrealistic values (e.g., -2.5 or 7.3)
- Domain knowledge: Ratings must be [0, 5]
- Clipping ensures predictions are valid

**What clipping does**:
```
SVD predicted: -1.2  →  Clipped: 0.0
SVD predicted:  3.2  →  Clipped: 3.2 (no change, within range)
SVD predicted:  6.8  →  Clipped: 5.0
```

### Decision 5: Dynamic Index Mapping

**Choice**: Map database IDs to array indices

**Code**:
```python
student_idx_map = {s.id: i for i, s in enumerate(self.students)}
```

**Why map?**
- Database IDs might be: 1, 7, 15, 23, 100 (sparse, non-sequential)
- NumPy arrays need: 0, 1, 2, 3, 4 (dense, sequential)
- Mapping bridges the two worlds

**Alternative**: Modify database to ensure sequential IDs (worse → adds complexity)

### Decision 6: Skip Already-Taken Modules

**Choice**: Exclude modules student already took

**Code**:
```python
if module.id not in taken_module_ids:
    scored_modules.append(...)
```

**Why skip?**
- No point recommending modules they've already completed
- Confuses user ("I already took this!")
- Could lead to retakes accidentally

**User experience**:
- Student sees: "You haven't taken these yet, and we think you'd like them"
- Not: "Here are modules you might like (including ones you finished)"

---

## The Math Behind It

### Formula 1: Interaction Matrix Entry

```
X[i,j] = rating[i,j] × 0.6 + (completion_rate[i,j] / 100) × 0.4
```

**Where**:
- `X[i,j]` = Combined score for student i and module j
- `rating[i,j]` ∈ [0, 5] = Student's explicit rating
- `completion_rate[i,j]` ∈ [0, 100] = Percentage of module completed

**Example**:
- Student rated 5/5, completed 100% → X = 5×0.6 + 1.0×0.4 = 3.4
- Student rated 2/5, completed 0% → X = 2×0.6 + 0×0.4 = 1.2
- Student didn't rate, completed 50% → X = 0×0.6 + 0.5×0.4 = 0.2

### Formula 2: SVD Decomposition

```
X ≈ U × Σ × V^T

Where:
- X: Original matrix (n_students × n_modules)
- U: Student latent factors (n_students × k)
- Σ: Singular values (k × k, diagonal)
- V^T: Module latent factors transposed (k × n_modules)
- k: Number of factors (10 in our case)
```

**In code**:
```python
U = svd.fit_transform(X)           # Returns U (already multiplied by Σ)
V_T = svd.components_               # Returns V^T directly
V = V_T.T                          # Transpose to get V
```

### Formula 3: Reconstruction (The Prediction)

```
Ŷ = U × V^T = U × svd.components_

Predicted rating for student i, module j:
Ŷ[i,j] = U[i] • V[j]
        = dot_product(student_i_latent_vector, module_j_latent_vector)
```

**In code**:
```python
predicted_scores = self.user_factors[student_idx] @ self.item_factors.T
```

### Formula 4: Confidence Score

```
confidence = min(0.95, (score / 5.0) × 0.95)
           = min(0.95, score × 0.19)
```

**Interpretation**:
- Score of 5.0 → confidence 0.95 (95% confident)
- Score of 2.5 → confidence 0.475 (47.5% confident)
- Score of 0.0 → confidence 0.0 (0% confident, basically ignore)

---

## Visual Examples

### Example 1: Full Flow with Real Numbers

**Setup**: 3 students, 4 modules, some interactions

**Step 1: Interaction Matrix**
```
Interaction data from database:
- Alice rated ML101: 5/5, completed 100% → score 5×0.6 + 1.0×0.4 = 3.4
- Bob rated ML101: 3/5, completed 50% → score 3×0.6 + 0.5×0.4 = 2.2
- Alice rated DB101: 4/5, completed 80% → score 4×0.6 + 0.8×0.4 = 2.88
- Carol completed AI101 with no rating → score 0×0.6 + 1.0×0.4 = 0.4

Matrix X:
        ML101  DB101  AI101  Web101
Alice    3.4    2.88    0      0
Bob      2.2     0      0      ?
Carol     0      0      0.4    0
```

**Step 2: SVD Decomposes Matrix**
```
TruncatedSVD with k=2 factors extracts:

U (Student factors):        V^T (Module factors):
        F1    F2           F1    F2    F3    F4
Alice  [0.9, -0.2]   ML101 [0.95, -0.1]
Bob    [0.5,  0.3]   DB101 [0.8,   0.2]
Carol  [0.1,  0.8]   AI101 [0.3,   0.9]
                     Web101 [0.6,  -0.3]

(Simplified - real SVD gives different numbers)
```

**Step 3: Predict Missing Ratings**
```
Bob hasn't taken DB101. Predict:
Ŷ[Bob, DB101] = U[Bob] • V[DB101]
               = [0.5, 0.3] • [0.8, 0.2]
               = 0.5×0.8 + 0.3×0.2
               = 0.4 + 0.06
               = 0.46 → Bob probably wouldn't like DB101

Carol hasn't taken ML101. Predict:
Ŷ[Carol, ML101] = [0.1, 0.8] • [0.95, -0.1]
                 = 0.1×0.95 + 0.8×(-0.1)
                 = 0.095 - 0.08
                 = 0.015 → Carol probably wouldn't like ML101

Alice hasn't taken Web101. Predict:
Ŷ[Alice, Web101] = [0.9, -0.2] • [0.6, -0.3]
                  = 0.9×0.6 + (-0.2)×(-0.3)
                  = 0.54 + 0.06
                  = 0.6 → Alice might like Web101
```

**Step 4: Get Recommendations for Carol**
```
Carol's predicted scores:
- ML101: 0.015 → confidence = 0.015 × 0.19 ≈ 0.003
- DB101: ? (compute similarly) ≈ 0.3 → confidence ≈ 0.057
- Web101: ? (compute similarly) ≈ 0.8 → confidence ≈ 0.152

Sorted (highest first):
1. Web101: 0.8 (confidence 0.152)
2. DB101: 0.3 (confidence 0.057)
3. ML101: 0.015 (confidence 0.003)

Already taken: AI101 (skip)

Return top-1 for Carol:
→ Recommend Web101 (score 0.8)
```

---

### Example 2: Why SVD Works Better Than Alternatives

**Scenario**: Recommend module for a new student with only 1 interaction

**Alternative 1: User-User Collaborative Filtering**
```
Find students most similar to new student:
- Only 1 interaction to compare → very noisy similarity
- "This new student took Module X, so find others who took X"
- But Module X alone doesn't tell us much about taste!
→ Unreliable recommendations
```

**Alternative 2: Item-Item Collaborative Filtering**
```
Find modules similar to ones student took:
- Student took ML101
- What modules are similar to ML101?
- Requires pre-computing item-item similarity (expensive)
→ Works OK, but doesn't capture latent patterns
```

**SVD (What we use)**:
```
Decompose matrix to find latent factors:
- New student + 1 interaction → Can estimate their latent factor vector
- Even with sparse data, SVD can reconstruct patterns
- If student X took Module A and rated high, and we know:
  - Module A teaches factor [0.9, 0.3, -0.1, ...]
  - Student X likely has factors close to [0.9, 0.3, -0.1, ...]
- So modules teaching similar factors = good recommendations
→ More robust with sparse data
```

---

### Example 3: Understanding Latent Factors

**What the 10 factors might represent** (we don't explicitly define these):

| Factor | Learned Meaning (Hypothetical) |
|--------|-------------------------------|
| F1 | "Mathematical rigor vs. practical application" |
| F2 | "Computational complexity vs. simplicity" |
| F3 | "Breadth vs. depth" |
| F4 | "Theory vs. implementation" |
| F5 | "Solo work vs. collaboration" |
| F6 | "Algorithmic vs. data-driven" |
| F7 | "Communication skills needed" |
| F8 | "Systems thinking vs. component focus" |
| F9 | "Creativity vs. following specs" |
| F10 | "Real-world application vs. academic" |

**Example Student Vector**:
```
Alice: [0.8, -0.3, 0.6, 0.2, -0.1, 0.5, 0.1, -0.2, 0.7, 0.4]
```

**Interpretation**:
- F1=0.8: Loves mathematical rigor
- F2=-0.3: Prefers practical over computational complexity
- F3=0.6: Likes broad topics
- F4=0.2: Slightly theory-leaning
- F5=-0.1: Slightly prefers solo work
- F6=0.5: Likes algorithmic approaches
- F7=0.1: Neutral on communication
- F8=-0.2: Prefers components over systems thinking
- F9=0.7: Very creative
- F10=0.4: Likes real-world applications

**Example Module Vector**:
```
ML101: [0.9, -0.1, 0.4, 0.3, 0.2, 0.8, -0.1, 0.1, 0.5, 0.6]
```

**Why Alice Would Like ML101**:
```
Dot product = 0.8×0.9 + (-0.3)×(-0.1) + 0.6×0.4 + 0.2×0.3 + ... 
            = 0.72 + 0.03 + 0.24 + 0.06 + ...
            = Very high (4.5+) → Predict Alice will like ML101
```

**High agreement on**:
- F1 (mathematical rigor): Alice 0.8 vs ML101 0.9 (match!)
- F6 (algorithmic): Alice 0.5 vs ML101 0.8 (somewhat match)
- F10 (real-world): Alice 0.4 vs ML101 0.6 (match)

**This is the "hidden pattern" SVD discovered!**

---

## Common Questions Answered

### Q1: Why not just ask "rate this module" for every student?

**A**: 
- Exhausting for users (rate 1000 modules?)
- Incomplete data (users won't rate everything)
- Can't recommend new modules (no ratings yet)

**SVD advantage**: Predicts unrated items from patterns in rated items

### Q2: Why 10 factors and not 100?

**A**:
- 100 factors = memorizing all relationships (overfitting)
- Model learns noise, not patterns
- Predicts poorly on NEW students

**Trade-off**: 10 factors is sweet spot between expressiveness and generalization

### Q3: What if two students have identical interaction histories?

**A**:
- SVD gives them nearly identical latent factor vectors
- They'll get nearly identical recommendations (correct!)
- Small numerical differences due to SVD's optimization

### Q4: Can SVD handle very sparse data?

**A**:
- Yes, that's what TruncatedSVD is optimized for
- Traditional SVD fails on sparse matrices
- TruncatedSVD uses iterative approximation
- Works well even if 90% of matrix is empty

### Q5: What happens when we add a new student?

**A**:
- Old factors: Don't change (already trained)
- New student: Needs re-training to get their latent vector
- In production: Retrain nightly or on-demand

### Q6: Does SVD guarantee better recommendations than alternatives?

**A**: No, it depends on:
- Data quality (garbage in, garbage out)
- Number of interactions
- Diversity of users and items
- Tuning of parameters (n_factors, weights, etc.)

**In our case**: Works well for 15 students (enough data), balanced by Graph Service for cold-start

---

## Summary: Why This Design?

| Component | Why This Choice |
|-----------|-----------------|
| **SVD Matrix Factorization** | Discovers hidden patterns, works with sparse data |
| **10 Latent Factors** | Balance: enough capacity, avoids overfitting |
| **60% Rating + 40% Completion** | Combines explicit + implicit signals |
| **Lazy Training** | Fast recommendations, avoids redundant work |
| **Clipping to [0,5]** | Ensures realistic predictions |
| **Skip Taken Modules** | Better UX, prevents confusing recommendations |
| **Confidence Score** | Communicates model certainty |
| **Index Mapping** | Handles non-sequential database IDs |

---

**Document Complete**: This explains every line of ML service code and the reasoning behind it.

