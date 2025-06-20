#!/usr/bin/env python3
"""
Database migration runner script for the Auth Service.
"""

import sys
import os
from alembic import command
from alembic.config import Config

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def run_migrations():
    """Run all pending database migrations."""
    try:
        # Get the alembic.ini file path
        alembic_cfg_path = os.path.join(os.path.dirname(__file__), '..', 'alembic.ini')
        
        # Create Alembic configuration
        alembic_cfg = Config(alembic_cfg_path)
        
        # Set the script location
        script_location = os.path.join(os.path.dirname(__file__), '..', 'src', 'migrations')
        alembic_cfg.set_main_option('script_location', script_location)
        
        print("Running database migrations...")
        
        # Run migrations
        command.upgrade(alembic_cfg, "head")
        
        print("✅ Database migrations completed successfully!")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        sys.exit(1)

def create_migration(message: str):
    """Create a new migration file."""
    try:
        alembic_cfg_path = os.path.join(os.path.dirname(__file__), '..', 'alembic.ini')
        alembic_cfg = Config(alembic_cfg_path)
        
        script_location = os.path.join(os.path.dirname(__file__), '..', 'src', 'migrations')
        alembic_cfg.set_main_option('script_location', script_location)
        
        print(f"Creating migration: {message}")
        command.revision(alembic_cfg, message=message, autogenerate=True)
        print("✅ Migration file created successfully!")
        
    except Exception as e:
        print(f"❌ Failed to create migration: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "create" and len(sys.argv) > 2:
            create_migration(" ".join(sys.argv[2:]))
        else:
            print("Usage: python run_migrations.py [create <message>]")
    else:
        run_migrations()