"""
Database schema validation and circuit breaker for assessment operations
Prevents future schema drift and provides monitoring
"""
import time
import logging
from typing import Dict, Set, List, Optional, Any
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

logger = logging.getLogger(__name__)

class SchemaValidationError(Exception):
    """Raised when database schema doesn't match expected structure"""
    pass

class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open due to repeated failures"""
    pass

class DatabaseSchemaValidator:
    """Validates database schema matches SQLAlchemy models"""
    
    EXPECTED_SCHEMAS = {
        'psychoed_scores': {
            'id', 'document_id', 'test_name', 'subtest_name', 'score_type',
            'raw_score', 'standard_score', 'percentile_rank', 'scaled_score',
            'confidence_interval_lower', 'confidence_interval_upper',
            'normative_sample', 'test_date', 'basal_score', 'ceiling_score',
            'created_at', 'test_version', 't_score', 'age_equivalent_years',
            'age_equivalent_months', 'grade_equivalent', 'confidence_interval',
            'confidence_level', 'qualitative_descriptor', 'score_classification',
            'extraction_confidence'
        },
        'assessment_documents': {
            'id', 'student_id', 'document_type', 'file_path', 'file_name',
            'gcs_path', 'upload_date', 'processing_status', 'assessment_date',
            'assessor_name', 'assessor_title', 'assessment_location',
            'extraction_confidence', 'processing_duration', 'error_message',
            'created_at', 'updated_at'
        },
        'quantified_assessment_data': {
            'id', 'student_id', 'assessment_date', 'cognitive_composite',
            'academic_composite', 'behavioral_composite', 'social_emotional_composite',
            'adaptive_composite', 'executive_composite', 'reading_composite',
            'math_composite', 'writing_composite', 'language_composite',
            'standardized_plop', 'growth_rate', 'progress_indicators',
            'learning_style_profile', 'cognitive_processing_profile',
            'priority_goals', 'service_recommendations', 'accommodation_recommendations',
            'eligibility_category', 'primary_disability', 'secondary_disabilities',
            'confidence_metrics', 'source_documents', 'created_at', 'updated_at'
        }
    }
    
    def __init__(self, engine: AsyncEngine):
        self.engine = engine
        self.last_validation_time = None
        self.validation_cache_duration = 300  # 5 minutes
        self.validation_results = {}
    
    async def validate_all_schemas(self, force: bool = False) -> Dict[str, Any]:
        """
        Validate all assessment-related table schemas
        
        Args:
            force: Skip cache and force validation
            
        Returns:
            Validation results with status and details
            
        Raises:
            SchemaValidationError: If critical schema mismatches found
        """
        now = time.time()
        
        # Use cached results if recent and not forced
        if (not force and self.last_validation_time and 
            now - self.last_validation_time < self.validation_cache_duration):
            return self.validation_results
        
        logger.info("🔍 Starting database schema validation...")
        
        async with self.engine.begin() as conn:
            validation_results = {
                'status': 'valid',
                'timestamp': now,
                'tables': {},
                'critical_errors': [],
                'warnings': []
            }
            
            for table_name, expected_columns in self.EXPECTED_SCHEMAS.items():
                table_result = await self._validate_table_schema(conn, table_name, expected_columns)
                validation_results['tables'][table_name] = table_result
                
                if table_result['critical_missing']:
                    validation_results['critical_errors'].extend(
                        f"Table {table_name} missing critical columns: {table_result['critical_missing']}"
                    )
                    validation_results['status'] = 'invalid'
                
                if table_result['missing_columns']:
                    validation_results['warnings'].append(
                        f"Table {table_name} missing optional columns: {table_result['missing_columns']}"
                    )
        
        self.validation_results = validation_results
        self.last_validation_time = now
        
        if validation_results['critical_errors']:
            error_msg = "; ".join(validation_results['critical_errors'])
            logger.error(f"❌ Critical schema validation errors: {error_msg}")
            raise SchemaValidationError(
                f"Database schema validation failed: {error_msg}. "
                f"Please run migrations: alembic upgrade head"
            )
        
        if validation_results['warnings']:
            logger.warning(f"⚠️ Schema warnings: {'; '.join(validation_results['warnings'])}")
        
        logger.info("✅ Database schema validation passed")
        return validation_results
    
    async def _validate_table_schema(
        self, 
        conn, 
        table_name: str, 
        expected_columns: Set[str]
    ) -> Dict[str, Any]:
        """Validate a specific table's schema"""
        
        try:
            # Get actual columns from database
            if 'sqlite' in str(conn.dialect.name).lower():
                result = await conn.execute(text(f"PRAGMA table_info({table_name})"))
                actual_columns = {row[1] for row in result}
            else:
                # PostgreSQL
                result = await conn.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = :table_name
                """), {"table_name": table_name})
                actual_columns = {row[0] for row in result}
            
            missing_columns = expected_columns - actual_columns
            extra_columns = actual_columns - expected_columns
            
            # Define critical columns that must exist
            critical_columns = self._get_critical_columns(table_name)
            critical_missing = missing_columns & critical_columns
            
            return {
                'exists': bool(actual_columns),
                'actual_columns': actual_columns,
                'expected_columns': expected_columns,
                'missing_columns': missing_columns,
                'extra_columns': extra_columns,
                'critical_missing': critical_missing,
                'status': 'invalid' if critical_missing else 'valid'
            }
            
        except Exception as e:
            logger.error(f"Error validating table {table_name}: {e}")
            return {
                'exists': False,
                'error': str(e),
                'status': 'error'
            }
    
    def _get_critical_columns(self, table_name: str) -> Set[str]:
        """Get columns that are critical for basic functionality"""
        critical_columns = {
            'psychoed_scores': {
                'id', 'document_id', 'test_name', 'subtest_name', 'score_type'
            },
            'assessment_documents': {
                'id', 'student_id', 'document_type', 'file_name', 'file_path'
            },
            'quantified_assessment_data': {
                'id', 'student_id', 'assessment_date'
            }
        }
        return critical_columns.get(table_name, set())


class AssessmentCircuitBreaker:
    """Circuit breaker for assessment database operations"""
    
    def __init__(self, failure_threshold: int = 5, timeout: int = 300, name: str = "assessment"):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.name = name
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self.last_success_time = time.time()
    
    async def call(self, operation, *args, operation_name: str = "unknown", **kwargs):
        """
        Execute operation through circuit breaker
        
        Args:
            operation: The async function to execute
            *args: Arguments for the operation
            operation_name: Name for logging
            **kwargs: Keyword arguments for the operation
            
        Returns:
            Operation result
            
        Raises:
            CircuitBreakerOpenError: If circuit is open
            Original exception: If operation fails and circuit allows it
        """
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.timeout:
                self.state = "HALF_OPEN"
                logger.info(f"🔄 Circuit breaker {self.name} entering HALF_OPEN state")
            else:
                raise CircuitBreakerOpenError(
                    f"Circuit breaker {self.name} is OPEN. "
                    f"Assessment queries temporarily disabled due to repeated schema errors. "
                    f"Please check database schema and run migrations."
                )
        
        try:
            result = await operation(*args, **kwargs)
            
            # Success - reset failure count if we were in HALF_OPEN
            if self.state == "HALF_OPEN":
                self.state = "CLOSED"
                self.failure_count = 0
                logger.info(f"✅ Circuit breaker {self.name} reset to CLOSED state")
            
            self.last_success_time = time.time()
            return result
            
        except Exception as e:
            self._handle_failure(e, operation_name)
            raise
    
    def _handle_failure(self, exception: Exception, operation_name: str):
        """Handle operation failure and update circuit breaker state"""
        
        # Check if this is a schema-related error
        error_msg = str(exception).lower()
        is_schema_error = any(phrase in error_msg for phrase in [
            "no such column", 
            "column does not exist", 
            "relation does not exist",
            "column not found",
            "table doesn't exist"
        ])
        
        if is_schema_error:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            logger.warning(
                f"⚠️ Schema error in operation '{operation_name}': {exception}. "
                f"Failure count: {self.failure_count}/{self.failure_threshold}"
            )
            
            if self.failure_count >= self.failure_threshold:
                self.state = "OPEN"
                logger.error(
                    f"🚨 Circuit breaker {self.name} OPENED due to repeated schema errors. "
                    f"Assessment operations temporarily disabled."
                )
        else:
            # Non-schema errors don't affect circuit breaker
            logger.debug(f"Non-schema error in '{operation_name}': {exception}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current circuit breaker status"""
        return {
            'name': self.name,
            'state': self.state,
            'failure_count': self.failure_count,
            'failure_threshold': self.failure_threshold,
            'last_failure_time': self.last_failure_time,
            'last_success_time': self.last_success_time,
            'timeout': self.timeout
        }


# Global instances
schema_validator = None
assessment_circuit_breaker = AssessmentCircuitBreaker()

async def initialize_schema_validation(engine: AsyncEngine):
    """Initialize schema validation with database engine"""
    global schema_validator
    schema_validator = DatabaseSchemaValidator(engine)
    
async def validate_startup_schema(engine: AsyncEngine) -> Dict[str, Any]:
    """Validate schema on application startup"""
    await initialize_schema_validation(engine)
    return await schema_validator.validate_all_schemas()

def get_circuit_breaker() -> AssessmentCircuitBreaker:
    """Get the global circuit breaker instance"""
    return assessment_circuit_breaker