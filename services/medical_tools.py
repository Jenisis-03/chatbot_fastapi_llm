from typing import Dict, Any

class MedicalTools:
    _available_doctors = {"smith": ["2025-06-10", "2025-06-11"], "jones": ["2025-06-12"]}
    _available_medicines = ["aspirin", "paracetamol"]
    _available_patients = ["123", "456", "789"]

    def get_doctor_appointment(self, doctor_name: str, date: str) -> str:
        if not doctor_name or not date:
            return "Please provide both doctor name and date for appointment booking."
        doctor_name = doctor_name.lower()
        if doctor_name not in self._available_doctors:
            return f"Error: Dr. {doctor_name.capitalize()} is not available in the system."
        if date not in self._available_doctors[doctor_name]:
            return f"Error: No availability for Dr. {doctor_name.capitalize()} on {date}."
        return f"Appointment booked with Dr. {doctor_name.capitalize()} on {date}."

    def get_medicine_info(self, medicine_name: str) -> str:
        if not medicine_name:
            return "Please provide medicine name for information."
        medicine_name = medicine_name.lower()
        if medicine_name not in self._available_medicines:
            return f"Error: Medicine {medicine_name.capitalize()} is not available in the system."
        return f"Details about {medicine_name.capitalize()}: Generic drug used for pain relief."

    def get_lab_report(self, patient_id: str) -> str:
        if not patient_id:
            return "Please provide patient ID for lab report."
        if patient_id not in self._available_patients:
            return f"Error: Patient ID {patient_id} not found in the system."
        return f"Lab report for patient ID {patient_id}: All values normal"

    def get_patient_appointments(self, patient_id: str) -> str:
        if not patient_id:
            return "Please provide patient ID to check appointments."
        if patient_id not in self._available_patients:
            return f"Error: Patient ID {patient_id} not found in the system."
        return f"Appointments for patient ID {patient_id}: Next appointment on 2025-06-10"

    def get_patient_details(self, patient_id: str) -> str:
        if not patient_id:
            return "Please provide patient ID for patient details."
        if patient_id not in self._available_patients:
            return f"Error: Patient ID {patient_id} not found in the system."
        return f"Patient ID {patient_id} details: John Doe, Age 40, Contact: 123-456-7890"