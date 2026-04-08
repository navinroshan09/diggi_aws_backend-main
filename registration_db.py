import os
import bcrypt
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def create_connection():
    """
    Create a connection to the PostgreSQL database.
    Uses environment variables for database credentials.
    """
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "ec2-3-93-174-181.compute-1.amazonaws.com"),
            port=os.getenv("DB_PORT", "5432"),
            database=os.getenv("DB_NAME", "diggi_login_db"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "Rs@181075")
        )
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None

def create_table():
    """
    Create the users table if it does not exist.
    """
    conn = create_connection()
    if conn is None:
        return
    cur = conn.cursor()
    sql = """
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        full_name TEXT NOT NULL,
        phone TEXT NOT NULL UNIQUE,
        country TEXT,
        gender TEXT,
        date_of_birth DATE,
        profile_pic TEXT,
        email TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    try:
        cur.execute(sql)
        conn.commit()
        print("Table created successfully")
    except Exception as e:
        print(f"Error creating table: {e}")
    finally:
        cur.close()
        conn.close()

def insert_user(data):
    """
    Insert a new user into the users table.
    Expects data as a dictionary with keys: full_name, phone, country, gender, date_of_birth, profile_pic, email, password
    Password will be hashed before insertion.
    """
    conn = create_connection()
    if conn is None:
        return
    cur = conn.cursor()
    
    # Hash the password
    hashed_password = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    sql = """
    INSERT INTO users (full_name, phone, country, gender, date_of_birth, profile_pic, email, password)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    values = (
        data['full_name'],
        data['phone'],
        data['country'],
        data['gender'],
        data['date_of_birth'],
        data['profile_pic'],
        data['email'],
        hashed_password
    )
    
    try:
        cur.execute(sql, values)
        conn.commit()
        print("User inserted successfully")
        return True
    except Exception as e:
        conn.rollback()
        print(f"Error inserting user: {e}")
        raise
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    print("Creating users table...")
    create_table()
