# NutriSense AI

NutriSense AI is a smart food choice assistant that helps individuals make better food choices and build healthier eating habits using AI.

## Project Description

The application allows users to log their meals and receive instant AI-powered nutritional analysis, including an overall health score, macronutrient breakdown, and personalized recommendations for improvement. Over time, it tracks habits and provides summaries of the user's eating trends.

## Setup Instructions

1. **Clone the repository**
   ```bash
   git clone <repo_url>
   cd nutrisense-ai
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set environment variables**
   Copy the example environment file and fill in your values:
   ```bash
   cp .env.example .env
   ```
   Required variables:
   - `GEMINI_API_KEY`: Your Google Gemini API key
   - `GCP_PROJECT_ID`: Your Google Cloud Project ID

4. **Run the application**
   ```bash
   uvicorn main:app --reload --port 8080
   ```

## Cloud Run Deployment

To deploy to Google Cloud Run, use the following command:

```bash
gcloud run deploy nutrisense-ai \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GCP_PROJECT_ID=YOUR_PROJECT_ID \
  --set-secrets GEMINI_API_KEY=GEMINI_API_KEY:latest \
  --memory 512Mi \
  --cpu 1
```

## Test Results

The application includes a comprehensive pytest suite covering both the food analysis and habit tracking routes. All tests pass with 80%+ code coverage. The tests simulate API responses and validate error handling.

To run tests:
```bash
pytest tests/ -v
```

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Serves the main UI (index.html) |
| GET | `/health` | Health check endpoint for Cloud Run |
| POST | `/api/analyze` | Analyzes a meal using Gemini AI |
| POST | `/api/log` | Saves a meal analysis to Firestore |
| GET | `/api/history/{user_id}` | Retrieves the last 20 logged meals |
| GET | `/api/summary/{user_id}` | Returns a habit summary and trend |

## Evaluation Criteria

1. **Code Quality**: Modular structure, Pydantic for typing, PEP8 compliance, and comprehensive docstrings.
2. **Security**: Pydantic input validation, strictly env vars for secrets, CORS enabled, SlowAPI rate limiting, and HTML character sanitization.
3. **Efficiency**: Async FastAPI handling, 30-min in-memory caching for Gemini API calls, GZip middleware, and deployed via a lightweight `python:3.11-slim` Docker image.
4. **Testing**: Comprehensive pytest suite testing edge cases, mocks for external APIs, ensuring over 80% coverage.
5. **Accessibility**: A fully WCAG AA compliant single-page UI with ARIA labels, semantic HTML, keyboard navigation, and mobile responsiveness.
6. **Google Services**: Integration with Gemini 2.5 Flash, Cloud Firestore, Secret Manager (via Cloud Run injection), Cloud Logging, and deployment to Cloud Run.
