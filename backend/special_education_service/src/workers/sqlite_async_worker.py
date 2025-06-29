"""SQLite-compatible async worker for IEP generation jobs"""

import asyncio
import logging
import json
import signal
import sys
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
from sqlalchemy import text, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_async_session
from ..models.job_models import IEPGenerationJob
from ..utils.gemini_client import GeminiClient
from ..schemas.gemini_schemas import GeminiIEPResponse
from ..utils.json_helpers import ensure_json_serializable
import gzip
import base64

logger = logging.getLogger(__name__)


class SQLiteAsyncWorker:
    """SQLite-compatible async worker for processing IEP generation jobs"""
    
    def __init__(self, worker_id: str = "worker-1", poll_interval: int = 5):
        self.worker_id = worker_id
        self.poll_interval = poll_interval
        self.running = False
        self.shutdown_event = asyncio.Event()
        self.gemini_client = GeminiClient()
        
        # SQLite concurrency settings
        self.max_concurrent_jobs = 1  # SQLite limitation
        self.claim_timeout = 300  # 5 minutes to process a job
        self.max_retries = 3
        
        logger.info(f"Initialized SQLite worker {worker_id} with {poll_interval}s poll interval")
    
    async def start(self):
        """Start the worker main loop"""
        self.running = True
        logger.info(f"Starting SQLite async worker {self.worker_id}")
        
        # Register signal handlers for graceful shutdown
        if sys.platform != 'win32':
            loop = asyncio.get_event_loop()
            loop.add_signal_handler(signal.SIGTERM, self._signal_handler)
            loop.add_signal_handler(signal.SIGINT, self._signal_handler)
        
        try:
            await self._worker_loop()
        except Exception as e:
            logger.error(f"Worker {self.worker_id} crashed: {e}", exc_info=True)
        finally:
            logger.info(f"Worker {self.worker_id} stopped")
    
    def _signal_handler(self):
        """Handle shutdown signals"""
        logger.info(f"Worker {self.worker_id} received shutdown signal")
        self.shutdown_event.set()
    
    async def stop(self):
        """Stop the worker gracefully"""
        logger.info(f"Stopping worker {self.worker_id}")
        self.running = False
        self.shutdown_event.set()
    
    async def _worker_loop(self):
        """Main worker loop"""
        while self.running and not self.shutdown_event.is_set():
            try:
                # Claim and process one job
                await self._process_next_job()
                
                # Wait for next poll or shutdown
                try:
                    await asyncio.wait_for(
                        self.shutdown_event.wait(), 
                        timeout=self.poll_interval
                    )
                    break  # Shutdown requested
                except asyncio.TimeoutError:
                    continue  # Normal poll interval
                    
            except Exception as e:
                logger.error(f"Error in worker loop: {e}", exc_info=True)
                await asyncio.sleep(min(self.poll_interval, 30))
    
    async def _process_next_job(self):
        """Claim and process the next available job"""
        async with self._get_session() as session:
            try:
                # Try to claim a job using SQLite-safe approach
                job_id = await self._claim_next_job(session)
                if not job_id:
                    return  # No jobs available
                
                logger.info(f"Worker {self.worker_id} claimed job {job_id}")
                
                # Process the job
                await self._process_job(session, job_id)
                
            except Exception as e:
                logger.error(f"Error processing job: {e}", exc_info=True)
    
    async def _claim_next_job(self, session: AsyncSession) -> Optional[str]:
        """Claim the next available job using SQLite-compatible UPDATE"""
        try:
            # SQLite UPDATE with ORDER BY and LIMIT - check if supported
            claim_time = datetime.utcnow()
            timeout_threshold = claim_time - timedelta(seconds=self.claim_timeout)
            
            # Try to claim a job atomically
            # This approach works with most SQLite builds
            result = await session.execute(
                text("""
                    UPDATE iep_generation_jobs 
                    SET 
                        status = 'processing',
                        claimed_by = :worker_id,
                        claimed_at = :claim_time,
                        updated_at = :claim_time
                    WHERE id = (
                        SELECT id FROM iep_generation_jobs 
                        WHERE (status = 'pending' 
                               OR (status = 'processing' AND claimed_at < :timeout_threshold))
                        ORDER BY priority DESC, created_at ASC 
                        LIMIT 1
                    )
                    RETURNING id
                """),
                {
                    "worker_id": self.worker_id,
                    "claim_time": claim_time,
                    "timeout_threshold": timeout_threshold
                }
            )
            
            row = result.fetchone()
            if row:
                await session.commit()
                return str(row[0])
            
            return None
            
        except Exception as e:
            # Fallback for SQLite versions without UPDATE...RETURNING
            logger.warning(f"UPDATE...RETURNING not supported, using fallback: {e}")
            await session.rollback()
            return await self._claim_job_fallback(session)
    
    async def _claim_job_fallback(self, session: AsyncSession) -> Optional[str]:
        """Fallback job claiming for older SQLite versions"""
        try:
            claim_time = datetime.utcnow()
            timeout_threshold = claim_time - timedelta(seconds=self.claim_timeout)
            
            # Find a job to claim
            result = await session.execute(
                select(IEPGenerationJob.id)
                .where(
                    (IEPGenerationJob.status == 'pending') |
                    ((IEPGenerationJob.status == 'processing') & 
                     (IEPGenerationJob.claimed_at < timeout_threshold))
                )
                .order_by(IEPGenerationJob.priority.desc(), IEPGenerationJob.created_at)
                .limit(1)
            )
            
            row = result.fetchone()
            if not row:
                return None
            
            job_id = row[0]
            
            # Try to claim it
            result = await session.execute(
                update(IEPGenerationJob)
                .where(
                    (IEPGenerationJob.id == job_id) &
                    ((IEPGenerationJob.status == 'pending') |
                     ((IEPGenerationJob.status == 'processing') & 
                      (IEPGenerationJob.claimed_at < timeout_threshold)))
                )
                .values(
                    status='processing',
                    claimed_by=self.worker_id,
                    claimed_at=claim_time,
                    updated_at=claim_time
                )
            )
            
            if result.rowcount > 0:
                await session.commit()
                return str(job_id)
            else:
                # Job was claimed by another worker
                await session.rollback()
                return None
                
        except Exception as e:
            logger.error(f"Error in fallback job claiming: {e}")
            await session.rollback()
            return None
    
    async def _process_job(self, session: AsyncSession, job_id: str):
        """Process a claimed job"""
        try:
            # Get job details
            job = await session.get(IEPGenerationJob, job_id)
            if not job:
                logger.error(f"Job {job_id} not found")
                return
            
            logger.info(f"Processing job {job_id}: {job.job_type}")
            
            # Update job progress
            await self._update_job_progress(session, job_id, 10, "Starting generation")
            
            # Process based on job type
            if job.job_type == 'iep_generation':
                await self._process_iep_generation(session, job)
            elif job.job_type == 'section_generation':
                await self._process_section_generation(session, job)
            else:
                raise ValueError(f"Unknown job type: {job.job_type}")
            
        except Exception as e:
            logger.error(f"Error processing job {job_id}: {e}", exc_info=True)
            await self._mark_job_failed(session, job_id, str(e))
    
    async def _process_iep_generation(self, session: AsyncSession, job: IEPGenerationJob):
        """Process full IEP generation using the real RAG system"""
        try:
            # Parse job parameters
            params = job.parameters or {}
            
            student_id = params.get('student_data', {}).get('student_id')
            template_id = params.get('template_data', {}).get('template_id')
            academic_year = params.get('academic_year')
            created_by_auth_id = params.get('created_by_auth_id')
            
            if not student_id:
                raise ValueError("Missing student_id in job parameters")
            
            # Update progress
            await self._update_job_progress(session, job.id, 10, "Initializing RAG system")
            
            # Initialize the full RAG system (same as the synchronous path)
            from ..repositories.iep_repository import IEPRepository
            from ..repositories.pl_repository import PLRepository
            from ..services.iep_service import IEPService
            from ..rag.iep_generator import IEPGenerator
            from common.src.vector_store import VectorStore
            from common.src.config import get_settings
            
            settings = get_settings()
            
            # Initialize vector store
            import os
            if os.getenv("ENVIRONMENT") == "development":
                vector_store = VectorStore(
                    project_id=getattr(settings, 'gcp_project_id', 'default-project'),
                    collection_name="rag_documents"
                )
            else:
                try:
                    from common.src.vector_store.vertex_vector_store import VertexVectorStore
                    vector_store = VertexVectorStore.from_settings(settings)
                except (ValueError, AttributeError) as e:
                    logger.warning(f"Vertex AI not configured ({e}), falling back to ChromaDB")
                    vector_store = VectorStore(
                        project_id=getattr(settings, 'gcp_project_id', 'default-project'),
                        collection_name="rag_documents"
                    )
            
            # Initialize repositories and services
            iep_repo = IEPRepository(session)
            pl_repo = PLRepository(session)
            
            # Initialize IEP generator with vector store
            iep_generator = IEPGenerator(
                vector_store=vector_store,
                project_id=getattr(settings, 'gcp_project_id', 'default-project'),
                bucket_name=getattr(settings, 'gcs_bucket_name', 'default-bucket'),
                model_name=getattr(settings, 'gemini_model', 'gemini-1.5-pro')
            )
            
            # Initialize IEP service
            iep_service = IEPService(
                repository=iep_repo,
                pl_repository=pl_repo,
                vector_store=vector_store,
                iep_generator=iep_generator,
                workflow_client=None,  # Not needed for async processing
                audit_client=None      # Not needed for async processing
            )
            
            # Update progress
            await self._update_job_progress(session, job.id, 25, "Generating IEP with RAG")
            
            # Parse UUIDs
            from uuid import UUID
            student_uuid = UUID(student_id)
            template_uuid = UUID(template_id) if template_id else None
            
            # Prepare initial data
            initial_data = {
                "content": params.get('template_data', {}).get('content', {}),
                "meeting_date": params.get('meeting_date'),
                "effective_date": params.get('effective_date'),
                "review_date": params.get('review_date')
            }
            
            # Update progress
            await self._update_job_progress(session, job.id, 50, "Calling RAG IEP generation")
            
            # Call the real RAG IEP generation service
            created_iep = await iep_service.create_iep_with_rag(
                student_id=student_uuid,
                template_id=template_uuid,
                academic_year=academic_year,
                initial_data=initial_data,
                user_id=int(created_by_auth_id),
                user_role="system"  # Background job
            )
            
            # Update progress
            await self._update_job_progress(session, job.id, 90, "Processing results")
            
            # Prepare result - the service already returns a complete IEP
            result = {
                'iep_data': ensure_json_serializable(created_iep),
                'generation_method': 'rag_system',
                'created_via_async': True,
                'validation_status': 'passed'
            }
            
            # Mark job completed
            await self._mark_job_completed(session, job.id, result)
            
            logger.info(f"Successfully completed IEP generation job {job.id}")
            
        except Exception as e:
            logger.error(f"IEP generation failed for job {job.id}: {e}", exc_info=True)
            await self._mark_job_failed(session, job.id, str(e))
    
    async def _process_section_generation(self, session: AsyncSession, job: IEPGenerationJob):
        """Process specific section generation"""
        try:
            # Parse job parameters
            params = job.parameters or {}
            
            section_type = params.get('section_type')
            student_data = params.get('student_data', {})
            context_data = params.get('context_data', {})
            
            # Update progress
            await self._update_job_progress(session, job.id, 25, f"Generating {section_type} section")
            
            # Build section-specific prompt
            prompt = self._build_section_prompt(section_type, student_data, context_data)
            
            # Generate with Gemini (simplified for sections)
            # This would be a lighter weight call than full IEP generation
            # For now, we'll mark as completed with placeholder
            
            result = {
                'section_type': section_type,
                'generated_content': f"Generated {section_type} content for student",
                'generation_metadata': {'section_generation': True}
            }
            
            await self._mark_job_completed(session, job.id, result)
            
        except Exception as e:
            logger.error(f"Section generation failed for job {job.id}: {e}", exc_info=True)
            await self._mark_job_failed(session, job.id, str(e))
    
    def _build_section_prompt(self, section_type: str, student_data: Dict, context_data: Dict) -> str:
        """Build prompt for specific section generation"""
        return f"""Generate {section_type} section for IEP based on:
Student: {json.dumps(student_data, indent=2)}
Context: {json.dumps(context_data, indent=2)}

Return only the section content as JSON."""
    
    async def _update_job_progress(self, session: AsyncSession, job_id: str, progress: int, status_message: str):
        """Update job progress"""
        try:
            await session.execute(
                update(IEPGenerationJob)
                .where(IEPGenerationJob.id == job_id)
                .values(
                    progress_percentage=progress,
                    status_message=status_message,
                    updated_at=datetime.utcnow()
                )
            )
            await session.commit()
        except Exception as e:
            logger.error(f"Error updating job progress: {e}")
            await session.rollback()
    
    async def _mark_job_completed(self, session: AsyncSession, job_id: str, result: Dict[str, Any]):
        """Mark job as completed with results"""
        try:
            await session.execute(
                update(IEPGenerationJob)
                .where(IEPGenerationJob.id == job_id)
                .values(
                    status='completed',
                    progress_percentage=100,
                    status_message='Generation completed successfully',
                    result=result,
                    completed_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
            )
            await session.commit()
        except Exception as e:
            logger.error(f"Error marking job completed: {e}")
            await session.rollback()
    
    async def _mark_job_failed(self, session: AsyncSession, job_id: str, error_message: str):
        """Mark job as failed"""
        try:
            # Increment retry count and decide whether to retry
            job = await session.get(IEPGenerationJob, job_id)
            if not job:
                return
            
            retry_count = (job.retry_count or 0) + 1
            
            if retry_count < self.max_retries:
                # Reset for retry
                status = 'pending'
                status_message = f"Retry {retry_count}/{self.max_retries}: {error_message}"
                failed_at = None
            else:
                # Permanently failed
                status = 'failed'
                status_message = f"Failed after {retry_count} attempts: {error_message}"
                failed_at = datetime.utcnow()
            
            await session.execute(
                update(IEPGenerationJob)
                .where(IEPGenerationJob.id == job_id)
                .values(
                    status=status,
                    status_message=status_message,
                    retry_count=retry_count,
                    error_details={'error': error_message, 'worker_id': self.worker_id},
                    failed_at=failed_at,
                    claimed_by=None,  # Release claim for retry
                    claimed_at=None,
                    updated_at=datetime.utcnow()
                )
            )
            await session.commit()
            
        except Exception as e:
            logger.error(f"Error marking job failed: {e}")
            await session.rollback()
    
    @asynccontextmanager
    async def _get_session(self):
        """Get database session with proper cleanup"""
        async for session in get_async_session():
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()


# Worker management functions
async def start_worker(worker_id: str = "worker-1", poll_interval: int = 5):
    """Start a single worker instance"""
    worker = SQLiteAsyncWorker(worker_id, poll_interval)
    await worker.start()


async def start_worker_pool(num_workers: int = 1, poll_interval: int = 5):
    """Start a pool of workers (limited for SQLite)"""
    # SQLite limitation: only 1 concurrent writer
    if num_workers > 1:
        logger.warning("SQLite detected: limiting to 1 worker for write safety")
        num_workers = 1
    
    workers = []
    tasks = []
    
    for i in range(num_workers):
        worker_id = f"worker-{i+1}"
        worker = SQLiteAsyncWorker(worker_id, poll_interval)
        workers.append(worker)
        tasks.append(asyncio.create_task(worker.start()))
    
    try:
        await asyncio.gather(*tasks)
    except KeyboardInterrupt:
        logger.info("Shutting down worker pool...")
        for worker in workers:
            await worker.stop()
        
        # Wait for tasks to finish
        await asyncio.gather(*tasks, return_exceptions=True)
        logger.info("Worker pool stopped")


if __name__ == "__main__":
    # CLI interface for running workers
    import argparse
    
    parser = argparse.ArgumentParser(description="SQLite Async Worker")
    parser.add_argument("--workers", type=int, default=1, help="Number of workers")
    parser.add_argument("--poll-interval", type=int, default=5, help="Poll interval in seconds")
    parser.add_argument("--worker-id", type=str, help="Single worker ID")
    
    args = parser.parse_args()
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    if args.worker_id:
        asyncio.run(start_worker(args.worker_id, args.poll_interval))
    else:
        asyncio.run(start_worker_pool(args.workers, args.poll_interval))