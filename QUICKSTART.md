# Quick Start Guide

## 5-Minute Setup

### Option 1: Local Development (Recommended for Testing)

```bash
# 1. Clone/Extract project
cd academic-recommender

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Generate sample data
python data_generator.py

# 5. Start the API
python main.py
```

Visit: http://localhost:8000/docs (interactive API docs)

### Option 2: Docker (Production-Ready)

```bash
# 1. Ensure Docker and Docker Compose are installed
docker --version
docker-compose --version

# 2. Start the full stack
docker-compose up -d

# 3. Check status
docker-compose ps
docker-compose logs -f api
```

Visit: http://localhost:8000/docs

## Testing the API

### Using curl

```bash
# Health check
curl http://localhost:8000/health

# Get recommendations for student 1
curl "http://localhost:8000/recommendations?student_id=1&limit=5"

# Get metrics
curl http://localhost:8000/metrics
```

### Using Python

```bash
python example_usage.py
```

## Common Tasks

### Generate New Sample Data
```bash
python data_generator.py
```

### Run Tests
```bash
pytest tests/ -v
```

### View API Documentation
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Reset Database (Development Only)
```bash
rm academic_recommender.db
python data_generator.py
```

### Stop Docker Services
```bash
docker-compose down
```

## First Recommendations Query

Once running, try:
```bash
curl "http://localhost:8000/recommendations?student_id=1&limit=3"
```

Expected response includes:
- Module recommendations
- Confidence scores
- Graph and ML component scores
- Reasoning for each recommendation

## Troubleshooting

### Port 8000 Already in Use
Change port in `docker-compose.yml` or run on different port:
```bash
uvicorn main:app --port 8001
```

### Database Connection Error
Ensure database URL in `.env` is correct:
```bash
# For SQLite (default)
DATABASE_URL=sqlite:///./academic_recommender.db

# For PostgreSQL
DATABASE_URL=postgresql://user:password@localhost/academic_recommender
```

### Module Import Error
```bash
# Reinstall dependencies
pip install --upgrade -r requirements.txt
```

## Next Steps

1. **Explore the API**: Visit http://localhost:8000/docs
2. **Create test data**: Use `/students` and `/modules` endpoints
3. **Test different methods**: Compare `/recommendations`, `/recommendations/graph-only`, `/recommendations/ml-only`
4. **Run tests**: `pytest tests/ -v`
5. **Read full docs**: See README.md

## Project Structure Overview

```
academic-recommender/
├── main.py                  ← Run this to start
├── data_generator.py        ← Run to generate sample data
├── example_usage.py         ← API usage examples
├── requirements.txt         ← Dependencies
├── docker-compose.yml       ← For Docker deployment
└── services/                ← Core recommendation engines
```

## Support & Questions

- Check README.md for full documentation
- Review example_usage.py for API examples
- Visit API docs at http://localhost:8000/docs
- Check logs for error details

---

**Ready to go!** The system is now running and ready to process recommendation requests.
