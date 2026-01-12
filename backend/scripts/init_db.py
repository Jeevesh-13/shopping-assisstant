import json
import sys

from app.database.db import init_db, get_db_context, engine
from app.database.models import MobilePhoneDB
from app.observability.logging import get_logger

logger = get_logger(__name__)

MOBILE_PHONES_DATA = json.load(open("/Users/jeeveshnandan/Documents/Development/shopping_agent/data/mobiles_data.json"))


def seed_database():
    logger.info("Starting database initialization...")
    
    # Initialize database (create tables)
    init_db()
    
    # Seed data
    with get_db_context() as db:
        # Check if data already exists
        existing_count = db.query(MobilePhoneDB).count()
        
        if existing_count > 0:
            logger.info(f"Database already contains {existing_count} phones. Skipping seed.")
            return
        
        logger.info(f"Seeding database with {len(MOBILE_PHONES_DATA)} mobile phones...")
        
        for phone_data in MOBILE_PHONES_DATA:
            phone = MobilePhoneDB(**phone_data)
            db.add(phone)
        
        db.commit()
        logger.info(f"Successfully seeded {len(MOBILE_PHONES_DATA)} mobile phones!")


def reset_database():
    """Reset database - drop all tables and recreate."""
    logger.warning("Resetting database - all data will be lost!")
    from app.database.models import Base
    Base.metadata.drop_all(bind=engine)
    init_db()
    seed_database()
    logger.info("Database reset complete!")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--reset":
        reset_database()
    else:
        seed_database()
