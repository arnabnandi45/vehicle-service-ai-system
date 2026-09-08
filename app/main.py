from fastapi import FastAPI, Depends, UploadFile, File
from app.core.config import settings
from app.db.database import Base, engine, SessionLocal
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.models.vehicle import Vehicle
from app.schemas.vehicle import VehicleCreate, VehicleUpdate
from app.models.user import User
from app.schemas.user import UserCreate
from app.core.security import hash_password
from app.api.auth import router as auth_router
from app.core.dependencies import get_current_user
from app.core.dependencies import require_admin
import shutil
from app.core.pdf_utils import extract_text_from_pdf
from app.core.text_utils import chunk_text
from app.services.embedding import create_embedding
from app.models.document_chunk import DocumentChunk
from app.services.search import find_most_similar_chunks
from app.services.answer_generator import generate_answer
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()

Base.metadata.create_all(bind=engine)


app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)


app.mount(
    "/static",
    StaticFiles(directory="app/static"),
    name="static"
)


@app.get("/")
def root():
    return {
        "message": f"{settings.APP_NAME} is running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }
@app.get("/db-check")
def database_check():
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))

    return {
        "database": "connected successfully"
    }
@app.get("/vehicles")
def get_vehicles(
    current_user: User = Depends(get_current_user)
):
    with engine.connect() as connection:
        result = connection.execute(
            text("SELECT * FROM vehicles")
        )

        vehicles = [
            dict(row._mapping)
            for row in result
        ]

    return vehicles

@app.get("/vehicles/{vehicle_id}")
def get_vehicle(
    vehicle_id: int,
    current_user: User = Depends(get_current_user)
):
    with engine.connect() as connection:
        result = connection.execute(
            text(
                "SELECT * FROM vehicles WHERE id = :vehicle_id"
            ),
            {"vehicle_id": vehicle_id}
        )

        vehicle = result.fetchone()

    if vehicle is None:
        return {
            "message": "Vehicle not found"
        }

    return dict(vehicle._mapping)


@app.post("/vehicles")
def create_vehicle(
    vehicle: VehicleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    new_vehicle = Vehicle(
        brand=vehicle.brand,
        model=vehicle.model,
        year=vehicle.year
    )

    db.add(new_vehicle)
    db.commit()
    db.refresh(new_vehicle)

    return {
        "message": "Vehicle created successfully",
        "vehicle": {
            "id": new_vehicle.id,
            "brand": new_vehicle.brand,
            "model": new_vehicle.model,
            "year": new_vehicle.year
        }
    }

@app.put("/vehicles/{vehicle_id}")
def update_vehicle(
    vehicle_id: int,
    vehicle: VehicleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    existing_vehicle = db.query(Vehicle).filter(
        Vehicle.id == vehicle_id
    ).first()

    if existing_vehicle is None:
        return {
            "message": "Vehicle not found"
        }

    existing_vehicle.brand = vehicle.brand
    existing_vehicle.model = vehicle.model
    existing_vehicle.year = vehicle.year

    db.commit()
    db.refresh(existing_vehicle)

    return {
        "message": "Vehicle updated successfully",
        "vehicle": {
            "id": existing_vehicle.id,
            "brand": existing_vehicle.brand,
            "model": existing_vehicle.model,
            "year": existing_vehicle.year
        }
    }

@app.delete("/vehicles/{vehicle_id}")
def delete_vehicle(
    vehicle_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    existing_vehicle = db.query(Vehicle).filter(
        Vehicle.id == vehicle_id
    ).first()

    if existing_vehicle is None:
        return {
            "message": "Vehicle not found"
        }

    db.delete(existing_vehicle)
    db.commit()

    return {
        "message": "Vehicle deleted successfully"
    }

@app.post("/register")
def register_user(user: UserCreate, db: Session = Depends(get_db)):

    existing_user = db.query(User).filter(
        User.email == user.email
    ).first()

    if existing_user:
        return {
            "message": "Email already registered"
        }

    hashed_password = hash_password(user.password)

    new_user = User(
    name=user.name,
    email=user.email,
    hashed_password=hashed_password
)

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "message": "User registered successfully",
        "user": {
            "id": new_user.id,
            "name": new_user.name,
            "email": new_user.email
        }
    }

@app.get("/admin")
def admin_dashboard(
    current_user: User = Depends(require_admin)
):
    return {
        "message": "Welcome Admin",
        "user": current_user.name
    }


@app.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    file_path = f"app/uploads/{file.filename}"

    # Save uploaded file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Extract text from PDF
    extracted_text = extract_text_from_pdf(file_path)

    # Split extracted text into chunks
    chunks = chunk_text(extracted_text)

    # Create embeddings and save them
    chunk_embeddings = []

    for chunk in chunks:
        embedding = create_embedding(chunk)

        new_chunk = DocumentChunk(
            filename=file.filename,
            chunk_text=chunk,
            embedding=str(embedding)
        )

        db.add(new_chunk)

        chunk_embeddings.append({
            "text": chunk,
            "embedding": embedding
        })

    # Save everything to PostgreSQL
    db.commit()

    return {
        "filename": file.filename,
        "content_type": file.content_type,
        "message": "File uploaded, text extracted, embeddings created and saved successfully",
        "total_chunks": len(chunks),
        "total_embeddings": len(chunk_embeddings),
        "embedding_dimension": len(chunk_embeddings[0]["embedding"]) if chunk_embeddings else 0,
        "data": chunk_embeddings
    }

@app.get("/test-embedding")
def test_embedding():

    text = "Vehicle needs an oil change"

    embedding = create_embedding(text)

    return {
        "text": text,
        "embedding_length": len(embedding),
        "first_10_values": embedding[:10]
    }
@app.get("/search")
def search_documents(
    question: str,
    db: Session = Depends(get_db)
):
    # Create embedding for user's question
    question_embedding = create_embedding(question)

    # Get all document chunks from database
    document_chunks = db.query(DocumentChunk).all()

    # Find the most similar chunks
    results = find_most_similar_chunks(
        question_embedding=question_embedding,
        document_chunks=document_chunks,
        top_k=3
    )

    return {
        "question": question,
        "results": results
    }

@app.get("/chat")
def chat(
    question: str,
    db: Session = Depends(get_db)
):
    # Create embedding for user's question
    question_embedding = create_embedding(question)

    # Get all document chunks from database
    document_chunks = db.query(DocumentChunk).all()

    # Find the most relevant chunks
    results = find_most_similar_chunks(
        question_embedding=question_embedding,
        document_chunks=document_chunks,
        top_k=3
    )

    # Combine relevant chunks into one context
    context = "\n\n".join(
        result["text"]
        for result in results
    )

    # Generate AI answer using the context
    answer = generate_answer(
        question=question,
        context=context
    )

    return {
        "question": question,
        "answer": answer,
        "sources": results
    }

@app.get("/chat-ui")
def chat_ui():
    return FileResponse("app/templates/chat.html")