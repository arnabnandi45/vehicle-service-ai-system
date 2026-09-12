from fastapi import FastAPI, Depends, UploadFile, File, HTTPException, WebSocket, WebSocketDisconnect
from app.core.config import settings
from app.db.database import Base, engine, SessionLocal
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.models.vehicle import Vehicle
from app.schemas.vehicle import VehicleCreate, VehicleUpdate
from app.models.user import User
from app.schemas.user import UserCreate
from app.models.customer import Customer
from app.schemas.customer import CustomerCreate, CustomerUpdate, CustomerResponse
from app.core.security import hash_password
from app.api.auth import router as auth_router
from app.core.dependencies import get_current_user
from app.core.dependencies import require_admin
import shutil
import os
import uuid
from app.core.pdf_utils import extract_text_from_pdf
from app.core.text_utils import chunk_text
from app.services.embedding import create_embedding
from app.models.document_chunk import DocumentChunk
from app.services.search import find_most_similar_chunks
from app.services.answer_generator import generate_answer
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.models.service_type import ServiceType
from app.schemas.service_type import (
    ServiceTypeCreate,
    ServiceTypeUpdate,
    ServiceTypeResponse
)
from app.models.technician import Technician
from app.schemas.technician import (
    TechnicianCreate,
    TechnicianUpdate,
    TechnicianResponse
)

from app.models.service_booking import ServiceBooking
from app.schemas.service_booking import (
    ServiceBookingCreate,
    ServiceBookingUpdate,
    ServiceBookingResponse
)
from datetime import datetime, timedelta
from app.models.job_card import JobCard
from app.schemas.job_card import (
    JobCardCreate,
    JobCardUpdate,
    JobCardResponse
)


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()

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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role == "admin":
        return db.query(Vehicle).all()

    return db.query(Vehicle).filter(
        Vehicle.customer_id == current_user.id
    ).all()


@app.get("/vehicles/{vehicle_id}")
def get_vehicle(
    vehicle_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    vehicle = db.query(Vehicle).filter(
        Vehicle.id == vehicle_id
    ).first()

    if vehicle is None:
        raise HTTPException(
            status_code=404,
            detail="Vehicle not found"
        )

    # Admin can access any vehicle
    if current_user.role == "admin":
        return vehicle

    # Customer can access only their own vehicle
    if vehicle.customer_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You do not have access to this vehicle"
        )

    return vehicle


@app.post("/vehicles")
def create_vehicle(
    vehicle: VehicleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    new_vehicle = Vehicle(
        customer_id=current_user.id,
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
            "customer_id": new_vehicle.customer_id,
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
    current_user: User = Depends(get_current_user)
):
    existing_vehicle = db.query(Vehicle).filter(
        Vehicle.id == vehicle_id
    ).first()

    if existing_vehicle is None:
        raise HTTPException(
            status_code=404,
            detail="Vehicle not found"
        )

    # Admin can update any vehicle
    if current_user.role != "admin":

        # Customer can update only their own vehicle
        if existing_vehicle.customer_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="You do not have access to this vehicle"
            )

    if vehicle.brand is not None:
        existing_vehicle.brand = vehicle.brand

    if vehicle.model is not None:
        existing_vehicle.model = vehicle.model

    if vehicle.year is not None:
        existing_vehicle.year = vehicle.year

    db.commit()
    db.refresh(existing_vehicle)

    return {
        "message": "Vehicle updated successfully",
        "vehicle": existing_vehicle
    }


@app.delete("/vehicles/{vehicle_id}")
def delete_vehicle(
    vehicle_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    existing_vehicle = db.query(Vehicle).filter(
        Vehicle.id == vehicle_id
    ).first()

    if existing_vehicle is None:
        raise HTTPException(
            status_code=404,
            detail="Vehicle not found"
        )

    # Only admin or owner can delete
    if current_user.role != "admin":
        if existing_vehicle.customer_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="You do not have access to this vehicle"
            )

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
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed"
        )

    # Read the uploaded file into memory first.
    file_content = await file.read()

    if not file_content:
        raise HTTPException(
            status_code=400,
            detail="Uploaded PDF is empty"
        )

    # Use a safe generated filename instead of trusting the original filename.
    original_filename = os.path.basename(file.filename or "uploaded.pdf")
    safe_filename = f"{uuid.uuid4().hex}_{original_filename}"

    upload_dir = "app/uploads"
    os.makedirs(upload_dir, exist_ok=True)

    file_path = os.path.join(upload_dir, safe_filename)

    try:
        # Save the new PDF.
        with open(file_path, "wb") as buffer:
            buffer.write(file_content)

        # Extract text from the new PDF before changing existing knowledge.
        try:
            extracted_text = extract_text_from_pdf(file_path)
        except Exception as exc:
            raise HTTPException(
                status_code=400,
                detail=f"Could not process the PDF: {str(exc)}"
            )

        if not extracted_text.strip():
            raise HTTPException(
                status_code=400,
                detail="Could not extract any text from the PDF"
            )

        # Split extracted text into chunks.
        chunks = chunk_text(extracted_text)

        if not chunks:
            raise HTTPException(
                status_code=400,
                detail="No usable text chunks were created from the PDF"
            )

        # Create all embeddings before modifying the existing knowledge base.
        new_chunks = []

        for chunk in chunks:
            embedding = create_embedding(chunk)

            new_chunks.append(
                DocumentChunk(
                    filename=original_filename,
                    chunk_text=chunk,
                    embedding=str(embedding)
                )
            )

        # Replace the old knowledge base only after the new document
        # has been successfully processed.
        db.query(DocumentChunk).delete(synchronize_session=False)

        for new_chunk in new_chunks:
            db.add(new_chunk)

        db.commit()

        return {
            "filename": original_filename,
            "content_type": file.content_type,
            "message": "File uploaded, text extracted, embeddings created and saved successfully",
            "total_chunks": len(new_chunks),
            "total_embeddings": len(new_chunks),
            "embedding_dimension": len(
                create_embedding(chunks[0])
            ) if chunks else 0
        }

    except HTTPException:
        db.rollback()

        if os.path.exists(file_path):
            os.remove(file_path)

        raise

    except Exception as exc:
        db.rollback()

        if os.path.exists(file_path):
            os.remove(file_path)

        raise HTTPException(
            status_code=500,
            detail=f"Failed to process uploaded document: {str(exc)}"
        )

    
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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Create embedding for user's question
    question_embedding = create_embedding(question)

    # Get all document chunks from database
    document_chunks = db.query(DocumentChunk).all()

    # Find the most similar chunks
    results = find_most_similar_chunks(
        question_embedding=question_embedding,
        document_chunks=document_chunks,
        top_k=5
    )

    return {
        "question": question,
        "results": results
    }

@app.get("/chat")
def chat(
    question: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Critical safety check
    safety_keywords = [
        "brake failure",
        "brakes failed",
        "brake not working",
        "brakes stopped working",
        "brake stopped working",
        "brakes don't work",
        "brakes do not work",
        "steering failure",
        "steering not working",
        "tyre burst",
        "tire burst",
        "fuel leak",
        "petrol leak",
        "diesel leak",
        "electrical fire",
        "smoke from engine",
        "engine fire",
        "fire from car"
    ]

    question_lower = question.lower()

    if any(keyword in question_lower for keyword in safety_keywords):
        return {
            "question": question,
            "answer": (
                "This may be a critical safety issue. "
                "Stop using the vehicle if it is unsafe to drive, "
                "move to a safe location if possible, and contact "
                "a qualified technician or emergency service as appropriate."
            ),
            "sources": []
        }
    
    question_embedding = create_embedding(question)
    document_chunks = db.query(DocumentChunk).all()

    if not document_chunks:
        return {
            "question": question,
            "answer": "No document has been uploaded yet. Please upload a PDF first.",
            "sources": []
        }

    results = find_most_similar_chunks(
        question_embedding=question_embedding,
        document_chunks=document_chunks,
        top_k=3
    )

    # Check whether relevant information was found
    similarity_threshold = 0.30

    if not results or results[0]["similarity"] < similarity_threshold:
        return {
            "question": question,
            "answer": "I don't have enough information in the provided service documents.",
            "sources": []
        }

    context = "\n\n".join(result["text"] for result in results)

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

@app.post("/service-types", response_model=ServiceTypeResponse)
def create_service_type(
    service: ServiceTypeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    new_service = ServiceType(
        name=service.name,
        description=service.description,
        base_price=service.base_price,
        duration_minutes=service.duration_minutes
    )

    db.add(new_service)
    db.commit()
    db.refresh(new_service)

    return new_service


@app.get("/service-types", response_model=list[ServiceTypeResponse])
def get_service_types(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(ServiceType).all()


@app.get("/service-types/{service_id}", response_model=ServiceTypeResponse)
def get_service_type(
    service_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = db.query(ServiceType).filter(
        ServiceType.id == service_id
    ).first()

    if not service:
        return {"message": "Service type not found"}

    return service


@app.put("/service-types/{service_id}", response_model=ServiceTypeResponse)
def update_service_type(
    service_id: int,
    service_data: ServiceTypeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    service = db.query(ServiceType).filter(
        ServiceType.id == service_id
    ).first()

    if not service:
        return {"message": "Service type not found"}

    if service_data.name is not None:
        service.name = service_data.name

    if service_data.description is not None:
        service.description = service_data.description

    if service_data.base_price is not None:
        service.base_price = service_data.base_price

    if service_data.duration_minutes is not None:
        service.duration_minutes = service_data.duration_minutes

    db.commit()
    db.refresh(service)

    return service


@app.delete("/service-types/{service_id}")
def delete_service_type(
    service_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    service = db.query(ServiceType).filter(
        ServiceType.id == service_id
    ).first()

    if not service:
        return {"message": "Service type not found"}

    db.delete(service)
    db.commit()

    return {"message": "Service type deleted successfully"}

@app.post("/technicians", response_model=TechnicianResponse)
def create_technician(
    technician: TechnicianCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    new_technician = Technician(
        name=technician.name,
        specialization=technician.specialization,
        is_available=technician.is_available
    )

    db.add(new_technician)
    db.commit()
    db.refresh(new_technician)

    return new_technician


@app.get("/technicians", response_model=list[TechnicianResponse])
def get_technicians(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(Technician).all()


@app.get("/technicians/{technician_id}", response_model=TechnicianResponse)
def get_technician(
    technician_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    technician = db.query(Technician).filter(
        Technician.id == technician_id
    ).first()

    if not technician:
        return {"message": "Technician not found"}

    return technician


@app.put("/technicians/{technician_id}", response_model=TechnicianResponse)
def update_technician(
    technician_id: int,
    technician_data: TechnicianUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    technician = db.query(Technician).filter(
        Technician.id == technician_id
    ).first()

    if not technician:
        return {"message": "Technician not found"}

    if technician_data.name is not None:
        technician.name = technician_data.name

    if technician_data.specialization is not None:
        technician.specialization = technician_data.specialization

    if technician_data.is_available is not None:
        technician.is_available = technician_data.is_available

    db.commit()
    db.refresh(technician)

    return technician


@app.delete("/technicians/{technician_id}")
def delete_technician(
    technician_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    technician = db.query(Technician).filter(
        Technician.id == technician_id
    ).first()

    if not technician:
        return {"message": "Technician not found"}

    db.delete(technician)
    db.commit()

    return {"message": "Technician deleted successfully"}

@app.post("/bookings", response_model=ServiceBookingResponse)
def create_booking(
    booking: ServiceBookingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check vehicle
    vehicle = db.query(Vehicle).filter(
        Vehicle.id == booking.vehicle_id
    ).first()

    if not vehicle:
        raise HTTPException(
            status_code=404,
            detail="Vehicle not found"
        )
    # Check vehicle ownership
    if current_user.role != "admin":
        if vehicle.customer_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="You do not have access to this vehicle"
            )


    # Check service type
    service = db.query(ServiceType).filter(
        ServiceType.id == booking.service_type_id
    ).first()

    if not service:
        raise HTTPException(
            status_code=404,
            detail="Service type not found"
        )

    # Check technician if provided
    if booking.technician_id is not None:
        technician = db.query(Technician).filter(
            Technician.id == booking.technician_id
        ).first()

        if not technician:
            raise HTTPException(
                status_code=404,
                detail="Technician not found"
            )

        if not technician.is_available:
            raise HTTPException(
                status_code=400,
                detail="Technician is not available"
            )

        # Check schedule conflict
        service_duration = timedelta(
            minutes=service.duration_minutes
        )

        booking_start = booking.scheduled_at
        booking_end = booking_start + service_duration

        existing_bookings = db.query(ServiceBooking).filter(
            ServiceBooking.technician_id == booking.technician_id,
            ServiceBooking.status != "cancelled"
        ).all()

        for existing in existing_bookings:
            existing_service = db.query(ServiceType).filter(
                ServiceType.id == existing.service_type_id
            ).first()

            existing_start = existing.scheduled_at
            existing_end = existing_start + timedelta(
                minutes=existing_service.duration_minutes
            )

            # Check whether the two time periods overlap
            if booking_start < existing_end and booking_end > existing_start:
                raise HTTPException(
                    status_code=409,
                    detail="Technician already has a booking at this time"
                )

    # Create booking
    new_booking = ServiceBooking(
        vehicle_id=booking.vehicle_id,
        service_type_id=booking.service_type_id,
        technician_id=booking.technician_id,
        scheduled_at=booking.scheduled_at,
        status="pending"
    )

    db.add(new_booking)
    db.commit()
    db.refresh(new_booking)

    return new_booking

@app.get("/bookings", response_model=list[ServiceBookingResponse])
def get_bookings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role == "admin":
        return db.query(ServiceBooking).all()

    return (
        db.query(ServiceBooking)
        .join(Vehicle, ServiceBooking.vehicle_id == Vehicle.id)
        .filter(Vehicle.customer_id == current_user.id)
        .all()
    )

@app.put("/bookings/{booking_id}", response_model=ServiceBookingResponse)
def update_booking(
    booking_id: int,
    booking_data: ServiceBookingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    booking = db.query(ServiceBooking).filter(
        ServiceBooking.id == booking_id
    ).first()

    if not booking:
        raise HTTPException(
            status_code=404,
            detail="Booking not found"
        )

    # Check vehicle ownership
    vehicle = db.query(Vehicle).filter(
        Vehicle.id == booking.vehicle_id
    ).first()

    if current_user.role != "admin":
        if not vehicle or vehicle.customer_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="You do not have access to this booking"
            )

    # Update technician if provided
    if booking_data.technician_id is not None:

        technician = db.query(Technician).filter(
            Technician.id == booking_data.technician_id
        ).first()

        if not technician:
            raise HTTPException(
                status_code=404,
                detail="Technician not found"
            )

        if not technician.is_available:
            raise HTTPException(
                status_code=400,
                detail="Technician is not available"
            )

        booking.technician_id = booking_data.technician_id

    # Update scheduled time
    if booking_data.scheduled_at is not None:
        booking.scheduled_at = booking_data.scheduled_at

    # Update status
    if booking_data.status is not None:
        booking.status = booking_data.status

    db.commit()
    db.refresh(booking)

    return booking


@app.delete("/bookings/{booking_id}")
def delete_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    booking = db.query(ServiceBooking).filter(
        ServiceBooking.id == booking_id
    ).first()

    if not booking:
        raise HTTPException(
            status_code=404,
            detail="Booking not found"
        )

    vehicle = db.query(Vehicle).filter(
        Vehicle.id == booking.vehicle_id
    ).first()

    if current_user.role != "admin":
        if not vehicle or vehicle.customer_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="You do not have access to this booking"
            )

    # Cancel instead of physically deleting,
    # so service history is preserved.
    booking.status = "cancelled"

    db.commit()

    return {
        "message": "Booking cancelled successfully"
    }

@app.post("/job-cards", response_model=JobCardResponse)
def create_job_card(
    job_data: JobCardCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    # Only admin and staff can create job cards
    allowed_roles = ["admin", "service_advisor", "technician"]

    if current_user.role not in allowed_roles:
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to create a job card"
        )
    # Check booking
    booking = db.query(ServiceBooking).filter(
        ServiceBooking.id == job_data.booking_id
    ).first()

    if not booking:
        raise HTTPException(
            status_code=404,
            detail="Booking not found"
        )

    # Check technician if provided
    if job_data.technician_id is not None:
        technician = db.query(Technician).filter(
            Technician.id == job_data.technician_id
        ).first()

        if not technician:
            raise HTTPException(
                status_code=404,
                detail="Technician not found"
            )

    # Prevent duplicate job card for same booking
    existing_job = db.query(JobCard).filter(
        JobCard.booking_id == job_data.booking_id
    ).first()

    if existing_job:
        raise HTTPException(
            status_code=409,
            detail="Job card already exists for this booking"
        )

    new_job_card = JobCard(
        booking_id=job_data.booking_id,
        technician_id=job_data.technician_id,
        inspection_notes=job_data.inspection_notes,
        estimate=job_data.estimate,
        status="open"
    )

    db.add(new_job_card)
    db.commit()
    db.refresh(new_job_card)

    return new_job_card


@app.get("/job-cards", response_model=list[JobCardResponse])
def get_job_cards(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Admin can see all job cards
    if current_user.role == "admin":
        return db.query(JobCard).all()

    # Customers can see only job cards
    # belonging to their own vehicles
    return (
        db.query(JobCard)
        .join(ServiceBooking, JobCard.booking_id == ServiceBooking.id)
        .join(Vehicle, ServiceBooking.vehicle_id == Vehicle.id)
        .filter(Vehicle.customer_id == current_user.id)
        .all()
    )

@app.get("/job-cards/{job_card_id}", response_model=JobCardResponse)
def get_job_card(
    job_card_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    job_card = db.query(JobCard).filter(
        JobCard.id == job_card_id
    ).first()

    if not job_card:
        raise HTTPException(
            status_code=404,
            detail="Job card not found"
        )

    # Admin can access any job card
    if current_user.role == "admin":
        return job_card

    # Find related booking
    booking = db.query(ServiceBooking).filter(
        ServiceBooking.id == job_card.booking_id
    ).first()

    if not booking:
        raise HTTPException(
            status_code=404,
            detail="Related booking not found"
        )

    # Find related vehicle
    vehicle = db.query(Vehicle).filter(
        Vehicle.id == booking.vehicle_id
    ).first()

    # Customer can access only their own vehicle's job card
    if not vehicle or vehicle.customer_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You do not have access to this job card"
        )

    return job_card


@app.put("/job-cards/{job_card_id}", response_model=JobCardResponse)
def update_job_card(
    job_card_id: int,
    job_data: JobCardUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Only admin and staff can update job cards
    allowed_roles = ["admin", "service_advisor", "technician"]

    if current_user.role not in allowed_roles:
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to update a job card"
        )

    job_card = db.query(JobCard).filter(
        JobCard.id == job_card_id
    ).first()

    if not job_card:
        raise HTTPException(
            status_code=404,
            detail="Job card not found"
        )

    if job_data.technician_id is not None:
        technician = db.query(Technician).filter(
            Technician.id == job_data.technician_id
        ).first()

        if not technician:
            raise HTTPException(
                status_code=404,
                detail="Technician not found"
            )

        job_card.technician_id = job_data.technician_id

    if job_data.inspection_notes is not None:
        job_card.inspection_notes = job_data.inspection_notes

    if job_data.estimate is not None:
        job_card.estimate = job_data.estimate

    if job_data.status is not None:
        job_card.status = job_data.status

    db.commit()
    db.refresh(job_card)

    return job_card

@app.delete("/job-cards/{job_card_id}")
def delete_job_card(
    job_card_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    job_card = db.query(JobCard).filter(
        JobCard.id == job_card_id
    ).first()

    if not job_card:
        raise HTTPException(
            status_code=404,
            detail="Job card not found"
        )

    db.delete(job_card)
    db.commit()

    return {"message": "Job card deleted successfully"}

@app.post("/customers", response_model=CustomerResponse)
def create_customer(
    customer: CustomerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    existing_customer = db.query(Customer).filter(
        Customer.user_id == current_user.id
    ).first()

    if existing_customer:
        raise HTTPException(
            status_code=409,
            detail="Customer profile already exists"
        )

    new_customer = Customer(
        user_id=current_user.id,
        phone=customer.phone,
        address=customer.address
    )

    db.add(new_customer)
    db.commit()
    db.refresh(new_customer)

    return new_customer


@app.get("/customers/me", response_model=CustomerResponse)
def get_my_customer_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    customer = db.query(Customer).filter(
        Customer.user_id == current_user.id
    ).first()

    if not customer:
        raise HTTPException(
            status_code=404,
            detail="Customer profile not found"
        )

    return customer


@app.put("/customers/me", response_model=CustomerResponse)
def update_my_customer_profile(
    customer_data: CustomerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    customer = db.query(Customer).filter(
        Customer.user_id == current_user.id
    ).first()

    if not customer:
        raise HTTPException(
            status_code=404,
            detail="Customer profile not found"
        )

    if customer_data.phone is not None:
        customer.phone = customer_data.phone

    if customer_data.address is not None:
        customer.address = customer_data.address

    db.commit()
    db.refresh(customer)

    return customer


@app.delete("/customers/me")
def delete_my_customer_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    customer = db.query(Customer).filter(
        Customer.user_id == current_user.id
    ).first()

    if not customer:
        raise HTTPException(
            status_code=404,
            detail="Customer profile not found"
        )

    db.delete(customer)
    db.commit()

    return {
        "message": "Customer profile deleted successfully"
    }

@app.get("/vehicles/{vehicle_id}/service-history")
def get_vehicle_service_history(
    vehicle_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Find vehicle
    vehicle = db.query(Vehicle).filter(
        Vehicle.id == vehicle_id
    ).first()

    if not vehicle:
        raise HTTPException(
            status_code=404,
            detail="Vehicle not found"
        )

    # Ownership protection
    if current_user.role != "admin":
        if vehicle.customer_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="You do not have access to this vehicle's service history"
            )

    # Get bookings for this vehicle
    bookings = db.query(ServiceBooking).filter(
        ServiceBooking.vehicle_id == vehicle_id
    ).all()

    history = []

    for booking in bookings:

        service = db.query(ServiceType).filter(
            ServiceType.id == booking.service_type_id
        ).first()

        technician = None

        if booking.technician_id is not None:
            technician = db.query(Technician).filter(
                Technician.id == booking.technician_id
            ).first()

        job_card = db.query(JobCard).filter(
            JobCard.booking_id == booking.id
        ).first()

        history.append({
            "booking_id": booking.id,
            "scheduled_at": booking.scheduled_at,
            "booking_status": booking.status,

            "service": {
                "id": service.id if service else None,
                "name": service.name if service else None,
                "base_price": service.base_price if service else None,
                "duration_minutes": service.duration_minutes if service else None
            },

            "technician": {
                "id": technician.id if technician else None,
                "name": technician.name if technician else None
            } if technician else None,

            "job_card": {
                "id": job_card.id,
                "inspection_notes": job_card.inspection_notes,
                "estimate": job_card.estimate,
                "status": job_card.status
            } if job_card else None
        })

    return {
        "vehicle": {
            "id": vehicle.id,
            "brand": vehicle.brand,
            "model": vehicle.model,
            "year": vehicle.year
        },
        "service_history": history
    }

@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()

    try:
        while True:
            question = await websocket.receive_text()

            # Safety check
            safety_keywords = [
                "brake failure",
                "brakes failed",
                "brake not working",
                "brakes stopped working",
                "brake stopped working",
                "brakes don't work",
                "brakes do not work",
                "steering failure",
                "steering not working",
                "tyre burst",
                "tire burst",
                "fuel leak",
                "petrol leak",
                "diesel leak",
                "electrical fire",
                "smoke from engine",
                "engine fire",
                "fire from car"
            ]

            question_lower = question.lower()

            if any(keyword in question_lower for keyword in safety_keywords):
                answer = (
                    "This may be a critical safety issue. "
                    "Stop using the vehicle if it is unsafe to drive, "
                    "move to a safe location if possible, and contact "
                    "a qualified technician or emergency service as appropriate."
                )

                await websocket.send_json({
                    "question": question,
                    "answer": answer,
                    "sources": []
                })

                continue

            # RAG search
            db = SessionLocal()

            try:
                question_embedding = create_embedding(question)

                document_chunks = db.query(DocumentChunk).all()

                if not document_chunks:
                    await websocket.send_json({
                        "question": question,
                        "answer": "No document has been uploaded yet. Please upload a PDF first.",
                        "sources": []
                    })
                    continue

                results = find_most_similar_chunks(
                    question_embedding=question_embedding,
                    document_chunks=document_chunks,
                    top_k=3
                )

                similarity_threshold = 0.30

                if not results or results[0]["similarity"] < similarity_threshold:
                    await websocket.send_json({
                        "question": question,
                        "answer": "I don't have enough information in the provided service documents.",
                        "sources": []
                    })
                    continue

                context = "\n\n".join(
                    result["text"] for result in results
                )

                answer = generate_answer(
                    question=question,
                    context=context
                )

                await websocket.send_json({
                    "question": question,
                    "answer": answer,
                    "sources": results
                })

            finally:
                db.close()

    except WebSocketDisconnect:
        print("WebSocket client disconnected")
