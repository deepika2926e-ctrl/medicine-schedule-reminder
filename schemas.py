from datetime import date, time, datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field

# ----------------- User Schemas -----------------
class UserRegister(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=150)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=100)
    phone: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserProfileUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=150)
    phone: Optional[str] = None

class PasswordChange(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=6, max_length=100)

class UserResponse(BaseModel):
    id: int
    full_name: str
    email: str
    phone: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# ----------------- Medicine Schemas -----------------
class MedicineBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)
    dosage: str = Field(..., min_length=1, max_length=100)
    medicine_type: str = Field(default="Tablet") # Tablet, Capsule, Syrup, Injection, Drops, Other
    start_date: date
    end_date: Optional[date] = None
    reminder_time: str # "HH:MM" or "HH:MM:SS"
    before_after_food: str = Field(default="after_food") # before_food, after_food, with_food, no_matter
    instructions: Optional[str] = None
    frequency: Optional[str] = "Once Daily" # Once Daily, Twice Daily, Three Times Daily, etc.

class MedicineCreate(MedicineBase):
    pass

class MedicineUpdate(BaseModel):
    name: Optional[str] = None
    dosage: Optional[str] = None
    medicine_type: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    reminder_time: Optional[str] = None
    before_after_food: Optional[str] = None
    instructions: Optional[str] = None
    is_active: Optional[bool] = None

class MedicineResponse(BaseModel):
    id: int
    user_id: int
    name: str
    dosage: str
    medicine_type: str
    start_date: date
    end_date: Optional[date] = None
    reminder_time: str
    before_after_food: str
    instructions: Optional[str] = None
    is_active: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ----------------- Schedule Schemas -----------------
class ScheduleCreate(BaseModel):
    medicine_id: int
    day_of_week: str = "Daily" # Daily, Monday...
    time_slot: str # Morning, Afternoon, Evening, Night
    reminder_time: str # "HH:MM"
    dosage: Optional[str] = None

class ScheduleResponse(BaseModel):
    id: int
    medicine_id: int
    medicine_name: Optional[str] = None
    user_id: int
    day_of_week: str
    time_slot: str
    reminder_time: str
    dosage: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class DailyScheduleSection(BaseModel):
    time_slot: str # Morning, Afternoon, Evening, Night
    items: List[dict]


# ----------------- Reminder & History Schemas -----------------
class ReminderAction(BaseModel):
    medicine_id: int
    scheduled_date: Optional[date] = None
    scheduled_time: Optional[str] = None
    notes: Optional[str] = None

class ReminderItem(BaseModel):
    medicine_id: int
    medicine_name: str
    dosage: str
    medicine_type: str
    before_after_food: str
    instructions: Optional[str] = None
    scheduled_date: str
    scheduled_time: str
    display_time: str
    status: str # "upcoming", "due", "taken", "skipped", "missed"
    schedule_id: Optional[int] = None

class HistoryItemResponse(BaseModel):
    id: int
    medicine_id: int
    medicine_name: str
    dosage: str
    medicine_type: str
    scheduled_date: date
    scheduled_time: str
    status: str
    notes: Optional[str] = None
    action_time: Optional[datetime] = None

    class Config:
        from_attributes = True


# ----------------- Dashboard Stats Schemas -----------------
class DashboardStats(BaseModel):
    total_medicines: int
    today_medicines: int
    completed_doses: int
    pending_doses: int
    upcoming_reminders: List[ReminderItem]
    completion_rate: int
