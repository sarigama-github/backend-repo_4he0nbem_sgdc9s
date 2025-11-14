import os
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

from database import db, create_document, get_documents
from schemas import (
    Client, Measurement, Session, WorkoutLog, NutritionEntry,
    Payment, ConsentTemplate, SignedConsent, RelativeStrengthResponse
)

app = FastAPI(title="MIND X MUSCLE API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "MIND X MUSCLE Backend Running"}

# --- EPIC 1: Client Profile & Measurements ---

@app.post("/clients", response_model=dict)
def create_client(client: Client):
    inserted_id = create_document("client", client)
    return {"id": inserted_id}

@app.get("/clients", response_model=List[dict])
def list_clients():
    return get_documents("client")

@app.post("/measurements", response_model=dict)
def add_measurement(measurement: Measurement):
    inserted_id = create_document("measurement", measurement)
    return {"id": inserted_id}

@app.get("/clients/{client_id}/measurements", response_model=List[dict])
def get_client_measurements(client_id: str):
    return get_documents("measurement", {"client_id": client_id})

class OneRMRequest(BaseModel):
    one_rm_kg: float
    bodyweight_kg: float
    date: Optional[str] = None

@app.post("/relative-strength", response_model=RelativeStrengthResponse)
def relative_strength(data: OneRMRequest):
    if data.bodyweight_kg <= 0:
        raise HTTPException(status_code=400, detail="Bodyweight must be > 0")
    rs = data.one_rm_kg / data.bodyweight_kg
    return RelativeStrengthResponse(
        client_id="",
        date=data.date,
        one_rm_kg=data.one_rm_kg,
        bodyweight_kg=data.bodyweight_kg,
        relative_strength=round(rs, 3)
    )

# --- EPIC 2: Sessions & Scheduling ---

@app.post("/sessions", response_model=dict)
def book_session(session: Session):
    inserted_id = create_document("session", session)
    return {"id": inserted_id}

@app.get("/clients/{client_id}/sessions", response_model=List[dict])
def get_client_sessions(client_id: str):
    return get_documents("session", {"client_id": client_id})

# Attendance tracking: decrement sessions_remaining when completed
class AttendanceUpdate(BaseModel):
    status: str  # completed/missed/cancelled

@app.post("/sessions/{session_id}/attendance")
def update_attendance(session_id: str, payload: AttendanceUpdate):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    from bson import ObjectId
    try:
        sess = db["session"].find_one({"_id": ObjectId(session_id)})
        if not sess:
            raise HTTPException(status_code=404, detail="Session not found")
        # update status
        db["session"].update_one({"_id": ObjectId(session_id)}, {"$set": {"status": payload.status, "updated_at": datetime.utcnow()}})
        # decrement client sessions on completed
        if payload.status == "completed":
            db["client"].update_one({"_id": ObjectId(sess["client_id"])}, {"$inc": {"sessions_remaining": -1}, "$set": {"updated_at": datetime.utcnow()}})
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# --- EPIC 3: Workouts & Programs ---

@app.post("/workouts/log", response_model=dict)
def log_workout(entry: WorkoutLog):
    inserted_id = create_document("workoutlog", entry)
    return {"id": inserted_id}

@app.get("/clients/{client_id}/workouts", response_model=List[dict])
def get_workouts(client_id: str):
    return get_documents("workoutlog", {"client_id": client_id})

# --- EPIC 4: Nutrition & Calorie Tracking ---

@app.post("/nutrition", response_model=dict)
def add_nutrition(entry: NutritionEntry):
    inserted_id = create_document("nutritionentry", entry)
    return {"id": inserted_id}

@app.get("/clients/{client_id}/nutrition", response_model=List[dict])
def get_nutrition(client_id: str):
    return get_documents("nutritionentry", {"client_id": client_id})

# --- EPIC 5: Progress Tracking & Reporting ---

@app.get("/clients/{client_id}/progress/relative-strength", response_model=List[dict])
def progress_relative_strength(client_id: str):
    return get_documents("measurement", {"client_id": client_id, "one_rm_kg": {"$gt": 0}, "bodyweight_kg": {"$gt": 0}})

# --- EPIC 6: Payments & Subscriptions ---

@app.post("/payments", response_model=dict)
def create_payment(p: Payment):
    inserted_id = create_document("payment", p)
    return {"id": inserted_id}

@app.get("/clients/{client_id}/payments", response_model=List[dict])
def get_payments(client_id: str):
    return get_documents("payment", {"client_id": client_id})

# --- EPIC 10: Digital Consent & Legal Forms ---

@app.post("/consent/templates", response_model=dict)
def upload_consent_template(t: ConsentTemplate):
    inserted_id = create_document("consenttemplate", t)
    return {"id": inserted_id}

class SignConsentRequest(BaseModel):
    client_id: str
    client_name: str
    template_id: str
    template_title: str
    template_version: str
    signature_text: str
    media_consent: bool = True

@app.post("/consent/sign", response_model=dict)
def sign_consent(data: SignConsentRequest):
    # Generate PDF-like filename
    today = datetime.utcnow().strftime("%Y-%m-%d")
    filename = f"Consent_AswajithSS_{data.client_name}_{today}.pdf"
    signed = SignedConsent(
        client_id=data.client_id,
        client_name=data.client_name,
        template_id=data.template_id,
        template_title=data.template_title,
        template_version=data.template_version,
        signed_at=datetime.utcnow().isoformat(),
        signature_text=data.signature_text,
        media_consent=data.media_consent,
        pdf_filename=filename,
    )
    inserted_id = create_document("signedconsent", signed)
    return {"id": inserted_id, "pdf": filename}

# --- Utilities ---

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name
            response["connection_status"] = "Connected"
            try:
                response["collections"] = db.list_collection_names()[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
