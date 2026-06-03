# How to Run the Academic Recommendation System

## Prerequisites
- Python 3.8+
- Node.js 16+
- pip and npm

## Installation (One-time)

### Backend Setup
```bash
pip install -r requirements.txt --break-system-packages
```

### Frontend Setup
```bash
cd frontend
npm install
cd ..
```

## Running the System

### Option 1: Run Both Servers (Recommended)

**Terminal 1 - Backend:**
```bash
python main.py
```
Backend will start on `http://localhost:8000`

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```
Frontend will start on `http://localhost:5173`

### Option 2: Run in Background

**Run backend in background:**
```bash
python main.py > logs/backend.log 2>&1 &
```

**Run frontend in background:**
```bash
cd frontend && npm run dev > ../logs/frontend.log 2>&1 &
```

## Access the System

- **Frontend**: Open `http://localhost:5173` in your browser
- **Backend API Docs**: Visit `http://localhost:8000/docs`
- **Health Check**: `curl http://localhost:8000/health`

## Sample Login Credentials

Use student IDs **1-15** (sample data generated automatically)

Example: Enter `5` and login

## Useful Commands

### Generate Fresh Sample Data
```bash
rm -f academic_recommender.db ontology.rdf
python data_generator.py
```

### Run Tests
```bash
pytest tests/test_services.py -v
```

### Check Backend Logs
```bash
tail -f logs/backend.log  # if running in background
```

### Stop Servers
```bash
# Kill all Python processes (backend)
pkill -f "python main.py"

# Kill all Node processes (frontend)
pkill -f "npm run dev"
```

## Project Structure

```
.
├── main.py                    # FastAPI backend
├── models.py                  # SQLAlchemy models
├── schemas.py                 # Pydantic schemas
├── database.py                # Database config
├── data_generator.py          # Generate sample data
├── services/
│   ├── graph_service.py       # Knowledge Graph (RDF/SPARQL)
│   ├── ml_service.py          # ML (SVD-based collaborative filtering)
│   ├── fusion_service.py      # Hybrid recommendations
│   └── evaluation_service.py  # Evaluation metrics
├── tests/
│   └── test_services.py       # Unit tests (18 tests)
├── frontend/                  # React app
│   ├── src/
│   │   ├── pages/            # Login, Home, CourseDetail
│   │   ├── components/       # RecommendationCard, Coefficients
│   │   ├── styles/           # CSS for each page
│   │   └── api.js            # Axios API wrapper
│   └── package.json
├── academic_recommender.db    # SQLite database (auto-generated)
├── ontology.rdf              # RDF ontology (auto-generated)
└── TESTING_GUIDE.md          # Detailed testing instructions
```

## Troubleshooting

**Backend won't start:**
- Check Python version: `python --version`
- Install missing packages: `pip install -r requirements.txt --break-system-packages`

**Frontend won't start:**
- Check Node version: `node --version`
- Clear node_modules: `cd frontend && rm -rf node_modules && npm install`

**CORS errors:**
- Ensure backend is running on 8000 and frontend on 5173
- Check browser console (F12) for specific error

**Database issues:**
- Delete and regenerate: `rm -f academic_recommender.db && python data_generator.py`

## For Development

### Hot Reload
- **Frontend**: Changes reload automatically in browser
- **Backend**: Restart the server to see changes

### Adding New Features
1. Modify backend (FastAPI endpoints)
2. Update frontend (React components)
3. Test via browser and API docs

## Production Deployment

For production:
1. Replace SQLite with PostgreSQL
2. Update `DATABASE_URL` in `database.py`
3. Set `--break-system-packages` is only for development
4. Use a proper WSGI server (gunicorn) instead of uvicorn
5. Build frontend: `cd frontend && npm run build`
6. Serve frontend static files from backend

See documentation files for more details on architecture and implementation.
