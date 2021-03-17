import datetime, re
from typing import List

from fastapi import APIRouter, status
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from sqlalchemy.orm import Session

from handoff.ui.backend import crud, models, schemas, database

router = APIRouter()

ACCESS_TOKEN_EXPIRE_MINUTES = 30


@router.post("/token", response_model=schemas.Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(crud.get_db),
):
    user = crud.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = datetime.timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = crud.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {
      "access_token": access_token,
      "token_type": "bearer"
    }


@router.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(crud.get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db=db, user=user)


@router.get("/users/", response_model=List[schemas.User])
def read_users(
        skip: int = 0,
        limit: int = 100,
        db: Session = Depends(crud.get_db),
):
    users = crud.get_users(db, skip=skip, limit=limit)
    return users


@router.get("/users/{user_id}", response_model=schemas.User)
def read_user(user_id: int, db: Session = Depends(crud.get_db)):
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@router.post(
    "/users/{user_id}/organizations/",
    response_model=schemas.Organization,
)
def create_organization_for_user(
    owner_id: int,
    organization: schemas.OrganizationCreate,
    db: Session = Depends(crud.get_db)
):
    return crud.create_user_organization(
        db=db,
        organization=organization,
        owner_id=owner_id)


@router.get("/users/me/", response_model=schemas.User)
async def read_users_me(
    current_user: schemas.User = Depends(crud.get_current_active_user)
):
    return current_user


@router.post("/organizations/", response_model=schemas.Organization)
def create_organization(
        org: schemas.OrganizationCreate,
        db: Session = Depends(crud.get_db)
):
    if not re.compile("^[a-z0-9_]{3,16}$").match(org.name):
        raise HTTPException(
            status_code=400,
            detail="Organization name must be 3 to 16 characters with a-z, 0-9, or _")
    db_org = crud.get_organization_by_name(db, name=org.name)
    if db_org:
        raise HTTPException(
            status_code=400,
            detail="Organization already registered")
    return crud.create_organization(db=db, org=org)


@router.get("/organizations/", response_model=List[schemas.Organization])
def read_organizations(
        skip: int = 0,
        limit: int = 100,
        db: Session = Depends(crud.get_db),
):
    orgs = crud.get_organizations(db, skip=skip, limit=limit)
    return orgs

