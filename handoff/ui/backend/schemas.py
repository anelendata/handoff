from typing import List, Optional

from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class OrganizationBase(BaseModel):
    name: str
    owner_id: int
    description: Optional[str] = None


class OrganizationCreate(OrganizationBase):
    pass


class Organization(OrganizationBase):
    id: int

    class Config:
        orm_mode = True


class UserBase(BaseModel):
    email: str


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: int
    deactivated: bool
    memberships: List[Organization] = []
    profile_url: str

    class Config:
        orm_mode = True


class AWSCredentialBase(BaseModel):
    owner_id: int
    name: str


class AWSCredentialCreate(AWSCredentialBase):
    masked_key: str
    encrypted_key: str
    encrypted_secret: str
    region: str
    external_id: Optional[str] = None


class AWSCredential(AWSCredentialBase):
    id: int
    deactivated: bool

    class Config:
        orm_mode = True
