from fastapi import FastAPI
from pydantic import BaseModel
from main import get_supper_summary, get_refined_suggestions

app = FastAPI()

class QueryRequest(BaseModel):
    query: str

@app.post("/summary")
async def summary(req: QueryRequest):
    query = req.query.strip()
    words = query.split()
    
    # Check if query is vague (consistent with Streamlit)
    if len(words) < 3:
        suggestions = get_refined_suggestions(query)
        return {
            "status": "vague",
            "message": f"'{query}' is too vague. if you want you can try one of the suggested specific topics.",
            "suggestions": suggestions
        }

    result = get_supper_summary(query)

    if result is None:
        return {"status": "error", "message": "Failed to generate summary"}

    return {
        "status": "success",
        "data": result.dict()
    }
