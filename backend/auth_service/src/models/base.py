"""Shared SQLAlchemy base for all models."""

from sqlalchemy.ext.declarative import declarative_base

# Single shared base for all models to prevent conflicts
Base = declarative_base()