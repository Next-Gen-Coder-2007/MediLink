from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
import enum
from app import app

db = SQLAlchemy(app)

# Enums for better data integrity
class UserRole(enum.Enum):
    ADMIN = "admin"
    DOCTOR = "doctor"
    NURSE = "nurse"
    LAB_TECHNICIAN = "lab_technician"
    PHARMACIST = "pharmacist"
    PATIENT = "patient"

class Gender(enum.Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"

class AppointmentStatus(enum.Enum):
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"

class PatientStatus(enum.Enum):
    ADMITTED = "admitted"
    DISCHARGED = "discharged"
    UNDER_OBSERVATION = "under_observation"
    EMERGENCY = "emergency"
    OUTPATIENT = "outpatient"

class LabTestStatus(enum.Enum):
    REQUESTED = "requested"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class PrescriptionStatus(enum.Enum):
    PRESCRIBED = "prescribed"
    FULFILLED = "fulfilled"
    PARTIALLY_FULFILLED = "partially_fulfilled"
    CANCELLED = "cancelled"

class BillStatus(enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    PARTIALLY_PAID = "partially_paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"

# Core User Management
class User(db.Model, UserMixin):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum(UserRole), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    photo = db.Column(db.Text)

    # Relationships
    doctor_profile = db.relationship("Doctor", back_populates="user", uselist=False)
    nurse_profile = db.relationship("Nurse", back_populates="user", uselist=False)
    lab_technician_profile = db.relationship("LabTechnician", back_populates="user", uselist=False)
    pharmacist_profile = db.relationship("Pharmacist", back_populates="user", uselist=False)
    patient_profile = db.relationship("Patient", back_populates="user", uselist=False)

# Hospital Structure
class Department(db.Model):
    __tablename__ = 'departments'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    head_doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    head_doctor = db.relationship("Doctor", foreign_keys=[head_doctor_id])
    doctors = db.relationship("Doctor", back_populates="department", foreign_keys="Doctor.department_id")
    nurses = db.relationship("Nurse", back_populates="department")

class Ward(db.Model):
    __tablename__ = 'wards'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'))
    capacity = db.Column(db.Integer, nullable=False)
    current_occupancy = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    department = db.relationship("Department")
    nurses = db.relationship("Nurse", back_populates="ward")
    patient_admissions = db.relationship("PatientAdmission", back_populates="ward")

# Staff Profiles
class Doctor(db.Model):
    __tablename__ = 'doctors'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True)
    license_number = db.Column(db.String(50), unique=True, nullable=False)
    specialization = db.Column(db.String(100))
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'))
    qualification = db.Column(db.String(200))
    experience_years = db.Column(db.Integer)
    consultation_fee = db.Column(db.Numeric(10, 2))
    is_available = db.Column(db.Boolean, default=True)
    
    # Relationships
    user = db.relationship("User", back_populates="doctor_profile")
    department = db.relationship("Department", back_populates="doctors", foreign_keys=[department_id])
    appointments = db.relationship("Appointment", back_populates="doctor")
    prescriptions = db.relationship("Prescription", back_populates="doctor")
    diagnoses = db.relationship("Diagnosis", back_populates="doctor")

class Nurse(db.Model):
    __tablename__ = 'nurses'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True)
    license_number = db.Column(db.String(50), unique=True)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'))
    ward_id = db.Column(db.Integer, db.ForeignKey('wards.id'))
    shift = db.Column(db.String(20))  # morning, evening, night
    is_available = db.Column(db.Boolean, default=True)
    
    # Relationships
    user = db.relationship("User", back_populates="nurse_profile")
    department = db.relationship("Department", back_populates="nurses")
    ward = db.relationship("Ward", back_populates="nurses")
    vital_records = db.relationship("VitalRecord", back_populates="nurse")

class LabTechnician(db.Model):
    __tablename__ = 'lab_technicians'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True)
    license_number = db.Column(db.String(50))
    specialization = db.Column(db.String(100))
    is_available = db.Column(db.Boolean, default=True)
    
    # Relationships
    user = db.relationship("User", back_populates="lab_technician_profile")
    lab_tests = db.relationship("LabTest", back_populates="technician")

class Pharmacist(db.Model):
    __tablename__ = 'pharmacists'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True)
    license_number = db.Column(db.String(50), unique=True)
    is_available = db.Column(db.Boolean, default=True)
    
    # Relationships
    user = db.relationship("User", back_populates="pharmacist_profile")
    prescription_fulfillments = db.relationship("PrescriptionFulfillment", back_populates="pharmacist")

# Patient Management
class Patient(db.Model):
    __tablename__ = 'patients'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True)
    patient_id = db.Column(db.String(20), unique=True, nullable=False)
    date_of_birth = db.Column(db.Date)
    gender = db.Column(db.Enum(Gender))
    blood_group = db.Column(db.String(5))
    address = db.Column(db.Text)
    emergency_contact_name = db.Column(db.String(100))
    emergency_contact_phone = db.Column(db.String(20))
    insurance_number = db.Column(db.String(50))
    status = db.Column(db.Enum(PatientStatus), default=PatientStatus.OUTPATIENT)
    registered_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship("User", back_populates="patient_profile")
    appointments = db.relationship("Appointment", back_populates="patient")
    admissions = db.relationship("PatientAdmission", back_populates="patient")
    vital_records = db.relationship("VitalRecord", back_populates="patient")
    diagnoses = db.relationship("Diagnosis", back_populates="patient")
    prescriptions = db.relationship("Prescription", back_populates="patient")
    lab_tests = db.relationship("LabTest", back_populates="patient")
    bills = db.relationship("Bill", back_populates="patient")

class PatientAdmission(db.Model):
    __tablename__ = 'patient_admissions'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'))
    ward_id = db.Column(db.Integer, db.ForeignKey('wards.id'))
    bed_number = db.Column(db.String(10))
    admission_date = db.Column(db.DateTime, default=datetime.utcnow)
    discharge_date = db.Column(db.DateTime)
    reason = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    patient = db.relationship("Patient", back_populates="admissions")
    ward = db.relationship("Ward", back_populates="patient_admissions")

# Appointments
class Appointment(db.Model):
    __tablename__ = 'appointments'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'))
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'))
    appointment_date = db.Column(db.Date, nullable=False)
    appointment_time = db.Column(db.Time, nullable=False)
    status = db.Column(db.Enum(AppointmentStatus), default=AppointmentStatus.SCHEDULED)
    reason = db.Column(db.Text)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    patient = db.relationship("Patient", back_populates="appointments")
    doctor = db.relationship("Doctor", back_populates="appointments")

# Medical Records
class VitalRecord(db.Model):
    __tablename__ = 'vital_records'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'))
    nurse_id = db.Column(db.Integer, db.ForeignKey('nurses.id'))
    temperature = db.Column(db.Numeric(4, 1))  # Celsius
    blood_pressure_systolic = db.Column(db.Integer)
    blood_pressure_diastolic = db.Column(db.Integer)
    heart_rate = db.Column(db.Integer)
    respiratory_rate = db.Column(db.Integer)
    oxygen_saturation = db.Column(db.Numeric(5, 2))
    weight = db.Column(db.Numeric(5, 2))  # kg
    height = db.Column(db.Numeric(5, 2))  # cm
    notes = db.Column(db.Text)
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    patient = db.relationship("Patient", back_populates="vital_records")
    nurse = db.relationship("Nurse", back_populates="vital_records")

class Diagnosis(db.Model):
    __tablename__ = 'diagnoses'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'))
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'))
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id'))
    diagnosis_code = db.Column(db.String(20))  # ICD-10 code
    diagnosis_description = db.Column(db.Text, nullable=False)
    symptoms = db.Column(db.Text)
    treatment_plan = db.Column(db.Text)
    follow_up_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    patient = db.relationship("Patient", back_populates="diagnoses")
    doctor = db.relationship("Doctor", back_populates="diagnoses")
    appointment = db.relationship("Appointment")

# Pharmacy Management
class Medicine(db.Model):
    __tablename__ = 'medicines'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    generic_name = db.Column(db.String(200))
    manufacturer = db.Column(db.String(100))
    dosage_form = db.Column(db.String(50))  # tablet, capsule, syrup, etc.
    strength = db.Column(db.String(50))  # 500mg, 10ml, etc.
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    stock_entries = db.relationship("MedicineStock", back_populates="medicine")
    prescription_items = db.relationship("PrescriptionItem", back_populates="medicine")

class MedicineStock(db.Model):
    __tablename__ = 'medicine_stock'
    
    id = db.Column(db.Integer, primary_key=True)
    medicine_id = db.Column(db.Integer, db.ForeignKey('medicines.id'))
    batch_number = db.Column(db.String(50), nullable=False)
    expiry_date = db.Column(db.Date, nullable=False)
    quantity_received = db.Column(db.Integer, nullable=False)
    quantity_available = db.Column(db.Integer, nullable=False)
    unit_cost = db.Column(db.Numeric(10, 2))
    supplier = db.Column(db.String(100))
    received_date = db.Column(db.Date, default=datetime.utcnow)
    
    # Relationships
    medicine = db.relationship("Medicine", back_populates="stock_entries")

class Prescription(db.Model):
    __tablename__ = 'prescriptions'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'))
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'))
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id'))
    prescription_date = db.Column(db.Date, default=datetime.utcnow)
    status = db.Column(db.Enum(PrescriptionStatus), default=PrescriptionStatus.PRESCRIBED)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    patient = db.relationship("Patient", back_populates="prescriptions")
    doctor = db.relationship("Doctor", back_populates="prescriptions")
    appointment = db.relationship("Appointment")
    items = db.relationship("PrescriptionItem", back_populates="prescription")
    fulfillments = db.relationship("PrescriptionFulfillment", back_populates="prescription")

class PrescriptionItem(db.Model):
    __tablename__ = 'prescription_items'
    
    id = db.Column(db.Integer, primary_key=True)
    prescription_id = db.Column(db.Integer, db.ForeignKey('prescriptions.id'))
    medicine_id = db.Column(db.Integer, db.ForeignKey('medicines.id'))
    dosage = db.Column(db.String(100), nullable=False)  # "1 tablet twice daily"
    quantity = db.Column(db.Integer, nullable=False)
    duration_days = db.Column(db.Integer)
    instructions = db.Column(db.Text)
    
    # Relationships
    prescription = db.relationship("Prescription", back_populates="items")
    medicine = db.relationship("Medicine", back_populates="prescription_items")

class PrescriptionFulfillment(db.Model):
    __tablename__ = 'prescription_fulfillments'
    
    id = db.Column(db.Integer, primary_key=True)
    prescription_id = db.Column(db.Integer, db.ForeignKey('prescriptions.id'))
    pharmacist_id = db.Column(db.Integer, db.ForeignKey('pharmacists.id'))
    fulfilled_date = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text)
    
    # Relationships
    prescription = db.relationship("Prescription", back_populates="fulfillments")
    pharmacist = db.relationship("Pharmacist", back_populates="prescription_fulfillments")

# Laboratory Management
class LabTestType(db.Model):
    __tablename__ = 'lab_test_types'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    normal_range = db.Column(db.String(100))
    unit = db.Column(db.String(20))
    sample_type = db.Column(db.String(50))  # blood, urine, stool, etc.
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    lab_tests = db.relationship("LabTest", back_populates="test_type")

class LabTest(db.Model):
    __tablename__ = 'lab_tests'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'))
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'))
    technician_id = db.Column(db.Integer, db.ForeignKey('lab_technicians.id'))
    test_type_id = db.Column(db.Integer, db.ForeignKey('lab_test_types.id'))
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id'))
    requested_date = db.Column(db.DateTime, default=datetime.utcnow)
    sample_collected_date = db.Column(db.DateTime)
    completed_date = db.Column(db.DateTime)
    status = db.Column(db.Enum(LabTestStatus), default=LabTestStatus.REQUESTED)
    result_value = db.Column(db.String(100))
    result_notes = db.Column(db.Text)
    result_file_path = db.Column(db.String(500))  # Path to uploaded PDF/image
    is_abnormal = db.Column(db.Boolean, default=False)
    
    # Relationships
    patient = db.relationship("Patient", back_populates="lab_tests")
    doctor = db.relationship("Doctor")
    technician = db.relationship("LabTechnician", back_populates="lab_tests")
    test_type = db.relationship("LabTestType", back_populates="lab_tests")
    appointment = db.relationship("Appointment")

# Billing System
class Bill(db.Model):
    __tablename__ = 'bills'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'))
    bill_number = db.Column(db.String(50), unique=True, nullable=False)
    bill_date = db.Column(db.Date, default=datetime.utcnow)
    total_amount = db.Column(db.Numeric(12, 2), nullable=False)
    paid_amount = db.Column(db.Numeric(12, 2), default=0)
    discount_amount = db.Column(db.Numeric(12, 2), default=0)
    status = db.Column(db.Enum(BillStatus), default=BillStatus.PENDING)
    due_date = db.Column(db.Date)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    patient = db.relationship("Patient", back_populates="bills")
    items = db.relationship("BillItem", back_populates="bill")
    payments = db.relationship("Payment", back_populates="bill")

class BillItem(db.Model):
    __tablename__ = 'bill_items'
    
    id = db.Column(db.Integer, primary_key=True)
    bill_id = db.Column(db.Integer, db.ForeignKey('bills.id'))
    description = db.Column(db.String(200), nullable=False)
    item_type = db.Column(db.String(50))  # consultation, medicine, lab_test, procedure
    quantity = db.Column(db.Integer, default=1)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    total_price = db.Column(db.Numeric(10, 2), nullable=False)
    reference_id = db.Column(db.Integer)  # ID of related appointment, prescription, lab_test
    
    # Relationships
    bill = db.relationship("Bill", back_populates="items")

class Payment(db.Model):
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    bill_id = db.Column(db.Integer, db.ForeignKey('bills.id'))
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    payment_method = db.Column(db.String(50))  # cash, card, online, insurance
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)
    transaction_reference = db.Column(db.String(100))
    notes = db.Column(db.Text)
    
    # Relationships
    bill = db.relationship("Bill", back_populates="payments")

# System Configuration and Analytics
class SystemConfig(db.Model):
    __tablename__ = 'system_config'
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text)
    description = db.Column(db.Text)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    action = db.Column(db.String(100), nullable=False)
    table_name = db.Column(db.String(50))
    record_id = db.Column(db.Integer)
    old_values = db.Column(db.Text)  # JSON string
    new_values = db.Column(db.Text)  # JSON string
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship("User")