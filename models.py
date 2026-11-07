from datetime import datetime, date, time
from sqlalchemy import Column, Integer, String, Text, Date, Time, Boolean, ForeignKey, Enum, TIMESTAMP
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    full_name = Column(String(150), nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    phone = Column(String(30), nullable=True)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    medicines = relationship("Medicine", back_populates="user", cascade="all, delete-orphan")
    schedules = relationship("MedicineSchedule", back_populates="user", cascade="all, delete-orphan")
    history = relationship("MedicineHistory", back_populates="user", cascade="all, delete-orphan")


class Medicine(Base):
    __tablename__ = "medicines"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(150), nullable=False)
    dosage = Column(String(100), nullable=False)
    medicine_type = Column(String(50), nullable=False, default="Tablet")
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    reminder_time = Column(Time, nullable=False)
    before_after_food = Column(String(50), nullable=False, default="after_food") # before_food, after_food, with_food, no_matter
    instructions = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="medicines")
    schedules = relationship("MedicineSchedule", back_populates="medicine", cascade="all, delete-orphan")
    history = relationship("MedicineHistory", back_populates="medicine", cascade="all, delete-orphan")


class MedicineSchedule(Base):
    __tablename__ = "medicine_schedules"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    medicine_id = Column(Integer, ForeignKey("medicines.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    day_of_week = Column(String(20), nullable=False, default="Daily") # Daily, Monday, ...
    time_slot = Column(String(30), nullable=False) # Morning, Afternoon, Evening, Night
    reminder_time = Column(Time, nullable=False)
    dosage = Column(String(100), nullable=True)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

    # Relationships
    medicine = relationship("Medicine", back_populates="schedules")
    user = relationship("User", back_populates="schedules")
    history = relationship("MedicineHistory", back_populates="schedule")


class MedicineHistory(Base):
    __tablename__ = "medicine_history"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    medicine_id = Column(Integer, ForeignKey("medicines.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    schedule_id = Column(Integer, ForeignKey("medicine_schedules.id", ondelete="SET NULL"), nullable=True)
    scheduled_date = Column(Date, nullable=False, index=True)
    scheduled_time = Column(Time, nullable=False)
    status = Column(Enum("taken", "skipped", "missed"), nullable=False, default="taken", index=True)
    notes = Column(Text, nullable=True)
    action_time = Column(TIMESTAMP, default=datetime.utcnow)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

    # Relationships
    medicine = relationship("Medicine", back_populates="history")
    user = relationship("User", back_populates="history")
    schedule = relationship("MedicineSchedule", back_populates="history")
