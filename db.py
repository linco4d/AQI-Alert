from __future__ import annotations
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from .config import settings

class Base(DeclarativeBase): pass

_engine = create_engine(settings.db_url, future=True)
SessionLocal = sessionmaker(bind=_engine, autoflush=False, expire_on_commit=False, future=True)

def get_engine():
    return _engine

def create_all(base=Base):
    base.metadata.create_all(_engine)
