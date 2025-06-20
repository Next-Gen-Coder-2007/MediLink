from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, abort, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
import enum
from PIL import Image
import io
import base64
import json
from decimal import Decimal

def compress_and_encode_image(photo, quality=40, max_width=800):
    if not photo:
        return None
    img = Image.open(photo)
    if img.mode == 'RGBA':
        img = img.convert('RGB')
    if img.width > max_width:
        ratio = max_width / float(img.width)
        new_height = int(img.height * ratio)
        img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
    img_io = io.BytesIO()
    img.save(img_io, format='JPEG', quality=quality, optimize=True)
    img_io.seek(0)
    image_base64 = base64.b64encode(img_io.read()).decode('utf-8')
    return image_base64
def model_to_dict(model):
    result = {}
    for column in model.__table__.columns:
        value = getattr(model, column.name)

        # Handle enums
        if isinstance(value, enum.Enum):
            value = value.name

        # Handle datetime
        elif isinstance(value, datetime):
            value = value.isoformat()  # or strftime

        # Handle Decimal
        elif isinstance(value, Decimal):
            value = float(value)  # or str(value) if precision matters

        result[column.name] = value
    return result

app = Flask(__name__, template_folder="../frontend")
app.secret_key = 'secret-code'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hospital.db'

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.init_app(app)
login_manager.login_view = 'login'

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
    email = db.Column(db.String(100), nullable=False)
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

def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role not in roles:
                flash("You don't have permission to access this page.", "warning")
                return redirect(request.referrer or url_for('home'))
            return f(*args, **kwargs)
        return wrapper
    return decorator

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route("/")
def home():
    if current_user.is_authenticated:
        logout_user()
    return render_template("home.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        logout_user()
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Query the database for the user
        user = User.query.filter_by(username=username).first()
        # Check if the user exists and the password is correct
        if user and user.password_hash == password:
            login_user(user)
            flash('Logged in successfully!','success')

            # Redirect based on user role
            if user.role == UserRole.ADMIN:
                return redirect(url_for('admin'))
            elif user.role == UserRole.DOCTOR:
                return redirect(url_for('doctor'))
            elif user.role == UserRole.NURSE:
                return redirect(url_for('nurse_dashboard'))
            elif user.role == UserRole.LAB_TECHNICIAN:
                return redirect(url_for('lab_technician_dashboard'))
            elif user.role == UserRole.PHARMACIST:
                return redirect(url_for('pharmacist_dashboard'))
            elif user.role == UserRole.PATIENT:
                user = User.query.filter_by(username=username).first()
                return redirect(url_for('patient', user_id = user.id))
        else:
            flash('Invalid username or password')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            # Core User Fields
            username = request.form['username']
            email = request.form['email']
            password_hash = request.form['password']
            first_name = request.form['first_name']
            last_name = request.form['last_name']
            phone = request.form.get('phone')

            # Patient Fields
            date_of_birth = request.form.get('date_of_birth')
            gender = request.form.get('gender')
            blood_group = request.form.get('blood_group')
            address = request.form.get('address')
            emergency_contact_name = request.form.get('emergency_contact_name')
            emergency_contact_phone = request.form.get('emergency_contact_phone')
            insurance_number = request.form.get('insurance_number')

            if gender and gender.upper() in Gender.__members__:
                gender_enum = Gender[gender.upper()]
            else:
                flash("Invalid or missing gender.", "danger")
                return redirect(url_for('register'))

            if User.query.filter_by(username=username).first() or User.query.filter_by(email=email).first():
                flash("Username or Email already exists", "danger")
                return redirect(url_for('register'))

            photo = request.files.get('photo')
            photo_data = compress_and_encode_image(photo)

            user = User(
                username=username,
                email=email,
                password_hash=password_hash,
                role=UserRole.PATIENT,
                first_name=first_name,
                last_name=last_name,
                phone=phone,
                photo=photo_data
            )
            db.session.add(user)
            db.session.flush()

            patient = Patient(
                user_id=user.id,
                date_of_birth=datetime.strptime(date_of_birth, '%Y-%m-%d') if date_of_birth else None,
                gender=gender_enum,
                blood_group=blood_group,
                address=address,
                emergency_contact_name=emergency_contact_name,
                emergency_contact_phone=emergency_contact_phone,
                insurance_number=insurance_number,
                status=PatientStatus.OUTPATIENT,
                registered_at=datetime.utcnow()
            )
            db.session.add(patient)

            db.session.commit()
            flash("Registration successful!", "success")
            return redirect(url_for('login'))

        except Exception as e:
            db.session.rollback()
            flash(f"Error during registration: {str(e)}", "danger")
            return redirect(url_for('register'))
    return render_template('register.html')

@app.route("/admin")
@login_required
@role_required(UserRole.ADMIN)
def admin():
    doctors = Doctor.query.all()
    nurses = Nurse.query.all()

    return render_template("admin/admin_home.html", doctors = doctors, nurses = nurses)

# Admin Routes for Doctor Management
@app.route('/admin/doctors')
@login_required
@role_required(UserRole.ADMIN)
def admin_doctors():
    doctors = Doctor.query.all()
    departments = Department.query.all()
    return render_template('admin/admin_doctors.html', doctors=doctors, departments = departments)

@app.route('/admin/doctors/create', methods=['GET', 'POST'])
@role_required(UserRole.ADMIN)
def admin_doctors_create():
    try:
        if request.method == 'POST':
            username = request.form['username']
            email = request.form['email']
            password_hash = request.form['password']
            first_name = request.form['first_name']
            last_name = request.form['last_name']
            phone = request.form['phone']
            photo = request.files.get('photo')

            license_number = request.form['license_number']
            specialization = request.form['specialization']
            department_id = request.form['department_id']
            qualification = request.form['qualification']
            experience_years = request.form['experience_years']
            consultation_fee = request.form['consultation_fee']

            photo_data = compress_and_encode_image(photo)
            if User.query.filter_by(username = username).first():
                flash("User name already Registered", 'warning')
                return redirect(url_for('admin_doctors'))
            
            new_user = User(
                username=username,
                email=email,
                password_hash=password_hash,
                role=UserRole.DOCTOR,
                first_name=first_name,
                last_name=last_name,
                phone=phone,
                is_active=True,
                photo=photo_data
            )
            db.session.add(new_user)
            db.session.flush()

            new_doctor = Doctor(
                user_id=new_user.id,
                license_number=license_number,
                specialization=specialization,
                department_id=department_id,
                qualification=qualification,
                experience_years=experience_years,
                consultation_fee=consultation_fee,
                is_available=True
            )
            db.session.add(new_doctor)
            user_json = [model_to_dict(new_user)]
            doctor_json = [model_to_dict(new_doctor)]
            new_audit = AuditLog(
                user_id=current_user.id,
                action="Created a Doctor",
                table_name="Doctors",
                new_values=json.dumps({
                    "user": user_json,
                    "doctor": doctor_json
                }),
                ip_address=request.headers.get('X-Forwarded-For', request.remote_addr),
                user_agent=request.headers.get('User-Agent')
            )
            db.session.add(new_audit)
            db.session.commit()
            flash('Doctor created successfully!', 'success')
            return redirect(url_for('admin_doctors'))
    except Exception as e:
        db.session.rollback()
        flash(f"Error during registration: {str(e)}", "danger")
        return redirect(url_for('admin_doctors'))

@app.route('/admin/doctors/<int:doctor_id>/edit', methods=['GET', 'POST'])
@role_required(UserRole.ADMIN, UserRole.DOCTOR)
def admin_doctors_edit(doctor_id):
    try:
        doctor = Doctor.query.get_or_404(doctor_id)
        user = User.query.get_or_404(doctor.user_id)
        user_json = model_to_dict(user)
        doctor_json = model_to_dict(doctor)
        if current_user.role == UserRole.DOCTOR and current_user.id != doctor.user_id:
            flash("Dont Access Others")
            return redirect(url_for('login'))
        if request.method == 'POST':
            # Update user information
            user.username = request.form['username']
            user.email = request.form['email']
            user.first_name = request.form['first_name']
            user.last_name = request.form['last_name']
            user.phone = request.form['phone']

            # Handle photo update if a new photo is provided
            photo = request.files.get('photo')
            if photo:
                photo_data = compress_and_encode_image(photo)
                user.photo = photo_data

            # Update doctor-specific information
            doctor.license_number = request.form['license_number']
            doctor.specialization = request.form['specialization']
            doctor.department_id = request.form['department_id']
            doctor.qualification = request.form['qualification']
            doctor.experience_years = request.form['experience_years']
            doctor.consultation_fee = request.form['consultation_fee']

            db.session.commit()
            new_user_json = model_to_dict(user)
            new_doctor_json = model_to_dict(doctor)
            # Combine and log
            new_audit = AuditLog(
                user_id=current_user.id,
                action="Edited a Doctor",
                table_name="Doctors",
                old_values=json.dumps({
                    "user": user_json,
                    "doctor": doctor_json
                }),
                new_values=json.dumps({
                    "user": new_user_json,
                    "doctor": new_doctor_json
                }),
                ip_address=request.headers.get('X-Forwarded-For', request.remote_addr),
                user_agent=request.headers.get('User-Agent')
            )
            db.session.add(new_audit)
            db.session.commit()
            flash('Doctor updated successfully!', 'success')
            return redirect(url_for('admin_doctors'))
    except Exception as e:
        db.session.rollback()
        flash(f"Error during update: {str(e)}", "danger")
        return redirect(url_for('admin_doctors'))

@app.route('/admin/doctors/<int:doctor_id>/deactivate')
@role_required(UserRole.ADMIN)
def admin_doctors_deactivate(doctor_id):
    doctor = Doctor.query.get_or_404(doctor_id)
    doctor_json = model_to_dict(doctor)
    doctor.user.is_active = False
    db.session.commit()
    new_audit = AuditLog(
        user_id = current_user.id,
        action = "Deactivated a Doctor",
        table_name = "Doctors",
        new_values = {doctor_json},
        ip_address = request.remote_addr
    )
    new_audit = AuditLog(
        user_id=current_user.id,
        action="Deactivated a Doctor",
        table_name="Doctors",
        new_values=json.dumps({
            "doctor": doctor_json
        }),
        ip_address=request.headers.get('X-Forwarded-For', request.remote_addr),
        user_agent=request.headers.get('User-Agent')
    )
    db.session.add(new_audit)
    db.session.commit()
    flash('Doctor Deactivated successfully!', 'success')
    return redirect(url_for('admin_doctors'))

@app.route('/admin/doctors/<int:doctor_id>/activate')
@role_required(UserRole.ADMIN)
def admin_doctors_activate(doctor_id):
    doctor = Doctor.query.get_or_404(doctor_id)
    doctor_json = model_to_dict(doctor)
    doctor.user.is_active = True
    db.session.commit()
    new_audit = AuditLog(
        user_id=current_user.id,
        action="Activated a Doctor",
        table_name="Doctors",
        new_values=json.dumps({
            "doctor": doctor_json
        }),
        ip_address=request.headers.get('X-Forwarded-For', request.remote_addr),
        user_agent=request.headers.get('User-Agent')
    )
    db.session.add(new_audit)
    db.session.commit()
    flash('Doctor Recovered successfully!', 'success')
    return redirect(url_for('admin_doctors'))

@app.route("/admin/doctors/<int:doctor_id>")
@login_required
@role_required(UserRole.ADMIN)
def admin_doctor_view(doctor_id):
    doctor = Doctor.query.get_or_404(doctor_id)
    return render_template('admin/admin_doctor_view.html', doctor=doctor)

@app.route('/admin/nurses')
@role_required(UserRole.ADMIN)
def admin_nurses():
    nurses = Nurse.query.all()
    departments = Department.query.all()
    wards = Ward.query.all()
    return render_template('admin/admin_nurses.html', nurses=nurses, departments=departments, wards = wards)

@app.route('/admin/nurses/create', methods=['GET', 'POST'])
@role_required(UserRole.ADMIN)
def admin_nurses_create():
    try:
        if request.method == 'POST':
            username = request.form['username']
            email = request.form['email']
            password_hash = request.form['password']
            role = UserRole.NURSE
            first_name = request.form['first_name']
            last_name = request.form['last_name']
            phone = request.form['phone']
            photo = request.files.get('photo')
            is_active = True

            license_number = request.form['license_number']
            department_id = request.form['department_id']
            ward_id = request.form['ward_id']
            shift = request.form['shift']

            photo_data = compress_and_encode_image(photo)

            new_user = User(
                username=username,
                email=email,
                password_hash=password_hash,
                role=role,
                first_name=first_name,
                last_name=last_name,
                phone=phone,
                is_active=is_active,
                photo=photo_data
            )
            db.session.add(new_user)
            db.session.commit()

            new_nurse = Nurse(
                user_id=new_user.id,
                license_number=license_number,
                department_id=department_id,
                ward_id=ward_id,
                shift=shift,
            )
            db.session.add(new_nurse)
            user_json = model_to_dict(new_user)
            nurse_json = model_to_dict(new_nurse)
            new_audit = AuditLog(
                user_id=current_user.id,
                action="Created a Nurse",
                table_name="Nurses",
                new_values=json.dumps({
                    "user": user_json,
                    "nurse": nurse_json
                }),
                ip_address=request.headers.get('X-Forwarded-For', request.remote_addr),
                user_agent=request.headers.get('User-Agent')
            )
            db.session.add(new_audit)
            db.session.commit()
            flash('Nurse created successfully!', 'success')
            return redirect(url_for('admin_nurses'))
    except Exception as e:
        db.session.rollback()
        flash(f"Error during update: {str(e)}", "danger")
        return redirect(url_for('admin_nurses'))

@app.route('/admin/nurses/<int:nurse_id>/edit', methods=['GET', 'POST'])
@role_required(UserRole.ADMIN, UserRole.NURSE)
def admin_nurses_edit(nurse_id):
    try:
        nurse = Nurse.query.get_or_404(nurse_id)
        user = User.query.get_or_404(nurse.user_id)
        user_json = model_to_dict(user)
        nurse_json = model_to_dict(nurse)
        if current_user.role == UserRole.NURSE and current_user.id != nurse.user_id:
            flash("Dont Access Others")
            return redirect(url_for('login'))
        if request.method == 'POST':
            user.username = request.form['username']
            user.email = request.form['email']
            user.first_name = request.form['first_name']
            user.last_name = request.form['last_name']
            user.phone = request.form['phone']

            # Handle photo update if a new photo is provided
            photo = request.files.get('photo')
            if photo:
                photo_data = compress_and_encode_image(photo)
                user.photo = photo_data

            # Update nurse-specific information
            nurse.license_number = request.form['license_number']
            nurse.department_id = request.form['department_id']
            nurse.ward_id = request.form['ward_id']
            nurse.shift = request.form['shift']

            db.session.commit()
            new_user_json = model_to_dict(user)
            new_nurse_json = model_to_dict(nurse)
            new_audit = AuditLog(
                user_id = current_user.id,
                action = "Edited a Nurse",
                table_name = "Nurses",
                old_values = {user_json, nurse_json},
                new_values = {new_user_json, new_nurse_json},
                ip_address = request.remote_addr
            )
            new_audit = AuditLog(
                user_id = current_user.id,
                action = "Edited a Nurse",
                table_name = "Nurses",
                old_values = json.dumps({user_json, nurse_json}),
                new_values = json.dumps({new_user_json, new_nurse_json}),
                ip_address = request.headers.get('X-Forwarded-For', request.remote_addr),
                user_agent = request.headers.get('User-Agent')
            )
            db.session.add(new_audit)
            db.session.commit()
            flash('Nurse updated successfully!', 'success')
            return redirect(url_for('admin_nurses'))

    except Exception as e:
        db.session.rollback()
        flash(f"Error during update: {str(e)}", "danger")
        return redirect(url_for('admin_nurses'))

@app.route('/admin/nurses/<int:nurse_id>/deactivate')
@role_required(UserRole.ADMIN)
def admin_nurses_deactivate(nurse_id):
    nurse = Nurse.query.get_or_404(nurse_id)
    nurse_json = model_to_dict(nurse)
    nurse.user.is_active = False
    db.session.commit()
    new_nurse_json = model_to_dict(nurse)
    new_audit = AuditLog(
        user_id = current_user.id,
        action = "Deactivated a Nurse",
        table_name = "Nurses",
        old_values = json.dumps(nurse_json),
        new_values = json.dumps(new_nurse_json),
        ip_address = request.headers.get('X-Forwarded-For', request.remote_addr),
        user_agent = request.headers.get('User-Agent')
    )
    db.session.add(new_audit)
    db.session.commit()
    flash('Nurse Deactivated successfully!', 'success')
    return redirect(url_for('admin_nurses'))

@app.route('/admin/nurses/<int:nurse_id>/activate')
@role_required(UserRole.ADMIN)
def admin_nurses_activate(nurse_id):
    nurse = Nurse.query.get_or_404(nurse_id)
    nurse_json = model_to_dict(nurse)
    nurse.user.is_active = True
    db.session.commit()
    new_nurse_json = model_to_dict(nurse)
    new_audit = AuditLog(
        user_id = current_user.id,
        action = "Activated a Nurse",
        table_name = "Nurses",
        old_values = json.dumps(nurse_json),
        new_values = json.dumps(new_nurse_json),
        ip_address = request.headers.get('X-Forwarded-For', request.remote_addr),
        user_agent = request.headers.get('User-Agent')
    )
    db.session.add(new_audit)
    db.session.commit()
    flash('Nurse Recovered successfully!', 'success')
    return redirect(url_for('admin_nurses'))

@app.route('/admin/lab_technicians')
@role_required(UserRole.ADMIN)
def admin_lab_technicians():
    lab_technicians = LabTechnician.query.all()
    return render_template('admin/admin_lab_technicians.html', lab_technicians=lab_technicians)

@app.route('/admin/lab_technicians/create', methods=['GET', 'POST'])
@role_required(UserRole.ADMIN)
def admin_lab_technicians_create():
    try:
        if request.method == 'POST':
            username = request.form['username']
            email = request.form['email']
            password_hash = request.form['password']
            role = UserRole.LAB_TECHNICIAN
            first_name = request.form['first_name']
            last_name = request.form['last_name']
            phone = request.form['phone']
            photo = request.files.get('photo')
            is_active = True

            license_number = request.form['license_number']
            specialization = request.form['specialization']
            is_available = True

            photo_data = compress_and_encode_image(photo)

            new_user = User(
                username=username,
                email=email,
                password_hash=password_hash,
                role=role,
                first_name=first_name,
                last_name=last_name,
                phone=phone,
                is_active=is_active,
                photo=photo_data
            )
            db.session.add(new_user)
            db.session.commit()

            new_lab_technician = LabTechnician(
                user_id=new_user.id,
                license_number=license_number,
                specialization=specialization,
                is_available=is_available
            )
            db.session.add(new_lab_technician)
            db.session.commit()
            flash('Lab Technician created successfully!', 'success')
            return redirect(url_for('admin_lab_technicians'))
    except Exception as e:
        db.session.rollback()
        flash(f"Error during creation: {str(e)}", "danger")
        return redirect(url_for('admin_lab_technicians'))

@app.route('/admin/lab_technicians/<int:technician_id>/edit', methods=['GET', 'POST'])
@role_required(UserRole.ADMIN, UserRole.LAB_TECHNICIAN)
def admin_lab_technicians_edit(technician_id):
    try:
        technician = LabTechnician.query.get_or_404(technician_id)
        user = User.query.get_or_404(technician.user_id)
        if current_user.role == UserRole.LAB_TECHNICIAN and current_user.id != technician.user_id:
            flash("Dont Access Others")
            return redirect(url_for('login'))
        if request.method == 'POST':
            user.username = request.form['username']
            user.email = request.form['email']
            user.first_name = request.form['first_name']
            user.last_name = request.form['last_name']
            user.phone = request.form['phone']

            photo = request.files.get('photo')
            if photo:
                photo_data = compress_and_encode_image(photo)
                user.photo = photo_data

            technician.license_number = request.form['license_number']
            technician.specialization = request.form['specialization']

            db.session.commit()
            flash('Lab Technician updated successfully!', 'success')
            return redirect(url_for('admin_lab_technicians'))
    except Exception as e:
        db.session.rollback()
        flash(f"Error during update: {str(e)}", "danger")
        return redirect(url_for('admin_lab_technicians'))

@app.route('/admin/lab_technicians/<int:technician_id>/deactivate')
@role_required(UserRole.ADMIN)
def admin_lab_technicians_deactivate(technician_id):
    technician = LabTechnician.query.get_or_404(technician_id)
    technician.user.is_active = False
    db.session.commit()
    flash('Lab Technician Deactivated successfully!', 'success')
    return redirect(url_for('admin_lab_technicians'))

@app.route('/admin/lab_technicians/<int:technician_id>/activate')
@role_required(UserRole.ADMIN)
def admin_lab_technicians_activate(technician_id):
    technician = LabTechnician.query.get_or_404(technician_id)
    technician.user.is_active = True
    db.session.commit()
    flash('Lab Technician Activated successfully!', 'success')
    return redirect(url_for('admin_lab_technicians'))

@app.route('/admin/pharmacists')
@role_required(UserRole.ADMIN)
def admin_pharmacists():
    pharmacists = Pharmacist.query.all()
    return render_template('admin/admin_pharmacists.html', pharmacists=pharmacists)

@app.route('/admin/pharmacists/create', methods=['GET', 'POST'])
@role_required(UserRole.ADMIN)
def admin_pharmacists_create():
    try:
        if request.method == 'POST':
            username = request.form['username']
            email = request.form['email']
            password_hash = request.form['password']
            role = UserRole.PHARMACIST
            first_name = request.form['first_name']
            last_name = request.form['last_name']
            phone = request.form['phone']
            photo = request.files.get('photo')
            is_active = True

            license_number = request.form['license_number']
            is_available = True

            photo_data = compress_and_encode_image(photo)

            new_user = User(
                username=username,
                email=email,
                password_hash=password_hash,
                role=role,
                first_name=first_name,
                last_name=last_name,
                phone=phone,
                is_active=is_active,
                photo=photo_data
            )
            db.session.add(new_user)
            db.session.commit()

            new_pharmacist = Pharmacist(
                user_id=new_user.id,
                license_number=license_number,
                is_available=is_available
            )
            db.session.add(new_pharmacist)
            db.session.commit()
            flash('Pharmacist created successfully!', 'success')
            return redirect(url_for('admin_pharmacists'))
    except Exception as e:
        db.session.rollback()
        flash(f"Error during creation: {str(e)}", "danger")
        return redirect(url_for('admin_pharmacists'))

@app.route('/admin/pharmacists/<int:pharmacist_id>/edit', methods=['GET', 'POST'])
@role_required(UserRole.ADMIN, UserRole.PHARMACIST)
def admin_pharmacists_edit(pharmacist_id):
    try:
        pharmacist = Pharmacist.query.get_or_404(pharmacist_id)
        user = User.query.get_or_404(pharmacist.user_id)
        if current_user.role == UserRole.PHARMACIST and current_user.id != pharmacist.user_id:
            flash("Dont Access Others")
            return redirect(url_for('login'))
        if request.method == 'POST':
            user.username = request.form['username']
            user.email = request.form['email']
            user.first_name = request.form['first_name']
            user.last_name = request.form['last_name']
            user.phone = request.form['phone']

            photo = request.files.get('photo')
            if photo:
                photo_data = compress_and_encode_image(photo)
                user.photo = photo_data

            pharmacist.license_number = request.form['license_number']

            db.session.commit()
            flash('Pharmacist updated successfully!', 'success')
            return redirect(url_for('admin_pharmacists'))
    except Exception as e:
        db.session.rollback()
        flash(f"Error during update: {str(e)}", "danger")
        return redirect(url_for('admin_pharmacists'))

@app.route('/admin/pharmacists/<int:pharmacist_id>/deactivate')
@role_required(UserRole.ADMIN)
def admin_pharmacists_deactivate(pharmacist_id):
    pharmacist = Pharmacist.query.get_or_404(pharmacist_id)
    pharmacist.user.is_active = False
    db.session.commit()
    flash('Pharmacist Deactivated successfully!', 'success')
    return redirect(url_for('admin_pharmacists'))

@app.route('/admin/pharmacists/<int:pharmacist_id>/activate')
@role_required(UserRole.ADMIN)
def admin_pharmacists_activate(pharmacist_id):
    pharmacist = Pharmacist.query.get_or_404(pharmacist_id)
    pharmacist.user.is_active = True
    db.session.commit()
    flash('Pharmacist Activated successfully!', 'success')
    return redirect(url_for('admin_pharmacists'))

@app.route("/admin/patients")
def admin_patients():
    patients = Patient.query.all()
    return render_template('admin/admin_patients.html', patients = patients)

@app.route('/admin/patients/<int:patient_id>/deactivate')
@role_required(UserRole.ADMIN)
def admin_patients_deactivate(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    patient.user.is_active = False
    db.session.commit()
    flash('Lab patient Deactivated successfully!', 'success')
    return redirect(url_for('admin_patients'))

@app.route('/admin/patients/<int:patient_id>/activate')
@role_required(UserRole.ADMIN)
def admin_patients_activate(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    patient.user.is_active = True
    db.session.commit()
    flash('Lab patient Activated successfully!', 'success')
    return redirect(url_for('admin_patients'))

# Admin Routes for Department Management
@app.route('/admin/departments')
@role_required(UserRole.ADMIN)
def admin_departments():
    doctors = Doctor.query.all()
    departments = Department.query.all()
    return render_template('admin/admin_departments.html', departments=departments, doctors=doctors)

@app.route('/admin/departments/create', methods=['GET', 'POST'])
@role_required(UserRole.ADMIN)
def admin_departments_create():
    if request.method == 'POST':
        name = request.form['departmentName']
        description = request.form['departmentDescription']
        head_doctor_id = request.form['headDoctor']
        is_active = bool(request.form['isActive'])

        new_department = Department(
            name=name,
            description=description,
            head_doctor_id=head_doctor_id,
            is_active=is_active
        )
        db.session.add(new_department)
        db.session.commit()
        flash('Department created successfully!', 'success')
        return redirect(url_for('admin_departments'))


@app.route('/admin/departments/<int:department_id>/edit', methods=['GET', 'POST'])
@role_required(UserRole.ADMIN)
def admin_departments_edit(department_id):
    department = Department.query.get_or_404(department_id)
    if request.method == 'POST':
        department.name = request.form['departmentName']
        department.description = request.form['departmentDescription']
        department.head_doctor_id = request.form['headDoctor']
        department.is_active = bool(int(request.form['isActive']))
        print(bool(request.form['isActive']))
        db.session.commit()
        flash('Department updated successfully!', 'success')
        return redirect(url_for('admin_departments'))

@app.route('/admin/departments/<int:department_id>/delete', methods=['POST'])
@role_required(UserRole.ADMIN)
def admin_departments_delete(department_id):
    department = Department.query.get_or_404(department_id)
    db.session.delete(department)
    db.session.commit()
    flash('Department deleted successfully!', 'success')
    return redirect(url_for('admin_departments'))

# Admin Routes for Ward Management
@app.route('/admin/wards')
@login_required
@role_required(UserRole.ADMIN)
def admin_wards():
    wards = Ward.query.all()
    departments = Department.query.all()
    total_beds = sum(ward.capacity for ward in wards)
    occupied_beds = sum(ward.current_occupancy for ward in wards)
    return render_template('admin/admin_wards.html',
                         wards=wards,
                         departments=departments,
                         total_beds=total_beds,
                         occupied_beds=occupied_beds)

@app.route('/admin/wards/create', methods=['GET', 'POST'])
@login_required
@role_required(UserRole.ADMIN)
def admin_wards_create():
    name = request.form.get('wardName')
    department_id = request.form.get('department')
    capacity = int(request.form.get('capacity'))
    is_active = bool(int(request.form['isActive']))

    new_ward = Ward(
        name=name,
        department_id=department_id,
        capacity=capacity,
        is_active=is_active,
        current_occupancy=0
    )

    db.session.add(new_ward)
    db.session.commit()
    flash('Ward created successfully', 'success')
    return redirect(url_for('admin_wards'))

@app.route('/admin/wards/<int:ward_id>/edit', methods=['GET', 'POST'])
@role_required(UserRole.ADMIN)
def admin_wards_edit(ward_id):
    ward = Ward.query.get_or_404(ward_id)
    if request.method == 'POST':
        ward.name = request.form['name']
        ward.department_id = request.form['department_id']
        ward.capacity = request.form['capacity']
        ward.current_occupancy = request.form['current_occupancy']
        ward.is_active = 'isActive' in request.form

        db.session.commit()
        flash('Ward updated successfully!', 'success')
        return redirect(url_for('admin_wards'))

    return render_template('admin/ward_edit.html', ward=ward)

@app.route('/admin/wards/<int:ward_id>/delete', methods=['POST'])
@role_required(UserRole.ADMIN)
def admin_wards_delete(ward_id):
    ward = Ward.query.get_or_404(ward_id)
    db.session.delete(ward)
    db.session.commit()
    flash('Ward deleted successfully!', 'success')
    return redirect(url_for('admin_wards'))

@app.route('/doctor')
@login_required
@role_required(UserRole.DOCTOR)
def doctor():
    doctor = Doctor.query.filter_by(user_id = current_user.id).first()
    return render_template('doctor/doctor_home.html',doctor = doctor)

@app.route('/doctor/appointments')
@login_required
@role_required(UserRole.DOCTOR)
def doctor_appointments():
    doctor = Doctor.query.filter_by(user_id = current_user.id).first()
    appointments = Appointment.query.filter_by(doctor_id = doctor.id). first()
    return render_template('doctor/doctor_appointments.html',doctor = doctor, appointments = appointments)

@app.route('/doctor/prescriptions')
@login_required
@role_required(UserRole.DOCTOR)
def doctor_prescriptions():
    doctor = Doctor.query.filter_by(user_id = current_user.id).first()
    appointments = Appointment.query.filter_by(doctor_id = doctor.id). first()
    prescriptions = Prescription.query.filter_by(doctor_id = doctor.id). first()
    return render_template('doctor/doctor_prescriptions.html',doctor = doctor, appointments = appointments, prescriptions = prescriptions)

@app.route('/doctor/prescriptions/create', methods = ['POST'])
@login_required
@role_required(UserRole.DOCTOR)
def doctor_prescriptions_create():
    if request.method == 'POST':
        doctor = Doctor.query.filter_by(user_id = current_user.id).first()
        appointments = Appointment.query.filter_by(doctor_id = doctor.id). first()
        prescriptions = Prescription.query.filter_by(doctor_id = doctor.id). first()
        return render_template('doctor/doctor_prescriptions.html',doctor = doctor, appointments = appointments, prescriptions = prescriptions)

@app.route('/patient/<int:user_id>')
@login_required
@role_required(UserRole.PATIENT)
def patient(user_id):
    patient = Patient.query.filter_by(user_id = user_id).first()
    return render_template('patient/patient_home.html',patient = patient)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('home'))

@app.route('/admin/audit-logs')
@login_required
def view_audit_logs():
    logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).all()
    return render_template('admin/admin_audit_logs.html', audit_logs=logs)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        admin_exists = User.query.filter_by(role=UserRole.ADMIN).first()

        if not admin_exists:
            admin = User(
                username='admin',
                email='admin@example.com',
                password_hash="password",  # Change this to a secure password
                role=UserRole.ADMIN,
                first_name='Admin',
                last_name='User',
                phone='1234567890',
                is_active=True
            )

            # Add the admin user to the database
            db.session.add(admin)
            db.session.commit()
            print("Admin user created successfully.")
        else:
            print("Admin user already exists.")
    app.run(debug=True)