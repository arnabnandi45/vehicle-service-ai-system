# Vehicle Service AI Assistant

An AI-powered vehicle service centre management system with a RAG-based service assistant.

## Features

- User registration and login
- JWT-based authentication
- Role-based access control
- Customer profile management
- Vehicle CRUD with customer ownership protection
- Service type management
- Technician management
- Service booking
- Technician schedule conflict validation
- Job card management
- Vehicle service history
- PDF knowledge document upload
- Text extraction and chunking
- Embedding generation
- Similarity-based document search
- RAG-based AI chatbot
- No-answer protection for unsupported questions
- Source references in chatbot responses
- Critical vehicle safety response
- WebSocket chat
- Pytest test setup
- Docker configuration

## Technology Stack

- Python
- FastAPI
- PostgreSQL
- SQLAlchemy
- Alembic
- JWT Authentication
- Sentence Transformers
- Hugging Face Transformers
- FLAN-T5
- Pytest
- Docker

## Project Structure

```text
vehicle-service-ai-assistant/
│
├── app/
│   ├── api/
│   ├── core/
│   ├── db/
│   ├── models/
│   ├── schemas/
│   ├── services/
│   ├── static/
│   ├── templates/
│   ├── uploads/
│   └── main.py
│
├── alembic/
│   └── versions/
│
├── tests/
│   └── unit/
│
├── .env.example
├── .gitignore
├── alembic.ini
├── Dockerfile
├── docker-compose.yml
├── pytest.ini
├── requirements.txt
└── README.md
```

## Environment Setup

Create a `.env` file in the project root.

Example:

```env
APP_NAME=Vehicle Service AI Assistant
DEBUG=True
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/vehicle_service_db
```

Do not commit real passwords or secret keys to GitHub.

## Install Dependencies

Create a virtual environment:

```bash
python -m venv venv
```

Activate it on Windows PowerShell:

```bash
venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Database Migration

Run the Alembic migrations:

```bash
alembic upgrade head
```

## Run the Application

Start the FastAPI server:

```bash
uvicorn app.main:app --reload
```

Open Swagger API documentation:

```text
http://127.0.0.1:8000/docs
```

## Main API Areas

### Authentication

```text
POST /auth/register
POST /auth/login
```

### Vehicles

```text
GET    /vehicles
POST   /vehicles
GET    /vehicles/{vehicle_id}
PUT    /vehicles/{vehicle_id}
DELETE /vehicles/{vehicle_id}
```

### Customer Profile

```text
POST   /customers
GET    /customers/me
PUT    /customers/me
DELETE /customers/me
```

### Service Types

```text
GET    /service-types
POST   /service-types
GET    /service-types/{service_id}
PUT    /service-types/{service_id}
DELETE /service-types/{service_id}
```

### Technicians

```text
GET    /technicians
POST   /technicians
GET    /technicians/{technician_id}
PUT    /technicians/{technician_id}
DELETE /technicians/{technician_id}
```

### Bookings

```text
POST   /bookings
GET    /bookings
PUT    /bookings/{booking_id}
DELETE /bookings/{booking_id}
```

### Job Cards

```text
POST   /job-cards
GET    /job-cards
GET    /job-cards/{job_card_id}
PUT    /job-cards/{job_card_id}
DELETE /job-cards/{job_card_id}
```

### AI Assistant

```text
POST /upload
GET  /search
GET  /chat
GET  /chat-ui
WS   /ws/chat
```

### Service History

```text
GET /vehicles/{vehicle_id}/service-history
```

## RAG Pipeline

```text
PDF Upload
    ↓
Text Extraction
    ↓
Text Chunking
    ↓
Embedding Generation
    ↓
PostgreSQL Storage
    ↓
Similarity Search
    ↓
Relevant Context
    ↓
FLAN-T5
    ↓
Grounded Answer + Sources
```

The assistant returns a no-answer response when relevant information is not found in the uploaded service documents.

## Testing

Run the test suite:

```bash
python -m pytest
```

Current test result:

```text
2 passed
```

## Docker

Docker configuration is included using:

```text
Dockerfile
docker-compose.yml
```

To build the Docker containers:

```bash
docker compose build
```

To start the application:

```bash
docker compose up
```

Docker execution requires Docker Desktop or another Docker installation.

## Security

- JWT authentication
- Protected API endpoints
- Role-based permissions
- Customer vehicle ownership protection
- Booking ownership protection
- Job card role protection
- Admin-only knowledge document upload
- Real credentials are excluded from the repository

## Safety

For critical symptoms involving brakes, steering, tyres, fuel leaks, or electrical/fire-related issues, the assistant provides a safety-oriented response and recommends stopping use of an unsafe vehicle and contacting a qualified technician or appropriate emergency service.

## Project Status

Core vehicle service management and RAG assistant functionality has been implemented.

## License

This project is developed as an academic final project.