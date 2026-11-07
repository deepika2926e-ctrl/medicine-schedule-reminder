import os
from datetime import datetime, date, time, timedelta
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, and_

from database import engine, get_db, Base
import models
import schemas
import auth
from routes import auth_routes

# Create database tables if they do not exist
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Medicine Schedule Reminder System API",
    description="Full-featured REST API for Medicine Schedule Reminder Web Application",
    version="1.0.0"
)

# Enable CORS for all origins (supports both local server and direct file/localhost access)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Authentication Routes
app.include_router(auth_routes.router)

# ----------------- Helper Functions -----------------
def parse_time_str(time_str: str) -> time:
    clean = time_str.strip()
    parts = clean.split(":")
    if len(parts) >= 2:
        return time(int(parts[0]), int(parts[1]), int(parts[2]) if len(parts) > 2 else 0)
    raise ValueError("Invalid time format. Expected HH:MM or HH:MM:SS")

def determine_time_slot(reminder_time: time) -> str:
    hour = reminder_time.hour
    if 5 <= hour < 12:
        return "Morning"
    elif 12 <= hour < 17:
        return "Afternoon"
    elif 17 <= hour < 21:
        return "Evening"
    else:
        return "Night"

def format_time_display(t: time) -> str:
    # 12-hour format with AM/PM
    return t.strftime("%I:%M %p")


# =====================================================
# 1. MEDICINES ENDPOINTS
# =====================================================

@app.post("/api/medicines/", response_model=schemas.MedicineResponse, status_code=status.HTTP_201_CREATED, tags=["Medicines"])
def create_medicine(
    payload: schemas.MedicineCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    try:
        t = parse_time_str(payload.reminder_time)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    if payload.end_date and payload.end_date < payload.start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="End date cannot be earlier than start date."
        )

    medicine = models.Medicine(
        user_id=current_user.id,
        name=payload.name.strip(),
        dosage=payload.dosage.strip(),
        medicine_type=payload.medicine_type.strip(),
        start_date=payload.start_date,
        end_date=payload.end_date,
        reminder_time=t,
        before_after_food=payload.before_after_food.strip(),
        instructions=payload.instructions.strip() if payload.instructions else None,
        is_active=True
    )
    db.add(medicine)
    db.commit()
    db.refresh(medicine)

    # Automatically generate schedule entries matching frequency
    freq = (payload.frequency or "Once Daily").lower()
    primary_slot = determine_time_slot(t)

    sched1 = models.MedicineSchedule(
        medicine_id=medicine.id,
        user_id=current_user.id,
        day_of_week="Daily",
        time_slot=primary_slot,
        reminder_time=t,
        dosage=medicine.dosage
    )
    db.add(sched1)

    if "twice" in freq:
        second_time = time(20, 0, 0) if t.hour < 15 else time(8, 0, 0)
        second_slot = "Night" if t.hour < 15 else "Morning"
        sched2 = models.MedicineSchedule(
            medicine_id=medicine.id,
            user_id=current_user.id,
            day_of_week="Daily",
            time_slot=second_slot,
            reminder_time=second_time,
            dosage=medicine.dosage
        )
        db.add(sched2)
    elif "three" in freq:
        sched2 = models.MedicineSchedule(
            medicine_id=medicine.id,
            user_id=current_user.id,
            day_of_week="Daily",
            time_slot="Afternoon",
            reminder_time=time(13, 0, 0),
            dosage=medicine.dosage
        )
        sched3 = models.MedicineSchedule(
            medicine_id=medicine.id,
            user_id=current_user.id,
            day_of_week="Daily",
            time_slot="Night",
            reminder_time=time(20, 30, 0),
            dosage=medicine.dosage
        )
        db.add(sched2)
        db.add(sched3)

    db.commit()

    return schemas.MedicineResponse(
        id=medicine.id,
        user_id=medicine.user_id,
        name=medicine.name,
        dosage=medicine.dosage,
        medicine_type=medicine.medicine_type,
        start_date=medicine.start_date,
        end_date=medicine.end_date,
        reminder_time=str(medicine.reminder_time)[:5],
        before_after_food=medicine.before_after_food,
        instructions=medicine.instructions,
        is_active=medicine.is_active,
        created_at=medicine.created_at
    )

@app.get("/api/medicines/", response_model=List[schemas.MedicineResponse], tags=["Medicines"])
def list_medicines(
    search: Optional[str] = Query(None),
    active_only: bool = Query(True),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    query = db.query(models.Medicine).filter(models.Medicine.user_id == current_user.id)
    if active_only:
        query = query.filter(models.Medicine.is_active == True)
    if search:
        query = query.filter(models.Medicine.name.ilike(f"%{search.strip()}%"))

    medicines = query.order_by(models.Medicine.reminder_time.asc()).all()

    return [
        schemas.MedicineResponse(
            id=m.id,
            user_id=m.user_id,
            name=m.name,
            dosage=m.dosage,
            medicine_type=m.medicine_type,
            start_date=m.start_date,
            end_date=m.end_date,
            reminder_time=str(m.reminder_time)[:5],
            before_after_food=m.before_after_food,
            instructions=m.instructions,
            is_active=m.is_active,
            created_at=m.created_at
        )
        for m in medicines
    ]

@app.get("/api/medicines/{medicine_id}", response_model=schemas.MedicineResponse, tags=["Medicines"])
def get_medicine(
    medicine_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    medicine = db.query(models.Medicine).filter(
        models.Medicine.id == medicine_id,
        models.Medicine.user_id == current_user.id
    ).first()

    if not medicine:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medicine not found.")

    return schemas.MedicineResponse(
        id=medicine.id,
        user_id=medicine.user_id,
        name=medicine.name,
        dosage=medicine.dosage,
        medicine_type=medicine.medicine_type,
        start_date=medicine.start_date,
        end_date=medicine.end_date,
        reminder_time=str(medicine.reminder_time)[:5],
        before_after_food=medicine.before_after_food,
        instructions=medicine.instructions,
        is_active=medicine.is_active,
        created_at=medicine.created_at
    )

@app.put("/api/medicines/{medicine_id}", response_model=schemas.MedicineResponse, tags=["Medicines"])
def update_medicine(
    medicine_id: int,
    payload: schemas.MedicineUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    medicine = db.query(models.Medicine).filter(
        models.Medicine.id == medicine_id,
        models.Medicine.user_id == current_user.id
    ).first()

    if not medicine:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medicine not found.")

    if payload.name is not None and payload.name.strip():
        medicine.name = payload.name.strip()
    if payload.dosage is not None and payload.dosage.strip():
        medicine.dosage = payload.dosage.strip()
    if payload.medicine_type is not None:
        medicine.medicine_type = payload.medicine_type.strip()
    if payload.start_date is not None:
        medicine.start_date = payload.start_date
    if payload.end_date is not None:
        medicine.end_date = payload.end_date
    if payload.reminder_time is not None:
        try:
            medicine.reminder_time = parse_time_str(payload.reminder_time)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    if payload.before_after_food is not None:
        medicine.before_after_food = payload.before_after_food.strip()
    if payload.instructions is not None:
        medicine.instructions = payload.instructions.strip() or None
    if payload.is_active is not None:
        medicine.is_active = payload.is_active

    db.commit()
    db.refresh(medicine)

    return schemas.MedicineResponse(
        id=medicine.id,
        user_id=medicine.user_id,
        name=medicine.name,
        dosage=medicine.dosage,
        medicine_type=medicine.medicine_type,
        start_date=medicine.start_date,
        end_date=medicine.end_date,
        reminder_time=str(medicine.reminder_time)[:5],
        before_after_food=medicine.before_after_food,
        instructions=medicine.instructions,
        is_active=medicine.is_active,
        created_at=medicine.created_at
    )

@app.delete("/api/medicines/{medicine_id}", tags=["Medicines"])
def delete_medicine(
    medicine_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    medicine = db.query(models.Medicine).filter(
        models.Medicine.id == medicine_id,
        models.Medicine.user_id == current_user.id
    ).first()

    if not medicine:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medicine not found.")

    db.delete(medicine)
    db.commit()
    return {"message": "Medicine deleted successfully."}


# =====================================================
# 2. SCHEDULES ENDPOINTS
# =====================================================

@app.post("/api/schedules/", response_model=schemas.ScheduleResponse, status_code=status.HTTP_201_CREATED, tags=["Schedules"])
def create_schedule(
    payload: schemas.ScheduleCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    med = db.query(models.Medicine).filter(
        models.Medicine.id == payload.medicine_id,
        models.Medicine.user_id == current_user.id
    ).first()
    if not med:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medicine not found.")

    try:
        t = parse_time_str(payload.reminder_time)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    schedule = models.MedicineSchedule(
        medicine_id=med.id,
        user_id=current_user.id,
        day_of_week=payload.day_of_week.strip(),
        time_slot=payload.time_slot.strip(),
        reminder_time=t,
        dosage=payload.dosage or med.dosage
    )
    db.add(schedule)
    db.commit()
    db.refresh(schedule)

    return schemas.ScheduleResponse(
        id=schedule.id,
        medicine_id=schedule.medicine_id,
        medicine_name=med.name,
        user_id=schedule.user_id,
        day_of_week=schedule.day_of_week,
        time_slot=schedule.time_slot,
        reminder_time=str(schedule.reminder_time)[:5],
        dosage=schedule.dosage,
        created_at=schedule.created_at
    )

@app.get("/api/schedules/", response_model=List[schemas.ScheduleResponse], tags=["Schedules"])
def list_schedules(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    schedules = db.query(models.MedicineSchedule).join(
        models.Medicine, models.MedicineSchedule.medicine_id == models.Medicine.id
    ).filter(
        models.MedicineSchedule.user_id == current_user.id,
        models.Medicine.is_active == True
    ).order_by(models.MedicineSchedule.reminder_time.asc()).all()

    return [
        schemas.ScheduleResponse(
            id=s.id,
            medicine_id=s.medicine_id,
            medicine_name=s.medicine.name if s.medicine else "",
            user_id=s.user_id,
            day_of_week=s.day_of_week,
            time_slot=s.time_slot,
            reminder_time=str(s.reminder_time)[:5],
            dosage=s.dosage,
            created_at=s.created_at
        )
        for s in schedules
    ]

@app.get("/api/schedules/daily", tags=["Schedules"])
def get_daily_schedule(
    target_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    today = target_date or date.today()
    day_name = today.strftime("%A")

    # Fetch active medicines valid for today
    med_query = db.query(models.MedicineSchedule).join(
        models.Medicine, models.MedicineSchedule.medicine_id == models.Medicine.id
    ).filter(
        models.MedicineSchedule.user_id == current_user.id,
        models.Medicine.is_active == True,
        models.Medicine.start_date <= today,
        or_(models.Medicine.end_date == None, models.Medicine.end_date >= today),
        or_(
            models.MedicineSchedule.day_of_week == "Daily",
            models.MedicineSchedule.day_of_week == day_name
        )
    ).order_by(models.MedicineSchedule.reminder_time.asc())

    schedules = med_query.all()

    # Fetch today's history logs
    logs = db.query(models.MedicineHistory).filter(
        models.MedicineHistory.user_id == current_user.id,
        models.MedicineHistory.scheduled_date == today
    ).all()
    log_map = {f"{l.medicine_id}_{str(l.scheduled_time)[:5]}": l.status for l in logs}

    sections = {
        "Morning": [],
        "Afternoon": [],
        "Evening": [],
        "Night": []
    }

    now_time = datetime.now().time()

    for s in schedules:
        time_key = str(s.reminder_time)[:5]
        status_val = log_map.get(f"{s.medicine_id}_{time_key}")
        if not status_val:
            if today < date.today():
                status_val = "missed"
            elif today == date.today() and s.reminder_time < now_time:
                status_val = "due"
            else:
                status_val = "upcoming"

        slot = s.time_slot if s.time_slot in sections else determine_time_slot(s.reminder_time)
        sections[slot].append({
            "schedule_id": s.id,
            "medicine_id": s.medicine_id,
            "medicine_name": s.medicine.name if s.medicine else "",
            "medicine_type": s.medicine.medicine_type if s.medicine else "Tablet",
            "dosage": s.dosage or (s.medicine.dosage if s.medicine else ""),
            "before_after_food": s.medicine.before_after_food if s.medicine else "after_food",
            "instructions": s.medicine.instructions if s.medicine else "",
            "reminder_time": time_key,
            "display_time": format_time_display(s.reminder_time),
            "status": status_val
        })

    return {
        "date": str(today),
        "day": day_name,
        "sections": sections
    }

@app.get("/api/schedules/weekly", tags=["Schedules"])
def get_weekly_schedule(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    today = date.today()
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    schedules = db.query(models.MedicineSchedule).join(
        models.Medicine, models.MedicineSchedule.medicine_id == models.Medicine.id
    ).filter(
        models.MedicineSchedule.user_id == current_user.id,
        models.Medicine.is_active == True,
        models.Medicine.start_date <= today,
        or_(models.Medicine.end_date == None, models.Medicine.end_date >= today)
    ).order_by(models.MedicineSchedule.reminder_time.asc()).all()

    weekly_map = {d: [] for d in days}
    for s in schedules:
        item = {
            "schedule_id": s.id,
            "medicine_id": s.medicine_id,
            "medicine_name": s.medicine.name if s.medicine else "",
            "dosage": s.dosage or (s.medicine.dosage if s.medicine else ""),
            "time_slot": s.time_slot,
            "reminder_time": str(s.reminder_time)[:5],
            "display_time": format_time_display(s.reminder_time),
            "day_of_week": s.day_of_week
        }
        if s.day_of_week == "Daily":
            for d in days:
                weekly_map[d].append(item)
        elif s.day_of_week in weekly_map:
            weekly_map[s.day_of_week].append(item)

    return {"days": weekly_map}

@app.delete("/api/schedules/{schedule_id}", tags=["Schedules"])
def delete_schedule(
    schedule_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    sched = db.query(models.MedicineSchedule).filter(
        models.MedicineSchedule.id == schedule_id,
        models.MedicineSchedule.user_id == current_user.id
    ).first()
    if not sched:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Schedule not found.")

    db.delete(sched)
    db.commit()
    return {"message": "Schedule removed."}


# =====================================================
# 3. REMINDERS ENDPOINTS
# =====================================================

@app.get("/api/reminders/upcoming", response_model=List[schemas.ReminderItem], tags=["Reminders"])
def get_upcoming_reminders(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    today = date.today()
    day_name = today.strftime("%A")
    now_time = datetime.now().time()

    schedules = db.query(models.MedicineSchedule).join(
        models.Medicine, models.MedicineSchedule.medicine_id == models.Medicine.id
    ).filter(
        models.MedicineSchedule.user_id == current_user.id,
        models.Medicine.is_active == True,
        models.Medicine.start_date <= today,
        or_(models.Medicine.end_date == None, models.Medicine.end_date >= today),
        or_(
            models.MedicineSchedule.day_of_week == "Daily",
            models.MedicineSchedule.day_of_week == day_name
        )
    ).order_by(models.MedicineSchedule.reminder_time.asc()).all()

    logs = db.query(models.MedicineHistory).filter(
        models.MedicineHistory.user_id == current_user.id,
        models.MedicineHistory.scheduled_date == today
    ).all()
    log_map = {f"{l.medicine_id}_{str(l.scheduled_time)[:5]}": l.status for l in logs}

    reminders = []
    for s in schedules:
        time_key = str(s.reminder_time)[:5]
        existing_status = log_map.get(f"{s.medicine_id}_{time_key}")

        if existing_status:
            stat = existing_status
        elif s.reminder_time <= now_time:
            stat = "due"
        else:
            stat = "upcoming"

        reminders.append(schemas.ReminderItem(
            medicine_id=s.medicine_id,
            medicine_name=s.medicine.name if s.medicine else "",
            dosage=s.dosage or (s.medicine.dosage if s.medicine else ""),
            medicine_type=s.medicine.medicine_type if s.medicine else "Tablet",
            before_after_food=s.medicine.before_after_food if s.medicine else "after_food",
            instructions=s.medicine.instructions if s.medicine else None,
            scheduled_date=str(today),
            scheduled_time=time_key,
            display_time=format_time_display(s.reminder_time),
            status=stat,
            schedule_id=s.id
        ))

    return reminders

@app.post("/api/reminders/taken", tags=["Reminders"])
def mark_reminder_taken(
    payload: schemas.ReminderAction,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    today = payload.scheduled_date or date.today()
    med = db.query(models.Medicine).filter(
        models.Medicine.id == payload.medicine_id,
        models.Medicine.user_id == current_user.id
    ).first()
    if not med:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medicine not found.")

    if payload.scheduled_time:
        try:
            t = parse_time_str(payload.scheduled_time)
        except ValueError:
            t = med.reminder_time
    else:
        t = med.reminder_time

    # Upsert in medicine_history
    existing = db.query(models.MedicineHistory).filter(
        models.MedicineHistory.user_id == current_user.id,
        models.MedicineHistory.medicine_id == med.id,
        models.MedicineHistory.scheduled_date == today,
        models.MedicineHistory.scheduled_time == t
    ).first()

    if existing:
        existing.status = "taken"
        existing.action_time = datetime.utcnow()
        if payload.notes:
            existing.notes = payload.notes.strip()
    else:
        history = models.MedicineHistory(
            medicine_id=med.id,
            user_id=current_user.id,
            scheduled_date=today,
            scheduled_time=t,
            status="taken",
            notes=payload.notes.strip() if payload.notes else None,
            action_time=datetime.utcnow()
        )
        db.add(history)

    db.commit()
    return {"message": f"{med.name} marked as Taken.", "status": "taken"}

@app.post("/api/reminders/skipped", tags=["Reminders"])
def mark_reminder_skipped(
    payload: schemas.ReminderAction,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    today = payload.scheduled_date or date.today()
    med = db.query(models.Medicine).filter(
        models.Medicine.id == payload.medicine_id,
        models.Medicine.user_id == current_user.id
    ).first()
    if not med:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medicine not found.")

    if payload.scheduled_time:
        try:
            t = parse_time_str(payload.scheduled_time)
        except ValueError:
            t = med.reminder_time
    else:
        t = med.reminder_time

    existing = db.query(models.MedicineHistory).filter(
        models.MedicineHistory.user_id == current_user.id,
        models.MedicineHistory.medicine_id == med.id,
        models.MedicineHistory.scheduled_date == today,
        models.MedicineHistory.scheduled_time == t
    ).first()

    if existing:
        existing.status = "skipped"
        existing.action_time = datetime.utcnow()
        if payload.notes:
            existing.notes = payload.notes.strip()
    else:
        history = models.MedicineHistory(
            medicine_id=med.id,
            user_id=current_user.id,
            scheduled_date=today,
            scheduled_time=t,
            status="skipped",
            notes=payload.notes.strip() if payload.notes else None,
            action_time=datetime.utcnow()
        )
        db.add(history)

    db.commit()
    return {"message": f"{med.name} marked as Skipped.", "status": "skipped"}


# =====================================================
# 4. HISTORY ENDPOINTS
# =====================================================

@app.get("/api/history/", response_model=List[schemas.HistoryItemResponse], tags=["History"])
def get_history(
    status_filter: Optional[str] = Query(None), # taken, skipped, missed
    date_filter: Optional[date] = Query(None),
    medicine_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    query = db.query(models.MedicineHistory).join(
        models.Medicine, models.MedicineHistory.medicine_id == models.Medicine.id
    ).filter(models.MedicineHistory.user_id == current_user.id)

    if status_filter:
        query = query.filter(models.MedicineHistory.status == status_filter.lower().strip())
    if date_filter:
        query = query.filter(models.MedicineHistory.scheduled_date == date_filter)
    if medicine_id:
        query = query.filter(models.MedicineHistory.medicine_id == medicine_id)

    records = query.order_by(
        models.MedicineHistory.scheduled_date.desc(),
        models.MedicineHistory.scheduled_time.desc()
    ).all()

    return [
        schemas.HistoryItemResponse(
            id=r.id,
            medicine_id=r.medicine_id,
            medicine_name=r.medicine.name if r.medicine else "Unknown",
            dosage=r.medicine.dosage if r.medicine else "",
            medicine_type=r.medicine.medicine_type if r.medicine else "Tablet",
            scheduled_date=r.scheduled_date,
            scheduled_time=str(r.scheduled_time)[:5],
            status=r.status,
            notes=r.notes,
            action_time=r.action_time
        )
        for r in records
    ]

@app.delete("/api/history/{history_id}", tags=["History"])
def delete_history_item(
    history_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    rec = db.query(models.MedicineHistory).filter(
        models.MedicineHistory.id == history_id,
        models.MedicineHistory.user_id == current_user.id
    ).first()
    if not rec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="History record not found.")

    db.delete(rec)
    db.commit()
    return {"message": "History record deleted."}


# =====================================================
# 5. DASHBOARD STATS ENDPOINT
# =====================================================

@app.get("/api/dashboard/stats", response_model=schemas.DashboardStats, tags=["Dashboard"])
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    today = date.today()
    day_name = today.strftime("%A")
    now_time = datetime.now().time()

    # Total active medicines
    total_meds = db.query(models.Medicine).filter(
        models.Medicine.user_id == current_user.id,
        models.Medicine.is_active == True
    ).count()

    # Today's scheduled doses
    today_scheds = db.query(models.MedicineSchedule).join(
        models.Medicine, models.MedicineSchedule.medicine_id == models.Medicine.id
    ).filter(
        models.MedicineSchedule.user_id == current_user.id,
        models.Medicine.is_active == True,
        models.Medicine.start_date <= today,
        or_(models.Medicine.end_date == None, models.Medicine.end_date >= today),
        or_(
            models.MedicineSchedule.day_of_week == "Daily",
            models.MedicineSchedule.day_of_week == day_name
        )
    ).order_by(models.MedicineSchedule.reminder_time.asc()).all()

    today_count = len(today_scheds)

    # History logs for today
    today_logs = db.query(models.MedicineHistory).filter(
        models.MedicineHistory.user_id == current_user.id,
        models.MedicineHistory.scheduled_date == today
    ).all()

    log_map = {f"{l.medicine_id}_{str(l.scheduled_time)[:5]}": l.status for l in today_logs}

    completed_count = sum(1 for l in today_logs if l.status == "taken")
    skipped_count = sum(1 for l in today_logs if l.status == "skipped")
    pending_count = max(0, today_count - completed_count - skipped_count)

    upcoming_list = []
    for s in today_scheds:
        time_key = str(s.reminder_time)[:5]
        existing_status = log_map.get(f"{s.medicine_id}_{time_key}")
        if existing_status:
            stat = existing_status
        elif s.reminder_time <= now_time:
            stat = "due"
        else:
            stat = "upcoming"

        upcoming_list.append(schemas.ReminderItem(
            medicine_id=s.medicine_id,
            medicine_name=s.medicine.name if s.medicine else "",
            dosage=s.dosage or (s.medicine.dosage if s.medicine else ""),
            medicine_type=s.medicine.medicine_type if s.medicine else "Tablet",
            before_after_food=s.medicine.before_after_food if s.medicine else "after_food",
            instructions=s.medicine.instructions if s.medicine else None,
            scheduled_date=str(today),
            scheduled_time=time_key,
            display_time=format_time_display(s.reminder_time),
            status=stat,
            schedule_id=s.id
        ))

    rate = round((completed_count / today_count * 100)) if today_count > 0 else 0

    return schemas.DashboardStats(
        total_medicines=total_meds,
        today_medicines=today_count,
        completed_doses=completed_count,
        pending_doses=pending_count,
        upcoming_reminders=upcoming_list,
        completion_rate=rate
    )


# =====================================================
# 6. STATIC FILE SERVING FOR FRONTEND
# =====================================================

frontend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))

if os.path.exists(frontend_path):
    css_path = os.path.join(frontend_path, "css")
    js_path = os.path.join(frontend_path, "js")
    assets_path = os.path.join(frontend_path, "assets")

    if os.path.exists(css_path):
        app.mount("/css", StaticFiles(directory=css_path), name="css")
    if os.path.exists(js_path):
        app.mount("/js", StaticFiles(directory=js_path), name="js")
    if os.path.exists(assets_path):
        app.mount("/assets", StaticFiles(directory=assets_path), name="assets")
    
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")

    @app.get("/")
    def serve_home():
        index_file = os.path.join(frontend_path, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        return {"message": "Medicine Schedule Reminder System Backend is running."}

    @app.get("/{page_name}.html")
    def serve_html_page(page_name: str):
        file_path = os.path.join(frontend_path, f"{page_name}.html")
        if os.path.exists(file_path):
            return FileResponse(file_path)
        raise HTTPException(status_code=404, detail="Page not found")
