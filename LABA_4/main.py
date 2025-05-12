from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import *
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta, timezone
import bcrypt
import jwt
from jwt.exceptions import InvalidTokenError
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware


# Настройки
SQLALCHEMY_DATABASE_URL = "mysql+pymysql://isp_r_Gulyaev:12345@77.91.86.135/isp_r_Gulyaev"
SECRET_KEY = '8y7w4n9aoofd9h896409n5xgujbjnp9u'
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30




# База данных
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Модель пользователя
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), index=True)
    email = Column(String(100), unique=True, index=True)
    full_name = Column(String(100), nullable=True)
    hashed_password = Column(String(100))
    disabled = Column(Boolean, default=False)

Base.metadata.create_all(bind=engine)

# Pydantic модели
class UserCreate(BaseModel):
    username: str
    email: str
    full_name: str | None = None
    password: str

class UserUpdate(BaseModel):
    username: str | None = None
    email: str | None = None
    full_name: str | None = None
    password: str | None = None
    disabled: bool | None = None

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: str | None = None
    disabled: bool | None = None
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None

# Хеширование пароля
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(plain_password, hashed_password):
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

# Аутентификация
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/token')

def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

def authenticate_user(db: Session, username: str, password: str):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        print(f"User not found: {username}")
        return False
    print(f"User found: {user.username}")
    if not verify_password(password, user.hashed_password):
        print(f"Password mismatch for {username}")
        return False
    return user




def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        user = get_user_by_username(db, username)
        if user is None:
            raise credentials_exception
        return user
    except InvalidTokenError:
        raise credentials_exception

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

# Создание приложения
app = FastAPI()

# Роуты
@app.get("/", response_class=HTMLResponse)
async def get_client():
    with open("static/index.html", "r") as file:
        return file.read()

@app.post("/register", response_model=UserResponse)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    hashed_password = hash_password(user.password)
    db_user = User(username=user.username, email=user.email, full_name=user.full_name, hashed_password=hashed_password)
    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Username or Email already registered")

@app.get("/users/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return UserResponse(id=current_user.id, username=current_user.username, email=current_user.email, full_name=current_user.full_name, disabled=current_user.disabled)

@app.put("/users/{user_id}", response_model=UserResponse, dependencies=[Depends(get_current_user)])
def update_user(user_id: int, user_update: UserUpdate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    if user_update.username:
        user.username = user_update.username
    if user_update.email:
        user.email = user_update.email
    if user_update.full_name:
        user.full_name = user_update.full_name
    if user_update.password:
        user.hashed_password = hash_password(user_update.password)
    if user_update.disabled is not None:
        user.disabled = user_update.disabled
    db.commit()
    db.refresh(user)
    return user

@app.delete("/users/{user_id}", response_model=UserResponse, dependencies=[Depends(get_current_user)])
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
    return user


@app.get("/users/", response_model=list[UserResponse])
def get_users(
        db: Session = Depends(get_db),
        username: str | None = None,
        email: str | None = None
):
    query = db.query(User)
    if username:
        query = query.filter(User.username == username)
    if email:
        query = query.filter(User.email == email)

    users = query.all()
    if not users:
        raise HTTPException(status_code=404, detail="Users not found")
    return users

#Задание 6
#Задание 6
#Задание 6


class TokenBlacklist(Base):
    __tablename__ = "token_blacklist"
    id = Column(Integer, primary_key=True, index=True)
    refresh_token = Column(String(200), unique=True)
    revoked_at = Column(DateTime, default=datetime.utcnow)

def create_refresh_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(days=7))  # 1 week expiration for refresh token
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )

    print(f"Generated access token for {user.username}: {access_token}")  # Add this line

    refresh_token_expires = timedelta(days=7)
    refresh_token = create_refresh_token(data={"sub": user.username}, expires_delta=refresh_token_expires)

    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


@app.post("/refresh", response_model=Token)
async def refresh_access_token(refresh_token: str, db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        user = get_user_by_username(db, username)
        if user is None:
            raise credentials_exception

        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )

        return {"access_token": access_token, "token_type": "bearer"}
    except InvalidTokenError:
        raise credentials_exception


@app.post("/logout")
async def logout(refresh_token: str, db: Session = Depends(get_db)):
    token_in_db = db.query(TokenBlacklist).filter(TokenBlacklist.refresh_token == refresh_token).first()
    if token_in_db:
        raise HTTPException(status_code=400, detail="Refresh token already revoked")

    db_token = TokenBlacklist(refresh_token=refresh_token)
    db.add(db_token)
    db.commit()
    db.refresh(db_token)

    return {"detail": "Logout successful, refresh token revoked"}


origins = [
    "http://localhost.tiangolo.com",
    "https://localhost.tiangolo.com",
    "http://localhost",
    "http://localhost:8080",
    "http://127.0.0.1:8000/",
    "http://127.0.0.1",
    "http://127.0.0.1/",
    "127.0.0.1:8000/",
    "127.0.0.1",
    "127.0.0.1/",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Настройте разрешенные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



app.mount("/static", StaticFiles(directory="static"), name="static")
