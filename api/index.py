from fastapi import FastAPI
from pydantic import BaseModel
from main import get_supper_summary

app = FastAPI()

class QueryRequest(BaseModel):
    query: str

@app.post("/summary")
async def summary(req: QueryRequest):
    result = get_supper_summary(req.query)

    if result is None:
        return {"status": "error", "message": "Failed to generate summary"}

    return {
        "status": "success",
        "data": result.dict()
    }