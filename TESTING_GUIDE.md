# Frontend & Full System Testing Guide

## System Setup

The system is now ready for end-to-end testing with a React frontend. Here's what you have:

### Backend (FastAPI)
- **Port**: 8000
- **Status**: Running with sample data (15 students, 10 courses)
- **Endpoints**: 
  - `http://localhost:8000/health` - Health check
  - `http://localhost:8000/docs` - Interactive API documentation

### Frontend (React + Vite)
- **Port**: 5173
- **URL**: `http://localhost:5173`
- **Features**: Login, Dashboard, Course Search, Course Details with Progress Tracking

---

## Testing Workflows

### 1. **Login Flow**
1. Open `http://localhost:5173` in your browser
2. Try student IDs **1-15** (sample data)
3. Example: Enter `1` and click "Login"

### 2. **Dashboard Features**

**Left Column: Recommended Courses**
- Shows top recommended courses
- Each card has: title, score (0-5), confidence, reason

**Right Column Top: All Courses Search**
- Search all 10 courses by name or code
- Click to view course details

**Right Column Bottom: Coefficients Box**
- Phase badge: Cold Start / Transition / Mature
- α (Graph weight) and β (ML weight) 
- Interaction count
- Visual weight bars

### 3. **Cold-Start to Mature Progression**

**Phase 1: Cold Start (< 5 interactions)**
- α = 0.8, β = 0.2 (Graph dominates)
- Badge: 🔴 Red

**Phase 2: Transition (5-19 interactions)**
- α gradually decreases, β gradually increases
- Badge: 🟠 Orange

**Phase 3: Mature (≥ 20 interactions)**
- α = 0.3, β = 0.7 (ML dominates)
- Badge: 🟢 Green

### 4. **Course Detail Page**
- View course info
- Set rating (0-5 slider)
- Set completion (0-100% slider)
- Click "Save Progress"
- Return to home and refresh to see weights update

### 5. **Search Functionality**
- **Left**: Search recommended courses
- **Right**: Search all courses
- By title or code (case-insensitive)

---

## Key Test Scenarios

### Test 1: Cold Start Verification
```
Login as student 1
Expected: Phase = "Cold Start", α ≈ 0.8, β ≈ 0.2
```

### Test 2: Dynamic Weight Transition
```
1. Login as student 1
2. Add 5+ interactions (visit courses, set rating + completion)
3. Refresh home each time
4. Watch phase badge change: Cold Start → Transition → Mature
5. Watch coefficients shift: α decreases, β increases
```

### Test 3: Recommendations Update
```
1. Note initial recommendations
2. Visit courses and give ratings
3. Refresh recommendations
4. See new courses appear based on your interactions
```

### Test 4: Search All 10 Courses
```
Available courses:
- CS101: Introduction to Python
- CS201: Advanced Python
- DS101: Data Science Fundamentals
- AI101: Machine Learning Basics
- AI201: Advanced Machine Learning
- WEB201: Web Development with FastAPI
- DB101: Database Design
- CLOUD201: Cloud Computing with AWS
- NLP301: Natural Language Processing
- DV101: Data Visualization
```

---

## API Endpoints

### Login
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"student_id": 1}'
```

### Get Recommendations with Coefficients
```bash
curl "http://localhost:8000/recommendations?student_id=1&limit=10"
```

### Save Interaction
```bash
curl -X POST http://localhost:8000/students/1/modules/1/interact \
  -H "Content-Type: application/json" \
  -d '{"rating": 4.5, "completion_rate": 75}'
```

### Interactive API Docs
Visit `http://localhost:8000/docs`

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Login fails | Use student IDs 1-15 |
| No recommendations | Click "Refresh Recommendations" |
| CORS errors | Ensure both servers running (8000 & 5173) |
| Can't find course | Try searching by code (e.g., "CS101") |
| Progress not saved | Check browser console, verify inputs not 0 |

---

## Running Backend Tests

```bash
# All tests
pytest tests/test_services.py -v

# With coverage
pytest tests/test_services.py -v --cov=services
```

---

Enjoy testing! 🚀
