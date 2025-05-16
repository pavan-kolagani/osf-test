import logging
import os
import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Boolean,
    ForeignKey,
    DateTime,
    Enum,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import enum

# Suppress everything except print statements
logging.getLogger().setLevel(logging.ERROR)

# Base class
Base = declarative_base()

# Enums for visibility and split ratio
class VisibilityEnum(enum.Enum):
    PRIVATE = "private"
    EMBARGOED = "embargoed"
    PUBLIC = "public"

class SplitRatioEnum(enum.Enum):
    RATIO_60_20_20 = "60-20-20"
    RATIO_70_15_15 = "70-15-15"
    RATIO_80_10_10 = "80-10-10"

# User table
class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=True)
    role = Column(String, nullable=False)  # 'peer' or 'scholar'
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    repositories = relationship('Repository', back_populates='owner')
    access_logs = relationship('AccessLog', back_populates='user')

# Repository table
class Repository(Base):
    __tablename__ = 'repositories'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    repo_name = Column(String, unique=True, nullable=False)
    description = Column(String, nullable=True)
    
    visibility = Column(Enum(VisibilityEnum), default=VisibilityEnum.PRIVATE)
    split_column = Column(String, nullable=True)
    split_ratio = Column(Enum(SplitRatioEnum), nullable=True)
    
    permalink = Column(String, unique=True, default=lambda: str(uuid.uuid4()))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    owner = relationship('User', back_populates='repositories')
    datasets = relationship('Dataset', back_populates='repository')
    access_logs = relationship('AccessLog', back_populates='repository')

# Dataset table
class Dataset(Base):
    __tablename__ = 'datasets'

    id = Column(Integer, primary_key=True)
    repository_id = Column(Integer, ForeignKey('repositories.id'), nullable=False)
    dataset_type = Column(String, nullable=False)  # 'train', 'test', 'validation', 'analysis'
    location = Column(String, nullable=False)  # file path
    uploaded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationship
    repository = relationship('Repository', back_populates='datasets')

# Access log table
class AccessLog(Base):
    __tablename__ = 'access_logs'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    repository_id = Column(Integer, ForeignKey('repositories.id'), nullable=False)
    accessed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    action = Column(String, nullable=False)  # 'upload', 'download'

    # Relationships
    user = relationship('User', back_populates='access_logs')
    repository = relationship('Repository', back_populates='access_logs')

# DB Setup
db_path = os.path.join(os.path.dirname(__file__), 'poc.db')
engine = create_engine(f"sqlite:///{db_path}", echo=True)
SessionLocal = sessionmaker(bind=engine)

def init_db():
    Base.metadata.create_all(engine)
