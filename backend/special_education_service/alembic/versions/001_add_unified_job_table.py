"""Add unified job table for IEP generation

Revision ID: 001
Revises: 
Create Date: 2025-06-29 04:01:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Create unified job/queue table
    op.create_table(
        'iep_generation_jobs',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('student_id', sa.String(36), nullable=False),
        sa.Column('academic_year', sa.String(10), nullable=False),
        sa.Column('template_id', sa.String(36), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='PENDING'),
        sa.Column('queue_status', sa.String(20), nullable=False, server_default='PENDING'),
        sa.Column('priority', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('claimed_at', sa.DateTime(), nullable=True),
        sa.Column('claim_worker_id', sa.String(50), nullable=True),
        sa.Column('input_data', sa.Text(), nullable=False),
        sa.Column('result_id', sa.String(36), nullable=True),
        sa.Column('gemini_request_id', sa.String(100), nullable=True),
        sa.Column('gemini_response_raw', sa.Text(), nullable=True),
        sa.Column('gemini_response_compressed', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('gemini_tokens_used', sa.Integer(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('next_retry_at', sa.DateTime(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('error_details', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('failed_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.String(36), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes optimized for SQLite
    op.create_index('idx_job_identity', 'iep_generation_jobs', 
                    ['student_id', 'academic_year', 'template_id'])
    op.create_index('idx_queue_claim', 'iep_generation_jobs', 
                    ['queue_status', 'next_retry_at', 'claimed_at'])
    op.create_index('idx_queue_priority', 'iep_generation_jobs', 
                    ['priority', 'created_at'])
    op.create_index('idx_job_status', 'iep_generation_jobs', 
                    ['status', 'created_at'])

def downgrade():
    op.drop_table('iep_generation_jobs')