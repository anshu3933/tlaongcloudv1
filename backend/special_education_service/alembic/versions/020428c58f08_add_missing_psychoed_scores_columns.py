"""Add missing psychoed_scores columns

Revision ID: 020428c58f08
Revises: 001
Create Date: 2025-07-13 16:32:06.129798

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '020428c58f08'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add missing columns to psychoed_scores table to match SQLAlchemy models"""
    
    # Add missing columns that the models expect but database doesn't have
    op.add_column('psychoed_scores', sa.Column('score_type', sa.String(50), nullable=True))
    op.add_column('psychoed_scores', sa.Column('confidence_interval_lower', sa.Integer(), nullable=True))
    op.add_column('psychoed_scores', sa.Column('confidence_interval_upper', sa.Integer(), nullable=True))
    op.add_column('psychoed_scores', sa.Column('normative_sample', sa.String(100), nullable=True))
    op.add_column('psychoed_scores', sa.Column('test_date', sa.DateTime(timezone=True), nullable=True))
    op.add_column('psychoed_scores', sa.Column('basal_score', sa.Integer(), nullable=True))
    op.add_column('psychoed_scores', sa.Column('ceiling_score', sa.Integer(), nullable=True))
    
    # Migrate existing data where possible
    # Set score_type based on which score fields have values
    op.execute("""
        UPDATE psychoed_scores 
        SET score_type = CASE 
            WHEN standard_score IS NOT NULL THEN 'standard_score'
            WHEN scaled_score IS NOT NULL THEN 'scaled_score'
            WHEN t_score IS NOT NULL THEN 't_score'
            WHEN percentile_rank IS NOT NULL THEN 'percentile_rank'
            WHEN raw_score IS NOT NULL THEN 'raw_score'
            ELSE 'unknown'
        END
        WHERE score_type IS NULL
    """)
    
    # Try to split confidence_interval text field into lower/upper if it exists and has format "X-Y"
    op.execute("""
        UPDATE psychoed_scores 
        SET 
            confidence_interval_lower = CAST(SUBSTR(confidence_interval, 1, INSTR(confidence_interval, '-') - 1) AS INTEGER),
            confidence_interval_upper = CAST(SUBSTR(confidence_interval, INSTR(confidence_interval, '-') + 1) AS INTEGER)
        WHERE confidence_interval IS NOT NULL 
          AND confidence_interval LIKE '%-%'
          AND LENGTH(confidence_interval) < 10
          AND confidence_interval_lower IS NULL
    """)


def downgrade() -> None:
    """Remove the added columns"""
    op.drop_column('psychoed_scores', 'ceiling_score')
    op.drop_column('psychoed_scores', 'basal_score')
    op.drop_column('psychoed_scores', 'test_date')
    op.drop_column('psychoed_scores', 'normative_sample')
    op.drop_column('psychoed_scores', 'confidence_interval_upper')
    op.drop_column('psychoed_scores', 'confidence_interval_lower')
    op.drop_column('psychoed_scores', 'score_type')