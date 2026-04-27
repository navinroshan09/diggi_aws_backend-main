import os
import psycopg2
from dotenv import load_dotenv
from fastapi import HTTPException, FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import bcrypt
from main import get_supper_summary, get_refined_suggestions, get_top_news_with_content
from credibility import compute_credibility, get_confidence_label

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
    allow_origins=["http://thediggi.com", "http://www.thediggi.com", "http://localhost:5173", "http://localhost:3000"],
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
    confirm_password: str


class UserLogin(BaseModel):
    email: str
    password: str


class UserProfileRequest(BaseModel):
    email: str
    full_name: str | None = None
    phone: str | None = None
    country: str | None = None
    gender: str | None = None
    date_of_birth: str | None = None
    profile_pic: str | None = None


@app.post("/register")
async def register(user: UserRegister):
    if user.password != user.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")
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


@app.get("/profile")
async def get_profile(email: str):
    conn = create_connection()
    if conn is None:
        raise HTTPException(status_code=500, detail="Database connection failed")

    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT email, full_name, phone, country, gender, date_of_birth, profile_pic
            FROM users
            WHERE email = %s
            """,
            (email,),
        )
        row = cur.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="User profile not found")

        return {
            "status": "success",
            "data": {
                "email": row[0],
                "full_name": row[1] or "",
                "phone": row[2] or "",
                "country": row[3] or "",
                "gender": row[4] or "",
                "date_of_birth": row[5].isoformat() if row[5] else "",
                "profile_pic": row[6] or "",
            },
        }
    finally:
        cur.close()
        conn.close()


@app.put("/profile")
async def update_profile(user: UserProfileRequest):
    conn = create_connection()
    if conn is None:
        raise HTTPException(status_code=500, detail="Database connection failed")

    cur = conn.cursor()
    try:
        cur.execute("SELECT email FROM users WHERE email = %s", (user.email,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="User profile not found")

        fields = []
        values = []

        if user.full_name is not None:
            fields.append("full_name = %s")
            values.append(user.full_name)
        if user.phone is not None:
            fields.append("phone = %s")
            values.append(user.phone)
        if user.country is not None:
            fields.append("country = %s")
            values.append(user.country)
        if user.gender is not None:
            fields.append("gender = %s")
            values.append(user.gender)
        if user.date_of_birth is not None:
            fields.append("date_of_birth = %s")
            values.append(user.date_of_birth)
        if user.profile_pic is not None:
            fields.append("profile_pic = %s")
            values.append(user.profile_pic)

        if not fields:
            raise HTTPException(status_code=400, detail="No profile fields provided")

        values.append(user.email)
        sql = f"UPDATE users SET {', '.join(fields)} WHERE email = %s"
        cur.execute(sql, tuple(values))
        conn.commit()

        cur.execute(
            """
            SELECT email, full_name, phone, country, gender, date_of_birth, profile_pic
            FROM users
            WHERE email = %s
            """,
            (user.email,),
        )
        row = cur.fetchone()

        return {
            "status": "success",
            "message": "Profile updated successfully",
            "data": {
                "email": row[0],
                "full_name": row[1] or "",
                "phone": row[2] or "",
                "country": row[3] or "",
                "gender": row[4] or "",
                "date_of_birth": row[5].isoformat() if row[5] else "",
                "profile_pic": row[6] or "",
            },
        }
    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cur.close()
        conn.close()

class QueryRequest(BaseModel):
    query: str

# @app.post("/summary")
# async def summary(req: QueryRequest):
#     query = req.query.strip()
#     words = query.split()
    
#     # Check if query is vague (consistent with Streamlit)
#     if len(words) < 3:
#         suggestions = get_refined_suggestions(query)
#         return {
#             "status": "vague",
#             "message": f"'{query}' is too vague. if you want you can try one of the suggested specific topics.",
#             "suggestions": suggestions
#         }

#     result = get_supper_summary(query)

#     if result is None:
#         return {"status": "error", "message": "Failed to generate summary"}

#     return {
#         "status": "success",
#         "data": result.dict()
#     }
@app.post("/summary")
async def summary(req: QueryRequest):
    query = req.query.strip()
    words = query.split()

    if len(words) < 3:
        suggestions = get_refined_suggestions(query)
        return {
            "status": "vague",
            "message": f"'{query}' is too vague.if you want you can try one of the suggested specific topics.",
            "suggestions": suggestions
        }

    # ✅ STEP 1: Fetch ONCE
    articles = get_top_news_with_content(query)

    if not articles:
        return {"status": "error", "message": "No articles found"}

    # ✅ STEP 2: AI processing
    result = get_supper_summary(articles)

    if result is None:
        return {"status": "error", "message": "Failed to generate summary"}

    # ✅ STEP 3: Ensure list
    if not isinstance(result, list):
        result = [result]

    # ✅ STEP 4: Credibility enhancement
    for i, article_analysis in enumerate(result):
        article = articles[i]

        claims = [
            c.claim for c in article_analysis.claim_level_focus.claims
        ]

        score = compute_credibility(article, articles, claims)

        article_analysis.credibility_signals.source_reliability = str(score)
        article_analysis.credibility_signals.confidence_level = get_confidence_label(score)

    # ✅ STEP 5: Return
    return {
        "status": "success",
        "data": [r.dict() for r in result]
    }