# Submission Write-Up: AarogyaBharat.AI

## Problem Statement
Access to initial medical triage, specialist discovery, and appointment booking in India often faces high friction. Patients lack clear guidance on whether their symptoms require emergency care, routine checkups, or a specific specialist.

## Solution Architecture
The solution uses a Multi-Agent architecture built on Google's Agent Development Kit (ADK) and Model Context Protocol (MCP). A central coordinator routes user requests to specialized agents for symptom analysis, doctor recommendations, scheduling, and health records management.

## Concepts Used
- **ADK Workflow**: A structured graph in `app/agent.py` defining the routing of patient requests through a central `coordinator_agent` and sub-agents.
- **LlmAgent**: Agents like `symptom_agent` and `appointment_agent` focus on narrow tasks to improve reliability.
- **MCP Server**: Located in `app/mcp_server.py`, exposing a local SQLite database of doctors, patients, and appointments through secure tools.
- **Security Checkpoint**: Implemented as a FunctionNode in `app/agent.py` to scrub PII (Aadhar, Phone, Email) and block prompt injection.
- **Agents CLI**: Project scaffolded using `agents-cli`.

## Security Design
The healthcare domain handles sensitive patient data.
- **PII Scrubbing**: Regex patterns automatically redact Aadhar numbers, Phone numbers, and Emails before the LLM processes them.
- **Prompt Injection**: Any attempt to override medical advice or bypass instructions is blocked by the security node.
- **Audit Logging**: Every security evaluation leaves a structured JSON trace in the console for compliance.

## MCP Server Design
The FastMCP server (`app/mcp_server.py`) provides the following tools:
1. `get_doctors_by_specialty`: Returns specialists based on triage outputs.
2. `get_patient_medical_history`: Fetches past diagnoses and records.
3. `book_appointment_slot`: Books consultations directly into the DB.
4. `get_medication_schedule`: Retrieves dosage guidelines and reminders.
5. `get_vaccination_schedule`: Retrieves immunization tracking.

## HITL Flow
The workflow currently allows seamless interaction but can easily integrate human-in-the-loop (HITL) for prescription refills and critical diagnosis confirmation using the RequestInput features.

## Demo Walkthrough
1. **Symptom Triage**: When a user complains of blurry vision, the system triages it and dynamically pulls ophthalmologists from the database.
2. **Booking**: The user provides their Health ID, and the appointment agent successfully locks in a time slot with the recommended doctor.
3. **Adherence**: The user queries their medication, and the agent lays out a clear, structured timetable based on their records.

## Impact / Value Statement
AarogyaBharat.AI streamlines the patient journey from the first symptom to the doctor's cabin, reducing friction and anxiety while maintaining data privacy.
