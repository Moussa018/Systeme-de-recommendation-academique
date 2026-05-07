# Academic Recommendation System - Hybrid Approach

A robust hybrid recommendation system combining **Knowledge Graphs** and **Machine Learning** to suggest academic modules and resources to students.

## System Architecture

### Core Components

1. **Graph Service (Knowledge Graph)** - RDF/OWL based content-based filtering
   - Manages academic ontology (students, modules, competencies)
   - Handles prerequisite relationships and semantic reasoning
   - Uses SPARQL queries for intelligent matching
   - Primary method for cold-start problems

2. **ML Service (Collaborative Filtering)** - SVD-based and neural approaches
   - Implements matrix factorization (SVD) as baseline
   - Analyzes student interaction patterns
   - Discovers hidden patterns in behavior
   - Primary method for mature student profiles

3. **Fusion Service** - Dynamic hybrid approach
   - Combines both methods with adaptive weighting
   - Cold-start profile: 80% Graph, 20% ML
   - Mature profile: 30% Graph, 70% ML
   - Calculates confidence scores for recommendations

4. **FastAPI REST API** - Microservices architecture
   - Single entry point: `/recommendations`
   - Modular service design for scalability
   - Health checks and performance metrics

## Technology Stack

### Core Technologies
- **Language**: Python 3.9+
- **API Framework**: FastAPI with Uvicorn
- **Database**: PostgreSQL (SQLite for development)
- **Knowledge Graph**: RDFLib + SPARQL

### ML & Data Science
- **Collaborative Filtering**: scikit-learn (SVD)
- **Deep Learning**: PyTorch (for Neural Collaborative Filtering)
- **Data**: pandas, numpy

### Testing & Development
- **Testing**: pytest
- **Data Generation**: Faker
- **ORM**: SQLAlchemy

## Installation

### Prerequisites
- Python 3.9 or higher
- pip package manager
- Virtual environment (recommended)

### Setup Steps

```bash
# 1. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Initialize database and generate sample data
python data_generator.py

# 4. Run the application
python main.py
```

The API will be available at `http://localhost:8000`

## API Endpoints

### Health & Metrics
- `GET /health` - System health check
- `GET /metrics` - Performance metrics

### Recommendations
- `GET /recommendations?student_id=1&limit=5` - Hybrid recommendations
- `GET /recommendations/graph-only?student_id=1&limit=5` - Graph-based only
- `GET /recommendations/ml-only?student_id=1&limit=5` - ML-based only

### Data Management
- `POST /students` - Create new student
- `POST /modules` - Create new module

## API Examples

### Get Hybrid Recommendations
```bash
curl "http://localhost:8000/recommendations?student_id=1&limit=5"
```

Response:
```json
{
  "student_id": 1,
  "recommendations": [
    {
      "module_id": 3,
      "module_title": "Data Science Fundamentals",
      "score": 0.85,
      "confidence": 0.92,
      "reason": "Aligns with your competencies",
      "graph_score": 0.80,
      "ml_score": 0.90
    }
  ],
  "timestamp": "2024-01-15T10:30:00",
  "method": "hybrid"
}
```

### Create a Student
```bash
curl -X POST "http://localhost:8000/students" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john@example.com",
    "major": "Computer Science",
    "year": 2
  }'
```

## Project Structure

```
academic-recommender/
├── main.py                    # FastAPI application entry point
├── database.py                # Database configuration
├── models.py                  # SQLAlchemy ORM models
├── schemas.py                 # Pydantic request/response schemas
├── data_generator.py          # Sample data generation
├── requirements.txt           # Python dependencies
├── README.md                  # This file
│
├── services/                  # Business logic services
│   ├── __init__.py
│   ├── graph_service.py       # Knowledge Graph service
│   ├── ml_service.py          # ML/Collaborative filtering service
│   └── fusion_service.py      # Hybrid fusion service
│
└── tests/                     # Unit tests
    ├── __init__.py
    └── test_services.py       # Service tests
```

## Database Schema

### Core Tables
- **students**: Student profiles and metadata
- **modules**: Academic modules/courses
- **competencies**: Skills and knowledge areas
- **student_competencies**: Student proficiency levels
- **interactions**: Student-module interactions (ratings, completion)
- **prerequisites**: Module dependency relationships

## Evaluation Metrics

The system measures performance using:

1. **Precision & Recall** - Relevance of recommendations
2. **F1-Score** - Balance between precision and recall
3. **RMSE / MAE** - Prediction accuracy for ratings
4. **NDCG** - Quality of ranked recommendations

## Configuration

### Environment Variables
```bash
DATABASE_URL=postgresql://user:password@localhost/academic_db
DEBUG=true
```

### Weight Configuration
- **Cold Start** (< 5 interactions): α=0.8, β=0.2
- **Transition** (5-20 interactions): Dynamic scaling
- **Mature** (> 20 interactions): α=0.3, β=0.7

## Running Tests

```bash
# Run all tests
pytest tests/

# Run with verbose output
pytest tests/ -v

# Run specific test
pytest tests/test_services.py::TestGraphService -v
```

## Sample Data

The system includes a data generator that creates:
- 15 students across different majors and years
- 10 academic modules at various difficulty levels
- 8 competency areas
- Realistic interaction patterns (ratings, completion rates)
- Prerequisite relationships

Generate sample data:
```bash
python data_generator.py
```

## Usage Examples

### Python Client Example
```python
import requests

# Get recommendations for student 1
response = requests.get(
    "http://localhost:8000/recommendations",
    params={"student_id": 1, "limit": 5}
)

recommendations = response.json()
for rec in recommendations["recommendations"]:
    print(f"{rec['module_title']}: {rec['score']:.2f} (confidence: {rec['confidence']:.2f})")
```

### Interactive API Documentation
Visit `http://localhost:8000/docs` for interactive Swagger UI
Visit `http://localhost:8000/redoc` for ReDoc documentation

## Performance Optimization

### Caching Strategy
- Cache SPARQL query results
- Store trained ML models in memory
- Use database indices on frequently queried fields

### Scalability
- Microservices architecture allows independent scaling
- Graph service can be offloaded to dedicated RDF store
- ML models can be distributed across worker processes

## Troubleshooting

### Database Issues
```bash
# Reset database (development only)
rm academic_recommender.db
python data_generator.py
```

### Model Training Issues
If ML service fails to train:
1. Ensure sufficient interaction data (at least 10 interactions)
2. Check data quality and missing values
3. Verify matrix factorization parameters

### API Connection Issues
```bash
# Check if API is running
curl http://localhost:8000/health

# Check API logs
tail -f app.log
```

## Development Roadmap

- [ ] Neural Collaborative Filtering (NCF) implementation
- [ ] Real-time learning and model updates
- [ ] Multi-language support
- [ ] Advanced filtering (by difficulty, credits, etc.)
- [ ] Recommendation explanations
- [ ] A/B testing framework
- [ ] PostgreSQL integration guide
- [ ] Containerization (Docker)
- [ ] Kubernetes deployment manifests

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/improvement`)
3. Commit changes (`git commit -am 'Add improvement'`)
4. Push to branch (`git push origin feature/improvement`)
5. Create Pull Request

## License

MIT License - See LICENSE file for details

## Documentation References

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [RDFLib Documentation](https://rdflib.readthedocs.io/)
- [scikit-learn Collaborative Filtering](https://scikit-learn.org/)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/)

## Support

For issues, questions, or suggestions:
- Create an issue in the repository
- Check existing issues for solutions
- Review API documentation at `/docs`

---

**Version**: 1.0.0  
**Last Updated**: January 2024  
**Status**: Production Ready
