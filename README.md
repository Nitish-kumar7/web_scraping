# Candidate Verification System

A FastAPI-based backend system that integrates with various platforms to analyze candidate profiles and match them against job descriptions.

## Features

- GitHub profile analysis
- LinkedIn profile parsing from PDF
- Instagram profile scraping
- Portfolio website analysis
- AI-powered skill matching against job descriptions
- Rate limiting and API key authentication
- Comprehensive logging
- Environment-based configuration

## Prerequisites

- Python 3.8+
- pip (Python package manager)
- Virtual environment (recommended)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd social_media_scraping
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the project root with the following variables:
```env
# API Configuration
API_KEY=your_api_key_here
HOST=0.0.0.0
PORT=8000
DEBUG=False

# Security
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000
ALLOWED_HOSTS=localhost,127.0.0.1

# GitHub API
GITHUB_TOKEN=your_github_token_here

# Instagram API (if using)
INSTAGRAM_USERNAME=your_instagram_username
INSTAGRAM_PASSWORD=your_instagram_password

# AI Model Configuration
OPENAI_API_KEY=your_openai_api_key_here
```

## Usage

1. Start the server:
```bash
python backend/main.py
```

2. The API will be available at `http://localhost:8000`

3. API Endpoints:

- `GET /github/{username}` - Fetch GitHub profile data
- `POST /resume/upload` - Upload and parse resume
- `GET /instagram/{username}` - Fetch Instagram profile data
- `GET /portfolio?url={url}` - Analyze portfolio website
- `POST /analyze` - Analyze candidate data against job description

4. Example API request:
```bash
curl -X POST "http://localhost:8000/analyze" \
     -H "X-API-Key: your_api_key_here" \
     -H "Content-Type: application/json" \
     -d '{
           "github_url": "https://github.com/username",
           "portfolio_url": "https://portfolio.com",
           "job_description": "Looking for a Python developer with React experience..."
         }'
```

## API Documentation

Once the server is running, you can access the interactive API documentation at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Security

- All endpoints require an API key
- Rate limiting is enabled to prevent abuse
- CORS is configured to allow only specified origins
- Trusted host middleware is enabled

## Logging

Logs are stored in the `logs` directory with daily rotation. Each log file is named `app_YYYYMMDD.log`.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 