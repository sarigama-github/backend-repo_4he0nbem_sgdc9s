"""
Database Schemas for MIND X MUSCLE

Each Pydantic model represents a collection in MongoDB.
Collection name is the lowercase of the class name.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime

# Core domain schemas

class Client(BaseModel):
    full_name: str = Field(..., description="Client full name")
    email: str = Field(..., description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")
    gender: Optional[Literal["male", "female", "other"]] = Field(None)
    date_of_birth: Optional[str] = Field(None, description="YYYY-MM-DD")
    height_cm: Optional[float] = Field(None, ge=50, le=250)
    weight_kg: Optional[float] = Field(None, ge=20, le=400)
    goal: Optional[str] = Field(None, description="Primary fitness goal")
    notes: Optional[str] = Field(None)
    package_type: Optional[str] = Field(None)
    sessions_total: Optional[int] = Field(None, ge=0)
    sessions_remaining: Optional[int] = Field(None, ge=0)
    is_active: bool = Field(True)

class Measurement(BaseModel):
    client_id: str = Field(..., description="Reference to Client _id as string")
    date: Optional[str] = Field(None, description="YYYY-MM-DD")
    weight_kg: Optional[float] = Field(None, ge=20, le=400)
    bodyfat_pct: Optional[float] = Field(None, ge=0, le=100)
    chest_cm: Optional[float] = None
    waist_cm: Optional[float] = None
    hips_cm: Optional[float] = None
    thigh_cm: Optional[float] = None
    arm_cm: Optional[float] = None
    vo2max: Optional[float] = Field(None, ge=0)
    one_rm_kg: Optional[float] = Field(None, ge=0, description="Estimated 1RM for key lift")
    bodyweight_kg: Optional[float] = Field(None, ge=0)

class Session(BaseModel):
    client_id: str
    start_time: str = Field(..., description="ISO datetime")
    end_time: str = Field(..., description="ISO datetime")
    status: Literal["scheduled", "completed", "missed", "cancelled"] = "scheduled"
    location: Optional[str] = None
    notes: Optional[str] = None
    reschedule_count: int = 0
    is_frozen: bool = False

class WorkoutLog(BaseModel):
    client_id: str
    date: str = Field(..., description="YYYY-MM-DD")
    exercise: str
    sets: int
    reps: int
    weight_kg: Optional[float] = None
    notes: Optional[str] = None
    source: Literal["session", "home"] = "session"

class NutritionEntry(BaseModel):
    client_id: str
    date: str = Field(..., description="YYYY-MM-DD")
    meal: Literal["breakfast", "lunch", "dinner", "snack"]
    item: str
    calories: Optional[int] = Field(None, ge=0)
    protein_g: Optional[float] = Field(None, ge=0)
    carbs_g: Optional[float] = Field(None, ge=0)
    fats_g: Optional[float] = Field(None, ge=0)

class Payment(BaseModel):
    client_id: str
    package_name: str
    amount: float = Field(..., ge=0)
    currency: str = "INR"
    start_date: str = Field(..., description="YYYY-MM-DD")
    end_date: str = Field(..., description="YYYY-MM-DD")
    status: Literal["paid", "pending", "failed"] = "paid"
    sessions_included: Optional[int] = None

class ConsentTemplate(BaseModel):
    title: str
    version: str = Field(..., description="e.g., v1.0")
    content: str = Field(..., description="Plain text or markdown body")

class SignedConsent(BaseModel):
    client_id: str
    client_name: str
    template_id: str
    template_title: str
    template_version: str
    signed_at: Optional[str] = Field(None, description="ISO datetime")
    signature_text: str = Field(..., description="Name or short signature text")
    media_consent: bool = True
    pdf_filename: Optional[str] = None

# Utility response models (not collections)

class RelativeStrengthResponse(BaseModel):
    client_id: str
    date: Optional[str] = None
    one_rm_kg: float
    bodyweight_kg: float
    relative_strength: float

