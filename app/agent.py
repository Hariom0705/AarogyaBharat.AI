# ruff: noqa
import sys
import asyncio

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

import datetime
import json
import re
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from google.adk.agents import LlmAgent
from google.adk.apps import App
from google.adk.events.event import Event
from google.adk.agents.context import Context
from google.adk.workflow import Workflow, START

from app.config import config


# ==========================================
# 1. Pydantic Schemas for Agents
# ==========================================

class CoordinatorOutput(BaseModel):
    route: str = Field(description="Target specialized agent: 'symptom_assessment', 'doctor_recommendation', 'appointment_management', 'medication_management', 'vaccination_intelligence', 'medical_records', 'health_timeline', 'preventive_healthcare', 'health_education', 'emergency_response', 'health_analytics', or 'general'")
    health_id: str = Field(description="The extracted Health ID if present (e.g., HB-1234), otherwise empty string")
    analysis: str = Field(description="Short reason for routing decision")


class SymptomAssessmentOutput(BaseModel):
    specialty: str = Field(description="Recommended medical specialty")
    severity: str = Field(description="Severity level: emergency, urgent, or routine")
    possible_conditions: List[str] = Field(description="Educational list of possible medical conditions")
    follow_up_questions: List[str] = Field(description="Follow-up clarification questions for the doctor")
    summary: str = Field(description="Empathic summary of symptom assessment")


class DoctorRecommendationOutput(BaseModel):
    specialty: str = Field(description="Specialty queried")
    recommendations: List[Dict[str, Any]] = Field(description="List of doctors with name, hospital, and availability")
    summary: str = Field(description="Summary explanation of choices")


class AppointmentManagementOutput(BaseModel):
    status: str = Field(description="Status: booked, rescheduled, cancelled, or pending")
    appointment_id: str = Field(description="Unique ID of appointment")
    details: str = Field(description="Date, time, doctor, and status details")


class MedicationManagementOutput(BaseModel):
    medications: List[Dict[str, Any]] = Field(description="List of meds with dosage and timing")
    reminders: List[str] = Field(description="Adherence reminders")
    summary: str = Field(description="Brief medication guidelines")


class VaccinationIntelligenceOutput(BaseModel):
    vaccines: List[Dict[str, Any]] = Field(description="Vaccination records and due dates")
    recommendations: List[str] = Field(description="Upcoming vaccines suggested")
    summary: str = Field(description="Importance and benefits summary")


class MedicalRecordsOutput(BaseModel):
    records: List[Dict[str, Any]] = Field(description="Search results of patient reports")
    summary: str = Field(description="Overview of relevant documents found")


class HealthTimelineOutput(BaseModel):
    timeline_events: List[Dict[str, Any]] = Field(description="Chronological events")
    mermaid_chart: str = Field(description="Valid Mermaid diagram representing timeline")
    summary: str = Field(description="Overview of recovery milestones and events")


class PreventiveHealthcareOutput(BaseModel):
    recommendations: List[str] = Field(description="Checkups and screenings")
    summary: str = Field(description="Lifestyle adjustment summary")


class HealthEducationOutput(BaseModel):
    explanation: str = Field(description="Scientific medical explanation")
    simple_summary: str = Field(description="Extremely simple, clear analogy/summary")


class EmergencyResponseOutput(BaseModel):
    is_emergency: bool = Field(description="Is this a true emergency?")
    instructions: str = Field(description="First aid and next steps")
    facilities: List[str] = Field(description="List of nearest critical care facilities")


class HealthAnalyticsOutput(BaseModel):
    metrics: Dict[str, Any] = Field(description="Hospital dashboard metrics")
    insights: List[str] = Field(description="Operational improvement points")


# ==========================================
# 2. Specialized LlmAgents (Sub-agents)
# ==========================================

import os
import sys
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters

mcp_server_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mcp_server.py")

mcp_toolset = McpToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command=sys.executable,
            args=[mcp_server_path],
        ),
    ),
)

coordinator_agent = LlmAgent(
    name="coordinator_agent",
    model=config.model,
    instruction=(
        "You are the central Coordinator Agent for AarogyaBharat.AI. "
        "Your task is to analyze the user request and select the correct specialized agent route. "
        "Route choices:\n"
        "- 'symptom_assessment': Symptom complaints, feeling unwell, diagnostic questions.\n"
        "- 'doctor_recommendation': Finding a doctor, matching specialist, availability query.\n"
        "- 'appointment_management': Booking, rescheduling, or canceling appointments.\n"
        "- 'medication_management': Prescriptions, timing, dosage, reminders.\n"
        "- 'vaccination_intelligence': Vaccine record, schedules, guidelines.\n"
        "- 'medical_records': Lab reports, allergies, medical history.\n"
        "- 'health_timeline': Visual timeline, historical summary of health events.\n"
        "- 'preventive_healthcare': General screening recommendations, checkup suggestions.\n"
        "- 'health_education': Explaining medical jargon or disease topics.\n"
        "- 'emergency_response': Chest pain, stroke signs, difficulty breathing.\n"
        "- 'health_analytics': Dashboard, statistics, adherence numbers.\n"
        "- 'general': Small talk, greetings, general non-medical support.\n"
        "Always extract the Health ID (starts with HB-) if present."
    ),
    output_schema=CoordinatorOutput,
)

symptom_agent = LlmAgent(
    name="symptom_agent",
    model=config.model,
    instruction="Provide a symptom triage assessment based on the user description. Suggest the appropriate specialty without providing a definitive diagnosis.",
    output_schema=SymptomAssessmentOutput,
    output_key="symptom_report",
)

doctor_agent = LlmAgent(
    name="doctor_agent",
    model=config.model,
    instruction="Recommend doctors by querying the get_doctors_by_specialty tool. The specialty can be found in the input (which may be a symptom triage report containing 'specialty' or a search query string). Inform about doctors' names, hospitals, and availability.",
    tools=[mcp_toolset],
    output_schema=DoctorRecommendationOutput,
    output_key="doctor_recommendations",
)

appointment_agent = LlmAgent(
    name="appointment_agent",
    model=config.model,
    instruction=(
        "You are the Appointment Management Agent.\n"
        "Your task is to manage medical appointments: booking new slots, rescheduling, or canceling appointments by calling the book_appointment_slot tool.\n"
        "If key details (such as the doctor's name, the date, or the time slot) are missing from the user request, "
        "you MUST set status='pending', appointment_id='N/A', and in the 'details' field, ask the user to specify the missing information.\n"
        "If the booking fails (e.g., because a doctor is not found in the database), set status='failed', appointment_id='N/A', and in the 'details' field, "
        "explain that the doctor was not found and recommend choosing one of the available doctors.\n"
        "You must ALWAYS return a JSON response adhering to the AppointmentManagementOutput schema. Never output plain text conversation outside the schema."
    ),
    tools=[mcp_toolset],
    output_schema=AppointmentManagementOutput,
)

medication_agent = LlmAgent(
    name="medication_agent",
    model=config.model,
    instruction="Store prescription lists and generate medication timetables/schedules by calling get_medication_schedule.",
    tools=[mcp_toolset],
    output_schema=MedicationManagementOutput,
)

vaccination_agent = LlmAgent(
    name="vaccination_agent",
    model=config.model,
    instruction="Provide vaccination guidance. Suggest timeline vaccines based on patient age by calling get_vaccination_schedule.",
    tools=[mcp_toolset],
    output_schema=VaccinationIntelligenceOutput,
)

records_agent = LlmAgent(
    name="records_agent",
    model=config.model,
    instruction="Handle digital patient record storage and query indexing. Ensure everything is searchable by calling get_patient_medical_history.",
    tools=[mcp_toolset],
    output_schema=MedicalRecordsOutput,
)

timeline_agent = LlmAgent(
    name="timeline_agent",
    model=config.model,
    instruction=(
        "Generate a visual health history timeline for the patient by calling get_patient_medical_history. "
        "Your output must include a valid Mermaid flowchart representing chronological health events (e.g., graph TD ...)"
    ),
    tools=[mcp_toolset],
    output_schema=HealthTimelineOutput,
)

preventive_agent = LlmAgent(
    name="preventive_agent",
    model=config.model,
    instruction="Provide checkup and screening schedules based on patient profile (age, gender, history).",
    output_schema=PreventiveHealthcareOutput,
)

education_agent = LlmAgent(
    name="education_agent",
    model=config.model,
    instruction="Translate complex medical terms or test reports into plain, easy-to-understand Patient Education guidelines.",
    output_schema=HealthEducationOutput,
)

emergency_agent = LlmAgent(
    name="emergency_agent",
    model=config.model,
    instruction="CRITICAL triage. Immediately provide emergency guidance and list emergency resources/nearest hospitals.",
    output_schema=EmergencyResponseOutput,
)

analytics_agent = LlmAgent(
    name="analytics_agent",
    model=config.model,
    instruction="Compute metrics for hospital dashboards, such as appointment rates, compliance, and cancellations.",
    output_schema=HealthAnalyticsOutput,
)

general_agent = LlmAgent(
    name="general_agent",
    model=config.model,
    instruction="Warmly handle greetings, general information, and platform support queries.",
)


# ==========================================
# 3. Workflow Function Nodes
# ==========================================

def get_text_from_content(content: Any) -> str:
    if not content:
        return ""
    if isinstance(content, str):
        return content
    if hasattr(content, "parts"):
        parts_text = []
        for p in content.parts:
            if hasattr(p, "text") and p.text:
                parts_text.append(p.text)
        return " ".join(parts_text)
    return str(content)


def security_checkpoint(ctx: Context, node_input: Any) -> Event:
    text = get_text_from_content(node_input)
    
    # 1. PII Scrubbing (Aadhar 12-digit, 10-digit Mobile, email addresses)
    aadhar_pattern = r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'
    phone_pattern = r'\b(?:\+?91[\s-]?)?[6-9]\d{9}\b'
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    
    scrubbed_text = text
    if config.pii_redaction_enabled:
        scrubbed_text = re.sub(aadhar_pattern, "[REDACTED-AADHAR]", scrubbed_text)
        scrubbed_text = re.sub(phone_pattern, "[REDACTED-PHONE]", scrubbed_text)
        scrubbed_text = re.sub(email_pattern, "[REDACTED-EMAIL]", scrubbed_text)
    
    ctx.state["user_query"] = scrubbed_text
    
    # 2. Prompt Injection Check
    injection_keywords = ["ignore instructions", "system prompt", "bypass", "override", "jailbreak", "hack"]
    detected_injection = False
    if config.injection_detection_enabled:
        for kw in injection_keywords:
            if kw in text.lower():
                detected_injection = True
                break
                
    # 3. gibberish/empty input check
    if len(text.strip()) < 2:
        return Event(output="Gibberish/empty input", route="gibberish")
        
    audit_log = {
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "actor": ctx.session.id,
        "action": "security_checkpoint",
        "severity": "CRITICAL" if detected_injection else "INFO",
        "details": f"Injection: {detected_injection}. Redacted: {scrubbed_text != text}."
    }
    print(f"[AUDIT] {json.dumps(audit_log)}")
    
    if detected_injection:
        return Event(output="Prompt injection blocked.", route="SECURITY_EVENT")
        
    return Event(output=scrubbed_text, route="pass")


def security_violation_handler(ctx: Context, node_input: str) -> Event:
    return Event(output="⚠️ Security Check failed. The request was flagged as a security policy violation.")


def gibberish_handler(ctx: Context, node_input: str) -> Event:
    return Event(output="Please type a valid question or medical request. The query entered was too short.")


def route_selector(ctx: Context, node_input: dict) -> Event:
    # node_input is the dict representation of CoordinatorOutput
    route = node_input.get("route", "general")
    health_id = node_input.get("health_id", "")
    analysis = node_input.get("analysis", "")
    
    if health_id:
        ctx.state["health_id"] = health_id
    ctx.state["routing_analysis"] = analysis
    
    return Event(output=ctx.state.get("user_query", ""), route=route)


def response_formatter(ctx: Context, node_input: Any) -> Event:
    from google.genai import types

    formatted_text = ""
    
    # Check if we have symptom report saved in state (which means we flowed from symptom -> doctor)
    symptom_report = ctx.state.get("symptom_report")
    doctor_recs = ctx.state.get("doctor_recommendations")
    
    if symptom_report:
        formatted_text = (
            f"### 🩺 Symptom Assessment Report\n\n"
            f"**Recommended Specialty:** {symptom_report.get('specialty')}\n"
            f"**Triage Severity:** {symptom_report.get('severity', 'routine').upper()}\n\n"
            f"**Possible Conditions (Educational only):**\n"
        )
        for cond in symptom_report.get("possible_conditions", []):
            formatted_text += f"- {cond}\n"
        if symptom_report.get("follow_up_questions"):
            formatted_text += f"\n**Follow-up Questions for Doctor:**\n"
            for q in symptom_report.get("follow_up_questions", []):
                formatted_text += f"- {q}\n"
        formatted_text += f"\n**Summary:** {symptom_report.get('summary')}\n\n"
        
        # Clear it so it doesn't leak to subsequent messages
        ctx.state["symptom_report"] = None
        
        if doctor_recs:
            formatted_text += f"### 👨‍⚕️ Available Specialist Recommendations\n\n"
            for doc in doctor_recs.get("recommendations", []):
                formatted_text += f"- **Dr. {doc.get('name')}** - {doc.get('hospital')} (Availability: {doc.get('availability')})\n"
            formatted_text += f"\n**Notes:** {doctor_recs.get('summary')}\n"
            ctx.state["doctor_recommendations"] = None
            
        return Event(
            content=types.Content(
                role="model",
                parts=[types.Part.from_text(text=formatted_text)]
            ),
            output=node_input
        )

    # Standard single-agent outputs format
    if isinstance(node_input, dict):
        if "specialty" in node_input and "possible_conditions" in node_input:
            formatted_text = (
                f"### 🩺 Symptom Assessment Report\n\n"
                f"**Recommended Specialty:** {node_input.get('specialty')}\n"
                f"**Triage Severity:** {node_input.get('severity', 'routine').upper()}\n\n"
                f"**Possible Conditions (Educational only):**\n"
            )
            for cond in node_input.get("possible_conditions", []):
                formatted_text += f"- {cond}\n"
            if node_input.get("follow_up_questions"):
                formatted_text += f"\n**Follow-up Questions for Doctor:**\n"
                for q in node_input.get("follow_up_questions", []):
                    formatted_text += f"- {q}\n"
            formatted_text += f"\n**Summary:** {node_input.get('summary')}\n"
            
        elif "recommendations" in node_input and "specialty" in node_input:
            formatted_text = f"### 👨‍⚕️ Smart Doctor Recommendations ({node_input.get('specialty')})\n\n"
            for doc in node_input.get("recommendations", []):
                formatted_text += f"- **Dr. {doc.get('name')}** - {doc.get('hospital')} ({doc.get('availability')})\n"
            formatted_text += f"\n**Summary:** {node_input.get('summary')}\n"
            
        elif "appointment_id" in node_input:
            formatted_text = (
                f"### 📅 Appointment Status\n\n"
                f"**Status:** {node_input.get('status', 'unknown').upper()}\n"
                f"**Appointment ID:** {node_input.get('appointment_id')}\n"
                f"**Details:** {node_input.get('details')}\n"
            )
            
        elif "medications" in node_input:
            formatted_text = f"### 💊 Medication Reminder & Schedule\n\n"
            for med in node_input.get("medications", []):
                formatted_text += f"- **{med.get('name')}** ({med.get('dosage')}) - *{med.get('timing')}*\n"
            if node_input.get("reminders"):
                formatted_text += f"\n**Reminders:**\n"
                for r in node_input.get("reminders", []):
                    formatted_text += f"- {r}\n"
            formatted_text += f"\n{node_input.get('summary', '')}\n"
            
        elif "vaccines" in node_input:
            formatted_text = f"### 💉 Vaccination Schedule\n\n"
            for vac in node_input.get("vaccines", []):
                formatted_text += f"- **{vac.get('name')}** ({vac.get('age')}) - *{vac.get('status')}*\n"
            if node_input.get("recommendations"):
                formatted_text += f"\n**Upcoming recommendations:**\n"
                for rec in node_input.get("recommendations", []):
                    formatted_text += f"- {rec}\n"
            formatted_text += f"\n{node_input.get('summary', '')}\n"
            
        elif "records" in node_input:
            formatted_text = f"### 📂 Digital Medical Records\n\n"
            for rec in node_input.get("records", []):
                formatted_text += f"- **{rec.get('date')}**: {rec.get('type')} ({rec.get('diagnosis')})\n"
            formatted_text += f"\n{node_input.get('summary', '')}\n"
            
        elif "mermaid_chart" in node_input:
            formatted_text = (
                f"### ⏳ Lifelong Health Timeline\n\n"
                f"```mermaid\n{node_input.get('mermaid_chart')}\n```\n\n"
                f"**Timeline Summary:**\n{node_input.get('summary')}\n"
            )
            
        elif "recommendations" in node_input and "summary" in node_input:
            formatted_text = f"### 🛡️ Preventive Health Recommendations\n\n"
            for rec in node_input.get("recommendations", []):
                formatted_text += f"- {rec}\n"
            formatted_text += f"\n{node_input.get('summary')}\n"
            
        elif "simple_summary" in node_input:
            formatted_text = (
                f"### 📖 Patient Education Library\n\n"
                f"{node_input.get('explanation')}\n\n"
                f"**In simple terms:** {node_input.get('simple_summary')}\n"
            )
            
        elif "is_emergency" in node_input:
            if node_input.get("is_emergency"):
                formatted_text = f"### 🚨 EMERGENCY WARNING DETECTED 🚨\n\n"
            else:
                formatted_text = f"### ℹ️ Emergency Response Check\n\n"
            formatted_text += f"{node_input.get('instructions')}\n\n"
            if node_input.get("facilities"):
                formatted_text += f"**Nearby Facilities:**\n"
                for fac in node_input.get("facilities", []):
                    formatted_text += f"- {fac}\n"
                    
        elif "metrics" in node_input:
            formatted_text = f"### 📊 Hospital Operations Dashboard\n\n"
            for k, v in node_input.get("metrics", {}).items():
                formatted_text += f"- **{k.replace('_', ' ').title()}:** {v}\n"
            if node_input.get("insights"):
                formatted_text += f"\n**Operational Insights:**\n"
                for ins in node_input.get("insights", []):
                    formatted_text += f"- {ins}\n"
        else:
            formatted_text = f"### Response\n\n"
            for k, v in node_input.items():
                formatted_text += f"- **{k}:** {v}\n"
    else:
        formatted_text = str(node_input)
        
    return Event(
        content=types.Content(
            role="model",
            parts=[types.Part.from_text(text=formatted_text)]
        ),
        output=node_input
    )


# ==========================================
# 4. ADK Workflow Graph
# ==========================================

from google.adk.workflow import FunctionNode, Edge

security_checkpoint_node = FunctionNode(func=security_checkpoint, name="security_checkpoint")
security_violation_handler_node = FunctionNode(func=security_violation_handler, name="security_violation_handler")
gibberish_handler_node = FunctionNode(func=gibberish_handler, name="gibberish_handler")
route_selector_node = FunctionNode(func=route_selector, name="route_selector")
response_formatter_node = FunctionNode(func=response_formatter, name="response_formatter")

root_agent = Workflow(
    name="aarogya_coordinator",
    description="Intelligent Coordinator for AarogyaBharat.AI multi-agent healthcare platform",
    edges=[
        # Entry check
        Edge(from_node=START, to_node=security_checkpoint_node),
        
        # Security routing
        Edge(from_node=security_checkpoint_node, to_node=security_violation_handler_node, route="SECURITY_EVENT"),
        Edge(from_node=security_checkpoint_node, to_node=gibberish_handler_node, route="gibberish"),
        Edge(from_node=security_checkpoint_node, to_node=coordinator_agent, route="pass"),
        
        # Coordination & Specialized sub-agent routing
        Edge(from_node=coordinator_agent, to_node=route_selector_node),
        Edge(from_node=route_selector_node, to_node=symptom_agent, route="symptom_assessment"),
        Edge(from_node=symptom_agent, to_node=doctor_agent), # Flow symptom triage results directly into doctor recommender
        Edge(from_node=route_selector_node, to_node=doctor_agent, route="doctor_recommendation"),
        Edge(from_node=route_selector_node, to_node=appointment_agent, route="appointment_management"),
        Edge(from_node=route_selector_node, to_node=medication_agent, route="medication_management"),
        Edge(from_node=route_selector_node, to_node=vaccination_agent, route="vaccination_intelligence"),
        Edge(from_node=route_selector_node, to_node=records_agent, route="medical_records"),
        Edge(from_node=route_selector_node, to_node=timeline_agent, route="health_timeline"),
        Edge(from_node=route_selector_node, to_node=preventive_agent, route="preventive_healthcare"),
        Edge(from_node=route_selector_node, to_node=education_agent, route="health_education"),
        Edge(from_node=route_selector_node, to_node=emergency_agent, route="emergency_response"),
        Edge(from_node=route_selector_node, to_node=analytics_agent, route="health_analytics"),
        Edge(from_node=route_selector_node, to_node=general_agent, route="general"),
        
        # Converge back to formatter node
        Edge(from_node=security_violation_handler_node, to_node=response_formatter_node),
        Edge(from_node=gibberish_handler_node, to_node=response_formatter_node),
        # Note: symptom_agent now flows through doctor_agent to response_formatter_node
        Edge(from_node=doctor_agent, to_node=response_formatter_node),
        Edge(from_node=appointment_agent, to_node=response_formatter_node),
        Edge(from_node=medication_agent, to_node=response_formatter_node),
        Edge(from_node=vaccination_agent, to_node=response_formatter_node),
        Edge(from_node=records_agent, to_node=response_formatter_node),
        Edge(from_node=timeline_agent, to_node=response_formatter_node),
        Edge(from_node=preventive_agent, to_node=response_formatter_node),
        Edge(from_node=education_agent, to_node=response_formatter_node),
        Edge(from_node=emergency_agent, to_node=response_formatter_node),
        Edge(from_node=analytics_agent, to_node=response_formatter_node),
        Edge(from_node=general_agent, to_node=response_formatter_node),
    ]
)

app = App(
    root_agent=root_agent,
    name="app",
)

