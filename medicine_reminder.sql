-- ===================================================================
-- Medicine Schedule Reminder System - Database Schema
-- Database: medicine_reminder_db
-- ===================================================================

CREATE DATABASE IF NOT EXISTS medicine_reminder_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE medicine_reminder_db;

-- 1. Users Table
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(150) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    phone VARCHAR(30) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. Medicines Table
CREATE TABLE IF NOT EXISTS medicines (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    name VARCHAR(150) NOT NULL,
    dosage VARCHAR(100) NOT NULL,
    medicine_type VARCHAR(50) NOT NULL DEFAULT 'Tablet', -- Tablet, Capsule, Syrup, Injection, Drops, Ointment, Inhaler, Other
    start_date DATE NOT NULL,
    end_date DATE NULL,
    reminder_time TIME NOT NULL,
    before_after_food VARCHAR(50) NOT NULL DEFAULT 'after_food', -- before_food, after_food, with_food, no_matter
    instructions TEXT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_medicines_user (user_id),
    INDEX idx_medicines_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. Medicine Schedules Table
CREATE TABLE IF NOT EXISTS medicine_schedules (
    id INT AUTO_INCREMENT PRIMARY KEY,
    medicine_id INT NOT NULL,
    user_id INT NOT NULL,
    day_of_week VARCHAR(20) NOT NULL DEFAULT 'Daily', -- Daily, Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday
    time_slot VARCHAR(30) NOT NULL, -- Morning, Afternoon, Evening, Night
    reminder_time TIME NOT NULL,
    dosage VARCHAR(100) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (medicine_id) REFERENCES medicines(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_schedules_user (user_id),
    INDEX idx_schedules_med (medicine_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4. Medicine History / Logs Table
CREATE TABLE IF NOT EXISTS medicine_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    medicine_id INT NOT NULL,
    user_id INT NOT NULL,
    schedule_id INT NULL,
    scheduled_date DATE NOT NULL,
    scheduled_time TIME NOT NULL,
    status ENUM('taken', 'skipped', 'missed') NOT NULL DEFAULT 'taken',
    notes TEXT NULL,
    action_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (medicine_id) REFERENCES medicines(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (schedule_id) REFERENCES medicine_schedules(id) ON DELETE SET NULL,
    UNIQUE KEY unique_user_med_time (user_id, medicine_id, scheduled_date, scheduled_time),
    INDEX idx_history_user_date (user_id, scheduled_date),
    INDEX idx_history_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
