# 🚗 Vehicle Service AI Assistant

An AI-powered vehicle service assistant built with FastAPI. The application allows users to upload vehicle service documents and ask questions based on the uploaded document.

## 🚀 Features

- Upload PDF documents
- Extract text from uploaded documents
- Split documents into text chunks
- Generate embeddings for document search
- Search relevant document content
- Ask questions through an AI chat interface
- Answer questions based on uploaded vehicle service documents
- FastAPI REST API
- Interactive Swagger API documentation
- Simple web-based chat interface
- Health check endpoint
- Basic automated testing

## 🛠️ Technologies Used

- Python
- FastAPI
- Uvicorn
- SQLAlchemy
- Alembic
- PostgreSQL
- Transformers
- Hugging Face
- HTML
- CSS
- JavaScript
- Pytest

## 📂 Project Structure

```text
vehicle-service-ai-assistant/
│
├── alembic/
│   └── versions/
│
├── app/
│   ├── api/
│   ├── core/
│   │   ├── config.py
│   │   ├── dependencies.py
│   │   ├── pdf_utils.py
│   │   ├── security.py
│   │   └── text_utils.py
│   │
│   ├── db/
│   ├── models/
│   ├── schemas/
│   │
│   ├── services/
│   │   ├── answer_generator.py
│   │   ├── embedding.py
│   │   └── search.py
│   │
│   ├── static/
│   │   ├── chat.js
│   │   └── styles.css
│   │
│   ├── templates/
│   │   └── chat.html
│   │
│   ├── uploads/
│   └── main.py
│
├── tests/
│   └── unit/
│       └── test_basic.py
│
├── .env
├── .env.example
├── .gitignore
├── alembic.ini
├── requirements.txt
└── README.md