#!/usr/bin/env python3
"""
Initialize Database Script
Run this once to set up PostgreSQL tables and seed initial data
"""

import sys
import os
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models.database import (
    Base, engine, SessionLocal,
    User, Market, Prediction, ValidatorReputation, init_db
)


def init_database():
    """Initialize all database tables"""
    print("🔧 Initializing database...")
    try:
        init_db()
        print("✅ Database tables created successfully")
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False
    return True


def seed_validator_reputation():
    """Seed initial validator reputation data"""
    print("\n📊 Seeding validator reputation...")
    
    db = SessionLocal()
    validators = [
        {
            "model_name": "gpt-4o",
            "total_predictions": 0,
            "correct_predictions": 0,
            "accuracy": 0.0,
            "avg_confidence": 0.75,
            "reputation_score": 500.0,
        },
        {
            "model_name": "claude-3-opus",
            "total_predictions": 0,
            "correct_predictions": 0,
            "accuracy": 0.0,
            "avg_confidence": 0.70,
            "reputation_score": 500.0,
        },
        {
            "model_name": "gemini-pro",
            "total_predictions": 0,
            "correct_predictions": 0,
            "accuracy": 0.0,
            "avg_confidence": 0.68,
            "reputation_score": 500.0,
        },
        {
            "model_name": "llama-3",
            "total_predictions": 0,
            "correct_predictions": 0,
            "accuracy": 0.0,
            "avg_confidence": 0.65,
            "reputation_score": 500.0,
        },
        {
            "model_name": "mistral-large",
            "total_predictions": 0,
            "correct_predictions": 0,
            "accuracy": 0.0,
            "avg_confidence": 0.72,
            "reputation_score": 500.0,
        },
    ]

    try:
        for validator_data in validators:
            # Check if already exists
            existing = db.query(ValidatorReputation).filter(
                ValidatorReputation.model_name == validator_data["model_name"]
            ).first()
            
            if not existing:
                validator = ValidatorReputation(**validator_data)
                db.add(validator)
                print(f"  ✅ Added {validator_data['model_name']}")
        
        db.commit()
        print("✅ Validator reputation seeded successfully")
    except Exception as e:
        print(f"❌ Error seeding data: {e}")
        db.rollback()
        return False
    finally:
        db.close()
    
    return True


def verify_connection():
    """Verify database connection"""
    print("\n🔍 Verifying database connection...")
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        print("✅ Database connection verified")
        return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("\n📝 Make sure PostgreSQL is running and DATABASE_URL is set:")
        print("   DATABASE_URL=postgresql://user:password@localhost:5432/predikt_db")
        return False


def main():
    """Run initialization"""
    print("╔══════════════════════════════════════════════════════╗")
    print("║    predikt Database Initialization             ║")
    print("╚══════════════════════════════════════════════════════╝\n")

    # Verify connection first
    if not verify_connection():
        return False

    # Initialize database
    if not init_database():
        return False

    # Seed data
    if not seed_validator_reputation():
        return False

    print("\n╔══════════════════════════════════════════════════════╗")
    print("║    ✅ Database Ready!                               ║")
    print("╚══════════════════════════════════════════════════════╝\n")
    print("Next steps:")
    print("  1. Run: python3 -m uvicorn backend.main:app --reload")
    print("  2. Visit: http://localhost:8000/docs")
    print("  3. Test API endpoints\n")

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
