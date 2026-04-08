from fastapi import HTTPException
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import bcrypt
from main import get_supper_summary, get_refined_suggestions
from registration_db import insert_user, create_connection, create_table

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class UserRegister(BaseModel):
    full_name: str
    phone: str
    country: str
    gender: str
    date_of_birth: str
    profile_pic: str
    email: str
    password: str


class UserLogin(BaseModel):
    email: str
    password: str


@app.post("/register")
async def register(user: UserRegister):
    try:
        insert_user(user.dict())
        return {"status": "success", "message": "User created"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/login")
async def login(user: UserLogin):
    conn = create_connection()
    if conn is None:
        raise HTTPException(status_code=500, detail="Database connection failed")

    cur = conn.cursor()
    try:
        cur.execute("SELECT email, password FROM users WHERE email=%s", (user.email,))
        db_user = cur.fetchone()

        if not db_user:
            raise HTTPException(status_code=404, detail="User not found")

        stored_password = db_user[1]

        if not bcrypt.checkpw(user.password.encode(), stored_password.encode()):
            raise HTTPException(status_code=401, detail="Invalid password")

        return {"status": "success", "message": "Login success"}
    finally:
        cur.close()
        conn.close()

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

@app.on_event("startup")
def startup():
    create_table()
