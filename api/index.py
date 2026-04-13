import os
import psycopg2
from dotenv import load_dotenv
from fastapi import HTTPException, FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import bcrypt
from main import get_supper_summary, get_refined_suggestions

load_dotenv()

def create_connection():
    """Create a connection to the PostgreSQL database."""
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "thediggi.com"),
            port=os.getenv("DB_PORT", "5432"),
            database=os.getenv("DB_NAME", "diggi_login_db"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "Rs@181075")
        )
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None

def insert_user(data):
    """Insert a new user into the users table."""
    conn = create_connection()
    if conn is None:
        return
    cur = conn.cursor()
    hashed_password = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    sql = """
    INSERT INTO users (full_name, phone, country, gender, date_of_birth, profile_pic, email, password)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    values = (data['full_name'], data['phone'], data['country'], data['gender'],
              data['date_of_birth'], data['profile_pic'], data['email'], hashed_password)
    try:
        cur.execute(sql, values)
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://thediggi.com", "http://www.thediggi.com"],
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

