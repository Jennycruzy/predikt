"""
PostgreSQL Database Models
SQLAlchemy ORM models for predikt

Install:
  pip install sqlalchemy psycopg2-binary alembic
"""

from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    Boolean,
    Text,
    ForeignKey,
    JSON,
    create_engine,
    event,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
import os

# Database URL from environment
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://user:password@localhost:5432/predikt_db"
)

# Create engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Verify connections before use
    echo=False,
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base for all models
Base = declarative_base()


class User(Base):
    """User accounts with wallet addresses"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    wallet_address = Column(String(42), unique=True, index=True)
    email = Column(String(255), unique=True, nullable=True)
    username = Column(String(255), unique=True, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_claim = Column(DateTime, nullable=True)
    balance = Column(Float, default=0.0)  # mUSDL balance

    # Relationships
    predictions = relationship("Prediction", back_populates="user")
    stakes = relationship("Stake", back_populates="user")

    def __repr__(self):
        return f"<User {self.wallet_address}>"


class Market(Base):
    """Prediction markets"""
    __tablename__ = "markets"

    id = Column(Integer, primary_key=True)
    chain_market_id = Column(String(255), unique=True, nullable=True)  # On-chain ID
    question = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=False)
    deadline = Column(DateTime, nullable=False)
    creator_address = Column(String(42), nullable=False)
    status = Column(String(50), default="open")  # open, debating, resolved
    predikt = Column(Float, nullable=True)  # Final predikt percentage
    confidence = Column(Float, nullable=True)  # Confidence level
    summary = Column(Text, nullable=True)  # AI summary
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)

    # Relationships
    predictions = relationship("Prediction", back_populates="market")
    stakes = relationship("Stake", back_populates="market")
    debates = relationship("Debate", back_populates="market")

    def __repr__(self):
        return f"<Market {self.id}: {self.question[:50]}...>"


class Prediction(Base):
    """AI validator predictions"""
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True)
    market_id = Column(Integer, ForeignKey("markets.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    model_name = Column(String(100), nullable=False)  # gpt-4o, claude, etc
    prediction = Column(Float, nullable=False)  # 0-1 confidence
    reasoning = Column(Text, nullable=False)
    reasoning_hash = Column(String(255), nullable=True)
    score = Column(Float, default=50.0)  # Reputation score
    accuracy = Column(Float, nullable=True)  # Calculated after resolution
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    market = relationship("Market", back_populates="predictions")
    user = relationship("User", back_populates="predictions")
    challenges = relationship("Challenge", back_populates="prediction")

    def __repr__(self):
        return f"<Prediction {self.id}: {self.model_name}>"


class Debate(Base):
    """Multi-round debates between validators"""
    __tablename__ = "debates"

    id = Column(Integer, primary_key=True)
    market_id = Column(Integer, ForeignKey("markets.id"), nullable=False)
    round_number = Column(Integer, default=1)
    challenger_model = Column(String(100), nullable=False)
    defender_model = Column(String(100), nullable=False)
    challenge_text = Column(Text, nullable=False)
    response_text = Column(Text, nullable=True)
    winner = Column(String(100), nullable=True)  # Determined by predikt
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    market = relationship("Market", back_populates="debates")

    def __repr__(self):
        return f"<Debate {self.id}: R{self.round_number}>"


class Challenge(Base):
    """Challenges to predictions"""
    __tablename__ = "challenges"

    id = Column(Integer, primary_key=True)
    prediction_id = Column(Integer, ForeignKey("predictions.id"), nullable=False)
    challenger_model = Column(String(100), nullable=False)
    challenge_type = Column(String(50), nullable=False)  # logical, evidence, methodology
    challenge_text = Column(Text, nullable=False)
    challenge_hash = Column(String(255), nullable=True)
    is_valid = Column(Boolean, nullable=True)  # Determined by predikt
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    prediction = relationship("Prediction", back_populates="challenges")

    def __repr__(self):
        return f"<Challenge {self.id}: {self.challenge_type}>"


class Stake(Base):
    """User stakes on market outcomes"""
    __tablename__ = "stakes"

    id = Column(Integer, primary_key=True)
    market_id = Column(Integer, ForeignKey("markets.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(Float, nullable=False)  # mUSDL amount
    position = Column(String(10), nullable=False)  # YES or NO
    payout = Column(Float, nullable=True)  # Calculated after resolution
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    market = relationship("Market", back_populates="stakes")
    user = relationship("User", back_populates="stakes")

    def __repr__(self):
        return f"<Stake {self.id}: {self.amount} mUSDL on {self.position}>"


class ValidatorReputation(Base):
    """Validator reputation tracking"""
    __tablename__ = "validator_reputation"

    id = Column(Integer, primary_key=True)
    model_name = Column(String(100), unique=True, nullable=False)
    total_predictions = Column(Integer, default=0)
    correct_predictions = Column(Integer, default=0)
    accuracy = Column(Float, default=0.0)
    avg_confidence = Column(Float, default=0.0)
    reputation_score = Column(Float, default=500.0)  # 0-1000 scale
    challenges_received = Column(Integer, default=0)
    challenges_won = Column(Integer, default=0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<ValidatorReputation {self.model_name}: {self.accuracy:.2%}>"


# Create all tables
def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created")


def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
