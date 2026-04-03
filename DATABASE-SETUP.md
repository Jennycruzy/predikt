"""
PostgreSQL Database Setup Guide
Complete instructions for setting up PostgreSQL with PREDIKT
"""

# ═══════════════════════════════════════════════════════════════════
# 1. INSTALL POSTGRESQL
# ═══════════════════════════════════════════════════════════════════

"""
macOS (Homebrew):
  brew install postgresql@15
  brew services start postgresql@15

Linux (Ubuntu/Debian):
  sudo apt-get install postgresql postgresql-contrib
  sudo service postgresql start

Windows:
  Download from https://www.postgresql.org/download/windows/
  Run installer and follow setup wizard
"""

# ═══════════════════════════════════════════════════════════════════
# 2. CREATE DATABASE AND USER
# ═══════════════════════════════════════════════════════════════════

"""
Open PostgreSQL shell:
  psql postgres

Then run these commands:

-- Create database
CREATE DATABASE predikt_db;

-- Create user with password
CREATE USER predikt_user WITH PASSWORD 'secure_password_here';

-- Grant privileges
ALTER ROLE predikt_user SET client_encoding TO 'utf8';
ALTER ROLE predikt_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE predikt_user SET default_transaction_deferrable TO on;
ALTER ROLE predikt_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE predikt_db TO predikt_user;

-- Connect to database
\c predikt_db

-- Grant schema privileges
GRANT USAGE ON SCHEMA public TO predikt_user;
GRANT CREATE ON SCHEMA public TO predikt_user;

-- Exit
\q
"""

# ═══════════════════════════════════════════════════════════════════
# 3. INSTALL PYTHON DEPENDENCIES
# ═══════════════════════════════════════════════════════════════════

"""
pip install sqlalchemy psycopg2-binary alembic python-dotenv
"""

# ═══════════════════════════════════════════════════════════════════
# 4. CONFIGURE ENVIRONMENT
# ═══════════════════════════════════════════════════════════════════

"""
Update .env file:

DATABASE_URL=postgresql://predikt_user:secure_password_here@localhost:5432/predikt_db
"""

# ═══════════════════════════════════════════════════════════════════
# 5. INITIALIZE DATABASE TABLES
# ═══════════════════════════════════════════════════════════════════

"""
In backend directory, run:

python3 -c "from models.database import init_db; init_db()"

Or from Python:

from models.database import init_db
init_db()
"""

# ═══════════════════════════════════════════════════════════════════
# 6. VERIFY CONNECTION
# ═══════════════════════════════════════════════════════════════════

"""
Run test script:

python3 << 'EOF'
from sqlalchemy import inspect
from models.database import engine

inspector = inspect(engine)
tables = inspector.get_table_names()
print("✅ Connected to database!")
print(f"Tables: {tables}")
EOF
"""

# ═══════════════════════════════════════════════════════════════════
# 7. DATABASE MODELS CREATED
# ═══════════════════════════════════════════════════════════════════

"""
✅ users
  - wallet_address (unique, indexed)
  - email
  - username
  - balance (mUSDL)
  - last_claim (timestamp)

✅ markets
  - question
  - category
  - deadline
  - creator_address
  - status (open, debating, resolved)
  - predikt (final percentage)
  - confidence (confidence score)

✅ predictions
  - market_id
  - user_id (AI validator)
  - model_name
  - prediction (0-1 confidence)
  - reasoning (text)
  - score (reputation)

✅ debates
  - market_id
  - round_number
  - challenger_model
  - defender_model
  - challenge_text
  - response_text

✅ challenges
  - prediction_id
  - challenger_model
  - challenge_type (logical, evidence, methodology)
  - challenge_text
  - is_valid (boolean)

✅ stakes
  - market_id
  - user_id
  - amount (mUSDL)
  - position (YES/NO)
  - payout

✅ validator_reputation
  - model_name
  - total_predictions
  - correct_predictions
  - accuracy
  - reputation_score (0-1000)
  - challenges_won
"""

# ═══════════════════════════════════════════════════════════════════
# 8. USING THE DATABASE IN CODE
# ═══════════════════════════════════════════════════════════════════

"""
In your FastAPI routers:

from sqlalchemy.orm import Session
from models.database import get_db
from models.database import User, Market, Prediction

@app.get("/markets")
def list_markets(db: Session = Depends(get_db)):
    markets = db.query(Market).filter(Market.status == "open").all()
    return markets

@app.post("/create-market")
def create_market(question: str, deadline: str, db: Session = Depends(get_db)):
    market = Market(
        question=question,
        deadline=datetime.fromisoformat(deadline),
        creator_address="0x...",
        category="general"
    )
    db.add(market)
    db.commit()
    db.refresh(market)
    return market
"""

# ═══════════════════════════════════════════════════════════════════
# 9. MIGRATIONS (OPTIONAL - ALEMBIC)
# ═══════════════════════════════════════════════════════════════════

"""
Setup Alembic for schema migrations:

alembic init alembic

Update alembic/env.py to use your models.

Create migration:
  alembic revision --autogenerate -m "Add users table"

Apply migration:
  alembic upgrade head

Rollback:
  alembic downgrade -1
"""

# ═══════════════════════════════════════════════════════════════════
# 10. TROUBLESHOOTING
# ═══════════════════════════════════════════════════════════════════

"""
Connection refused:
  - Check PostgreSQL is running
  - Verify credentials in DATABASE_URL
  - Check database exists: psql -l

Authentication failed:
  - Reset password: ALTER USER predikt_user PASSWORD 'newpass';
  - Check username spelling
  - Verify database user has privileges

Import errors:
  - pip install sqlalchemy psycopg2-binary
  - pip install --upgrade psycopg2-binary

Tables not created:
  - Run: python3 -c "from models.database import init_db; init_db()"
  - Check if schema public exists: \dn

Slow queries:
  - Create indexes: CREATE INDEX idx_market_status ON markets(status);
  - Vacuum: VACUUM ANALYZE markets;
"""
