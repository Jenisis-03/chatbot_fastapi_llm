import re
import json
from typing import Dict, Any, Optional
from dataclasses import dataclass
from .medical_tools import MedicalTools
from config.settings import client, api_enabled

@dataclass
class ToolResponse:
    tool: str
    params: Dict[str, Any]
    result: Optional[str] = None
    error: Optional[str] = None

class QueryBuilder:
    def __init__(self, model_name: str = "gpt-3.5-turbo"):
        self.model = model_name if api_enabled else None
        self.tools = MedicalTools()
        self.routing_prompt = """
You are a medical assistant chatbot. Your task is to deeply understand the user's query and map it to the appropriate tool and parameters. The user may phrase their query in natural language, and you should interpret it intelligently. Respond ONLY with a valid JSON object in the format {"tool": "function_name", "params": {"param1": "value1"}}, with no extra text, newlines, or comments.
Available tools and their required parameters:
- get_doctor_appointment: doctor_name (string, lowercase), date (string in format "YYYY-MM-DD", e.g., "2025-06-10")
- get_medicine_info: medicine_name (string, lowercase)
- get_lab_report: patient_id (string)
- get_patient_appointments: patient_id (string)
- get_patient_details: patient_id (string)
Instructions:
1. Interpret the user's intent and extract the relevant tool and parameters.
2. For dates, convert natural language dates (e.g., "June 10th", "next week") to the format "YYYY-MM-DD". Today's date is 2025-06-09.
3. If the query is ambiguous or missing information, make a best guess or return an error in the format {"tool": "none", "params": {}, "error": "error message"}.
4. If the query doesn't match any tool, return {"tool": "none", "params": {}, "error": "Unable to understand query."}.
Examples:
- Query: "Book appointment with Dr. Smith on June 10th"
  Response: {"tool": "get_doctor_appointment", "params": {"doctor_name": "smith", "date": "2025-06-10"}}
- Query: "Can I see Dr. Jones tomorrow?"
  Response: {"tool": "get_doctor_appointment", "params": {"doctor_name": "jones", "date": "2025-06-10"}}
- Query: "What’s the info on aspirin?"
  Response: {"tool": "get_medicine_info", "params": {"medicine_name": "aspirin"}}
- Query: "Show lab report for patient 123"
  Response: {"tool": "get_lab_report", "params": {"patient_id": "123"}}
- Query: "Who is patient 456?"
  Response: {"tool": "get_patient_details", "params": {"patient_id": "456"}}
- Query: "Appointments for patient 789"
  Response: {"tool": "get_patient_appointments", "params": {"patient_id": "789"}}
- Query: "Book appointment with Dr. Smith"
  Response: {"tool": "get_doctor_appointment", "params": {}, "error": "Please provide the date for the appointment."}
- Query: "Hello world"
  Response: {"tool": "none", "params": {}, "error": "Unable to understand query."}
Query: {query}
"""

    def manual_parse_query(self, query: str) -> ToolResponse:
        print(f"Manual parsing query: {query}")
        query_lower = query.lower().strip()

        if "book appointment" in query_lower:
            doc_match = re.search(r'dr\.?\s+(\w+)', query_lower)
            date_match = re.search(r'(june\s+\d+|2025-\d+-\d+)', query_lower)
            if doc_match and date_match:
                date = date_match.group(1).replace("june ", "2025-06-").replace("th", "")
                return ToolResponse(
                    tool="get_doctor_appointment",
                    params={"doctor_name": doc_match.group(1), "date": date}
                )
            return ToolResponse(
                tool="get_doctor_appointment",
                params={},
                error="Please provide both doctor name and date for appointment booking."
            )

        if "medicine info" in query_lower or "get medicine info" in query_lower:
            med_match = re.search(r'(?:medicine info for|info for)\s+(\w+)', query_lower)
            if med_match:
                return ToolResponse(
                    tool="get_medicine_info",
                    params={"medicine_name": med_match.group(1)}
                )
            return ToolResponse(
                tool="get_medicine_info",
                params={},
                error="Please provide a medicine name to get information."
            )

        if "patient details" in query_lower or "patient info" in query_lower:
            id_match = re.search(r'\b(\d+)\b', query)
            if id_match:
                return ToolResponse(
                    tool="get_patient_details",
                    params={"patient_id": id_match.group(1)}
                )
            return ToolResponse(
                tool="get_patient_details",
                params={},
                error="Please provide a patient ID to get patient details."
            )

        if "appointments for patient" in query_lower or "patient appointments" in query_lower:
            id_match = re.search(r'\b(\d+)\b', query)
            if id_match:
                return ToolResponse(
                    tool="get_patient_appointments",
                    params={"patient_id": id_match.group(1)}
                )
            return ToolResponse(
                tool="get_patient_appointments",
                params={},
                error="Please provide a patient ID to check appointments."
            )

        if "lab report" in query_lower or "show lab report" in query_lower:
            id_match = re.search(r'\b(\d+)\b', query)
            if id_match:
                return ToolResponse(
                    tool="get_lab_report",
                    params={"patient_id": id_match.group(1)}
                )
            return ToolResponse(
                tool="get_lab_report",
                params={},
                error="Please provide a patient ID to get the lab report."
            )

        return ToolResponse(
            tool="none",
            params={},
            error="Unable to parse query. Please try a query like 'Book appointment with Dr. Smith on June 10th' or 'Get medicine info for aspirin'."
        )

    def parse_query(self, query: str, retries: int = 3, timeout: float = 10.0) -> ToolResponse:
        if not api_enabled or self.model is None:
            print("API disabled, using manual parsing.")
            return self.manual_parse_query(query)
        for attempt in range(retries):
            try:
                prompt = self.routing_prompt.format(query=query)
                response = client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant that parses medical queries into structured JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=150,
                    temperature=0.0,
                    timeout=timeout
                )
                response_text = response.choices[0].message.content.strip()
                print(f"Attempt {attempt + 1} - ChatGPT Response: {response_text}")
                tool_data = json.loads(response_text)
                if "tool" not in tool_data or "params" not in tool_data:
                    return ToolResponse(
                        tool="none",
                        params={},
                        error="Invalid ChatGPT response format."
                    )
                if "error" in tool_data:
                    return ToolResponse(
                        tool=tool_data["tool"],
                        params=tool_data["params"],
                        error=tool_data["error"]
                    )
                return ToolResponse(
                    tool=tool_data["tool"],
                    params=tool_data["params"]
                )
            except (json.JSONDecodeError, Exception) as e:
                print(f"Error on attempt {attempt + 1}: {str(e)}")
                if attempt == retries - 1:
                    print("Falling back to manual parsing due to repeated ChatGPT failures.")
                    return self.manual_parse_query(query)
                continue

    def execute_tool(self, tool_response: ToolResponse) -> ToolResponse:
        if tool_response.error:
            return tool_response
        try:
            tool_name = tool_response.tool
            params = tool_response.params if tool_response.params is not None else {}

            required_params = {
                "get_doctor_appointment": ["doctor_name", "date"],
                "get_medicine_info": ["medicine_name"],
                "get_lab_report": ["patient_id"],
                "get_patient_appointments": ["patient_id"],
                "get_patient_details": ["patient_id"]
            }

            if api_enabled and self.model:
                validation_prompt = f"""
Validate the parameters for the tool '{tool_name}' with params: {json.dumps(params)}.
Available tools and required parameters:
- get_doctor_appointment: doctor_name, date
- get_medicine_info: medicine_name
- get_lab_report: patient_id
- get_patient_appointments: patient_id
- get_patient_details: patient_id
Return 'valid' if parameters are complete and appropriate, otherwise return an error message.
"""
                try:
                    validation_response = client.chat.completions.create(
                        model=self.model,
                        messages=[
                            {"role": "system", "content": "You are a helpful assistant that validates parameters."},
                            {"role": "user", "content": validation_prompt}
                        ],
                        max_tokens=50,
                        temperature=0.0,
                        timeout=10.0
                    )
                    validation_text = validation_response.choices[0].message.content.strip()
                    if validation_text != "valid":
                        return ToolResponse(
                            tool=tool_name,
                            params=params,
                            error=validation_text
                        )
                except Exception as e:
                    print(f"Validation failed: {str(e)}, falling back to manual validation.")
                    if tool_name in required_params:
                        missing_params = [p for p in required_params[tool_name] if p not in params or not params[p]]
                        if missing_params:
                            return ToolResponse(
                                tool=tool_name,
                                params=params,
                                error=f"Missing required parameters: {', '.join(missing_params)}."
                            )
            else:
                if tool_name in required_params:
                    missing_params = [p for p in required_params[tool_name] if p not in params or not params[p]]
                    if missing_params:
                        return ToolResponse(
                            tool=tool_name,
                            params=params,
                            error=f"Missing required parameters: {', '.join(missing_params)}."
                        )

            tool_functions = {
                "get_doctor_appointment": self.tools.get_doctor_appointment,
                "get_medicine_info": self.tools.get_medicine_info,
                "get_lab_report": self.tools.get_lab_report,
                "get_patient_appointments": self.tools.get_patient_appointments,
                "get_patient_details": self.tools.get_patient_details
            }

            if tool_name not in tool_functions:
                return ToolResponse(
                    tool=tool_name,
                    params=params,
                    error="Invalid tool selected."
                )

            result = tool_functions[tool_name](**params)
            return ToolResponse(
                tool=tool_name,
                params=params,
                result=result
            )
        except Exception as e:
            return ToolResponse(
                tool=tool_response.tool,
                params=tool_response.params if tool_response.params is not None else {},
                error=f"Error executing tool: {str(e)}"
            )