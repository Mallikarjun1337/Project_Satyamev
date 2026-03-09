# Backend - Satyamev Vijayate

Python backend for fake news verification using FastAPI.

## Structure

- `src/api_gateway.py` - FastAPI application and endpoints
- `src/verification_engine.py` - Orchestrates multi-modal analysis
- `src/analyzers/` - Specialized analyzers for each content type
  - `text_analyzer.py` - Text content analysis
  - `image_analyzer.py` - Image content analysis
  - `video_analyzer.py` - Video content analysis
- `src/models.py` - Pydantic data models

## Setup

### Create Virtual Environment
```bash
python -m venv venv
```

### Activate Virtual Environment
- Windows: `venv\Scripts\activate`
- Linux/Mac: `source venv/bin/activate`

### Install Dependencies
```bash
pip install -r requirements.txt
pip install -e .
```

## Development

### Run Development Server
```bash
uvicorn src.api_gateway:app --reload
```

The API will be available at `http://localhost:8000`

### API Documentation
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Testing

### Run All Tests
```bash
pytest
```

### Run with Coverage
```bash
pytest --cov=src --cov-report=html
```

### Run Specific Test File
```bash
pytest tests/test_verification_engine.py
```

## Testing Framework

- **pytest**: Testing framework
- **hypothesis**: Property-based testing library
- **pytest-asyncio**: Async testing support
- **pytest-mock**: Mocking utilities

## Coverage Goals

- Minimum 90% code coverage
- 100% coverage of classification rules
- All error paths must have explicit tests

## API Endpoints

### POST /api/v1/verify
Verify content for fake news

**Request:**
```json
{
  "content_type": "text",
  "content_data": "Content to verify",
  "language": "en",
  "user_id": "user123"
}
```

**Response:**
```json
{
  "id": "uuid",
  "timestamp": 1234567890,
  "content_type": "text",
  "credibility_score": 75.5,
  "classification": "Verified",
  "confidence": 0.85,
  "explanation": "Analysis explanation",
  "sources": [],
  "analysis_details": {}
}
```

### POST /api/v1/report
Report incorrect verification results

### GET /api/v1/health
Health check endpoint
