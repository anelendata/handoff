import os
from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from sqlalchemy.orm import Session
from passlib.context import CryptContext

from . import models, schemas, database

# to get a string like this run:
# openssl rand -hex 32
SECRET_KEY = os.environ["SECRET_KEY"]
ALGORITHM = "HS256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# User
def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        email=user.email,
        hashed_password=hashed_password,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()


def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()


def get_user_by_username(db: Session, username: str):
    return get_user_by_email(db, username)


async def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)):
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
        token_data = schemas.TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user_by_username(db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: schemas.User = Depends(get_current_user)
):
    if current_user.deactivated:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def authenticate_user(db: Session, username: str, password: str):
    user = get_user_by_username(db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


# Organization
def create_organization(db: Session, org: schemas.OrganizationCreate):
    db_org = models.Organization(
        owner_id=org.owner_id,
        name=org.name,
        description=org.description,
    )
    db.add(db_org)
    db.commit()
    db.refresh(db_org)
    return db_org


def get_organizations(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Organization).offset(skip).limit(limit).all()


def get_organization_by_name(db: Session, name: str):
    return db.query(models.User).filter(
        models.Organization.name == name).first()


def create_user_organization(
        db: Session,
        org: schemas.OrganizationCreate,
        user_id: int,
):
    db_organization = models.Organization(**org.dict(), owner_id=user_id)
    db.add(db_organization)
    db.commit()
    db.refresh(db_organization)
    return db_organization
