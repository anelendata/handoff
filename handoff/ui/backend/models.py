from sqlalchemy import Table, Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from .database import Base


member_organization = Table(
    "member_organization_fk",
    Base.metadata,
    Column("member_id", Integer, ForeignKey("user.id")),
    Column("organization_id", Integer, ForeignKey("organization.id")),
)


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    deactivated = Column(Boolean, default=False)
    organizations = relationship(
        "Organization",
        secondary="member_organization_fk",
        backref="members",
    )


class Organization(Base):
    __tablename__ = "organization"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(String, index=True)
    owner_id = Column(Integer, ForeignKey('user.id'))
    owner = relationship("User", backref="owned_orgs")
