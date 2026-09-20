import sqlite3
from pwdlib import PasswordHash
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
import jwt

from datetime import datetime, timedelta, timezone

SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"



#user registriation register/login
router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

#user creation 
class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str


password_hash = PasswordHash.recommended()


# Return the hashed password
def hash_password(password):
    return password_hash.hash(password)

# compare entered password with hashed password
def verify_password(password, hashed_password):
    return password_hash.verify(password, hashed_password)

#create 30 minute token for authorized user
def create_access_token(username):
    expire = datetime.now(timezone.utc) + timedelta(minutes=30)
    payload = {
        "sub": username,
        "exp": expire
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    return token

#get the current user aut token and if in db
def get_current_user(token = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")

        if username is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid Authentication Credentials"
            )

    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )

    connection = sqlite3.connect("products.db")
    cursor = connection.cursor()

    cursor.execute("""
        SELECT * FROM users
        WHERE username = ?
        
    """,(username,))

    db_user = cursor.fetchone()
    connection.close()

    if db_user is None:
        raise HTTPException(
            status_code=401,
            detail= "User not found"
        )
    
    return db_user

def require_admin(current_user = Depends(get_current_user)):
    if current_user[4] != "admin":
        raise HTTPException(
            status_code=403,
            detail="Admin Credentials needed. I know who you are, but you dont have permission to do this. "
        )




#FastAPI recieves the request body and pydantic validates it 
@router.post("/register")
def register_user(user: UserCreate):
    #takes user password from UserCreate and adds
    hashed_password = hash_password(user.password)

    #creates a connection for register in the db
    connection = sqlite3.connect("products.db")
    cursor = connection.cursor()

    try:
        #inserting values into the usr, email, and hashed password not password because we need it hashed
        cursor.execute("""
            INSERT INTO users (username, email, password_hash)
            VALUES(?,?,?)""",
            
        (user.username, user.email, hashed_password))
        connection.commit()

    # if username already exists creating your status code 400 with expl 
    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=400,
            detail="Username or email already exists"
        )
    #close connection
    finally:
        connection.close()

    return {
        "message": "User registered successfully congrats",
        "username": user.username,
        "email": user.email,
        "password reminder": "Please keep use a discreet way to remember your password!"

    }
    #end of register_user




#login route
@router.post("/login")
def login_user(form_data = Depends(OAuth2PasswordRequestForm)):

    connection = sqlite3.connect("products.db")
    cursor = connection.cursor()

    cursor.execute("""
        SELECT * FROM users
        WHERE username = ?

    """, (form_data.username,)) 

    db_user = cursor.fetchone()

    if db_user is None:
        connection.close()
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )

    if not verify_password(form_data.password, db_user[3]):
        connection.close()
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )
    connection.close()

    access_token = create_access_token(db_user[1])

    return {
        "message": "Login succesfull",
        "username": db_user[1],
        "access_token": access_token,
        "token_type": "bearer"
    }

@router.get("/me")
def get_me(current_user = Depends(get_current_user)):
    return {
        "username": current_user[1],
        "email": current_user[2],
        "role": current_user[4]
    }

#connect to data base same db that the products are stored
connection = sqlite3.connect("products.db")
cursor = connection.cursor()

#create user tabled
cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'user'
)
""")

connection.commit()
connection.close()


