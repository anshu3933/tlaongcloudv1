"""Startup script for async worker processes"""

import asyncio
import logging
import os
import sys
import signal
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.workers.sqlite_async_worker import start_worker_pool
from src.database import init_db

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Main worker startup function"""
    logger.info("🚀 Starting Async IEP Generation Worker System")
    
    # Check environment variables
    if not os.getenv("GEMINI_API_KEY"):
        logger.error("❌ GEMINI_API_KEY environment variable not set")
        logger.error("Please set your Gemini API key to enable AI generation")
        return False
    
    # Initialize database
    try:
        await init_db()
        logger.info("✅ Database initialized successfully")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        return False
    
    # Configuration
    num_workers = int(os.getenv("NUM_WORKERS", "1"))
    poll_interval = int(os.getenv("POLL_INTERVAL", "5"))
    
    logger.info(f"Configuration:")
    logger.info(f"  Workers: {num_workers}")
    logger.info(f"  Poll Interval: {poll_interval}s")
    logger.info(f"  Database: {os.getenv('DATABASE_URL', 'default SQLite')}")
    
    # Start worker pool
    try:
        logger.info("🏃‍♂️ Starting worker pool...")
        await start_worker_pool(num_workers=num_workers, poll_interval=poll_interval)
    except KeyboardInterrupt:
        logger.info("👋 Shutdown requested by user")
        return True
    except Exception as e:
        logger.error(f"❌ Worker pool failed: {e}")
        return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Async IEP Generation Worker")
    parser.add_argument("--workers", type=int, default=1, help="Number of workers (1 for SQLite)")
    parser.add_argument("--poll-interval", type=int, default=5, help="Poll interval in seconds")
    parser.add_argument("--test", action="store_true", help="Run in test mode with sample job")
    
    args = parser.parse_args()
    
    # Set environment variables from args
    os.environ["NUM_WORKERS"] = str(args.workers)
    os.environ["POLL_INTERVAL"] = str(args.poll_interval)
    
    # Set default environment for development
    os.environ.setdefault("ENVIRONMENT", "development")
    os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./special_ed.db")
    
    if args.test:
        logger.info("🧪 Running in test mode")
        # Import and run test
        from test_async_system import run_all_tests
        success = asyncio.run(run_all_tests())
        sys.exit(0 if success else 1)
    else:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)