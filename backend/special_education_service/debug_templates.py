#!/usr/bin/env python3
"""Debug script to check template initialization"""

import asyncio
import sys
import os

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

async def main():
    from src.database import init_database, get_db_session
    from src.models.special_education_models import IEPTemplate, DisabilityType
    from sqlalchemy import select
    
    print("Checking templates in database...")
    
    async with get_db_session() as session:
        # Check existing templates
        result = await session.execute(select(IEPTemplate))
        templates = result.scalars().all()
        print(f"Found {len(templates)} existing templates")
        
        for template in templates:
            print(f"  - {template.name} (ID: {template.id})")
        
        # Check disability types
        result = await session.execute(select(DisabilityType))
        disabilities = result.scalars().all()
        print(f"Found {len(disabilities)} disability types")
        
        for disability in disabilities[:3]:
            print(f"  - {disability.name} ({disability.code})")
    
    print("\nRunning database initialization...")
    await init_database()
    print("Initialization complete")
    
    print("\nChecking templates after initialization...")
    async with get_db_session() as session:
        result = await session.execute(select(IEPTemplate))
        templates = result.scalars().all()
        print(f"Found {len(templates)} templates after init")
        
        for template in templates[:5]:
            print(f"  - {template.name} (ID: {template.id})")

if __name__ == "__main__":
    asyncio.run(main())