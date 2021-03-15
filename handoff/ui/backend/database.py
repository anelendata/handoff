from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from . import config

connect_args = {}
if config.DATABASE_URL.startswith("sqlite"):
    connect_args.update({"check_same_thread": False})

engine = create_engine(
    config.DATABASE_URL,
    connect_args=connect_args,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
