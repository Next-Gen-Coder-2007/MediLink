# Hospital Management System

A comprehensive web-based system designed to manage various aspects of hospital operations, including user management, patient records, appointments, and more. This system features distinct interfaces and functionalities for each user role, with administrators having separate management pages for each type of user.

## Table of Contents

- [Features](#features)
- [Models](#models)
  - [Department Model](#department-model)
  - [Ward Model](#ward-model)
- [User Roles and Pages](#user-roles-and-pages)
  - [Admin](#admin)
  - [Doctor](#doctor)
  - [Nurse](#nurse)
  - [Lab Technician](#lab-technician)
  - [Pharmacist](#pharmacist)
  - [Patient](#patient)
- [Access Control](#access-control)
- [Installation](#installation)
- [Usage](#usage)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)

## Features

- **Role-Based Access Control:** Secure and tailored access for different user roles.
- **Separate Management Pages:** Admin has distinct pages for managing doctors, nurses, lab technicians, pharmacists, and patients.
- **Comprehensive User Interfaces:** Tailored dashboards and functionalities for each role.
- **Appointment and Patient Management:** Schedule, manage, and track appointments and patient records.
- **Prescription and Inventory Management:** Create, manage prescriptions, and track medicine inventory.
- **Lab Test Management:** Record and update lab test results and track samples.
- **Billing and Payments:** Manage billing information and process payments.

## Models

### Department Model

The `Department` model represents different departments within the hospital, such as Cardiology, Neurology, Pediatrics, etc.

#### Attributes

- **id:** A unique identifier for each department.
- **name:** The name of the department.
- **description:** A brief description of the department's functions or specialties.
- **head_doctor_id:** A foreign key referencing the `Doctor` model, indicating the doctor who heads the department.
- **is_active:** A boolean flag indicating whether the department is currently active.
- **created_at:** The timestamp when the department record was created.

#### Relationships

- **head_doctor:** A relationship to the `Doctor` model, representing the doctor who is the head of the department.
- **doctors:** A relationship to the `Doctor` model, representing all doctors associated with the department.
- **nurses:** A relationship to the `Nurse` model, representing all nurses associated with the department.
- **wards:** A relationship to the `Ward` model, representing all wards within the department.

### Ward Model

The `Ward` model represents different wards within a department, such as ICU, General Ward, Maternity Ward, etc.

#### Attributes

- **id:** A unique identifier for each ward.
- **name:** The name of the ward.
- **department_id:** A foreign key referencing the `Department` model, indicating the department to which the ward belongs.
- **capacity:** The maximum number of patients the ward can accommodate.
- **current_occupancy:** The current number of patients in the ward.
- **is_active:** A boolean flag indicating whether the ward is currently active.

#### Relationships

- **department:** A relationship to the `Department` model, representing the department to which the ward belongs.
- **nurses:** A relationship to the `Nurse` model, representing all nurses assigned to the ward.
- **patient_admissions:** A relationship to the `PatientAdmission` model, representing all patient admissions to the ward.

## User Roles and Pages

### Admin

- **Admin Dashboard:** Overview of system statistics and quick access to management tools.
- **Manage Doctors:** Add, edit, deactivate doctors, and view the list of doctors.
- **Manage Nurses:** Add, edit, deactivate nurses, and view the list of nurses.
- **Manage Lab Technicians:** Add, edit, deactivate lab technicians, and view the list of lab technicians.
- **Manage Pharmacists:** Add, edit, deactivate pharmacists, and view the list of pharmacists.
- **Manage Patients:** View and deactivate patient accounts, and view the list of patients.
- **System Configuration:** Configure system settings, email settings, and security settings.
- **Reports and Analytics:** Generate and view reports on system usage and hospital operations.

### Doctor

- **Doctor Dashboard:** Overview of appointments, patients, and tasks.
- **Appointment Management:** Manage and update appointment statuses.
- **Patient Records:** Access and update patient medical records and history.
- **Prescription Management:** Create and manage patient prescriptions.

### Nurse

- **Nurse Dashboard:** Overview of assigned patients and tasks.
- **Vital Records:** Record and update patient vital signs.
- **Patient Admission:** Manage patient admissions and discharges.

### Lab Technician

- **Lab Technician Dashboard:** Overview of assigned lab tests and tasks.
- **Lab Test Management:** Record and update lab test results and manage test statuses.

### Pharmacist

- **Pharmacist Dashboard:** Overview of prescriptions and inventory tasks.
- **Prescription Fulfillment:** Manage and fulfill patient prescriptions.
- **Medicine Inventory:** Manage medicine stock, track batch numbers, and expiry dates.

### Patient

- **Patient Dashboard:** Overview of appointments, prescriptions, and medical records.
- **Appointment Scheduling:** Schedule and manage appointments with doctors.
- **Medical Records:** View personal medical records and history.
- **Billing and Payments:** View and manage billing information and make payments.

## Access Control

- **Authentication:** Secure login and registration processes for all user roles.
- **Authorization:** Role-based access control to ensure users can only access relevant pages and functionalities.
- **Middleware:** Checks user permissions and redirects unauthorized access attempts.

## Installation

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/yourusername/hospital-management-system.git
   cd hospital-management-system
