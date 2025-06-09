from fastapi import FastAPI, HTTPException
from datetime import datetime
from models.query import QueryRequest, QueryResponse
from services.query_builder import QueryBuilder
from config.settings import api_enabled

# Construct the description based on API status
api_status = "Using Gemini API for query parsing." if api_enabled else "Gemini API disabled; using manual parsing (may be less accurate for complex queries)."
app_description = f"""
API for processing medical queries related to appointments, medicines, lab reports, and patient details.
**API Status**: {api_status}
"""

app = FastAPI(
    title="Medical Assistant API",
    description=app_description,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

@app.post(
    "/query",
    response_model=QueryResponse,
    summary="Process a Medical Query",
    description="Process a natural language query related to medical services such as booking appointments, retrieving medicine info, lab reports, patient appointments, or patient details.",
    responses={
        200: {
            "description": "Successful response with the query result or an error message",
            "content": {
                "application/json": {
                    "example": {
                        "result": "Appointment booked with Dr. Smith on 2025-06-10",
                        "error": None  # Changed 'null' to 'None'
                    }
                }
            }
        },
        500: {
            "description": "Internal server error",
            "content": {
                "application/json": {
                    "example": {"detail": "Error processing query: <error message>"}
                }
            }
        }
    }
)
async def process_medical_query(request: QueryRequest):
    try:
        query_builder = QueryBuilder()
        tool_response = query_builder.parse_query(request.query)
        print(f"Tool response after parsing: {tool_response}")
        tool_response = query_builder.execute_tool(tool_response)
        print(f"Tool response after execution: {tool_response}")
        if tool_response.error:
            return QueryResponse(error=tool_response.error)
        return QueryResponse(result=tool_response.result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

@app.get(
    "/health",
    summary="Check API Health",
    description="Check the health status of the Medical Assistant API.",
    responses={
        200: {
            "description": "API is healthy",
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "timestamp": "2025-06-09T16:55:00.123456"
                    }
                }
            }
        }
    }
)
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)