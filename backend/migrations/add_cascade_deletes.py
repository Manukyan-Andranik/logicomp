"""
Migration script to add cascade delete constraints
This ensures that when a contest is deleted, all related data is also deleted
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision = 'add_cascade_deletes'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Drop existing foreign key constraints and recreate them with CASCADE
    op.drop_constraint('problems_contest_id_fkey', 'problems', type_='foreignkey')
    op.create_foreign_key('problems_contest_id_fkey', 'problems', 'contests', ['contest_id'], ['id'], ondelete='CASCADE')
    
    op.drop_constraint('submissions_contest_id_fkey', 'submissions', type_='foreignkey')
    op.create_foreign_key('submissions_contest_id_fkey', 'submissions', 'contests', ['contest_id'], ['id'], ondelete='CASCADE')
    
    op.drop_constraint('submissions_problem_id_fkey', 'submissions', type_='foreignkey')
    op.create_foreign_key('submissions_problem_id_fkey', 'submissions', 'problems', ['problem_id'], ['id'], ondelete='CASCADE')
    
    op.drop_constraint('submissions_user_id_fkey', 'submissions', type_='foreignkey')
    op.create_foreign_key('submissions_user_id_fkey', 'submissions', 'users', ['user_id'], ['id'], ondelete='CASCADE')
    
    op.drop_constraint('test_cases_problem_id_fkey', 'test_cases', type_='foreignkey')
    op.create_foreign_key('test_cases_problem_id_fkey', 'test_cases', 'problems', ['problem_id'], ['id'], ondelete='CASCADE')
    
    # Drop and recreate the contest_participants table with CASCADE constraints
    op.drop_table('contest_participants')
    op.create_table('contest_participants',
        sa.Column('contest_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['contest_id'], ['contests.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('contest_id', 'user_id')
    )
    
    # Add foreign key constraint to participants_history table
    op.create_foreign_key('participants_history_contest_id_fkey', 'participants_history', 'contests', ['contest_id'], ['id'], ondelete='CASCADE')

def downgrade():
    # Revert the changes if needed
    op.drop_constraint('participants_history_contest_id_fkey', 'participants_history', type_='foreignkey')
    
    op.drop_table('contest_participants')
    op.create_table('contest_participants',
        sa.Column('contest_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['contest_id'], ['contests.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('contest_id', 'user_id')
    )
    
    op.drop_constraint('test_cases_problem_id_fkey', 'test_cases', type_='foreignkey')
    op.create_foreign_key('test_cases_problem_id_fkey', 'test_cases', 'problems', ['problem_id'], ['id'])
    
    op.drop_constraint('submissions_user_id_fkey', 'submissions', type_='foreignkey')
    op.create_foreign_key('submissions_user_id_fkey', 'submissions', 'users', ['user_id'], ['id'])
    
    op.drop_constraint('submissions_problem_id_fkey', 'submissions', type_='foreignkey')
    op.create_foreign_key('submissions_problem_id_fkey', 'submissions', 'problems', ['problem_id'], ['id'])
    
    op.drop_constraint('submissions_contest_id_fkey', 'submissions', type_='foreignkey')
    op.create_foreign_key('submissions_contest_id_fkey', 'submissions', 'contests', ['contest_id'], ['id'])
    
    op.drop_constraint('problems_contest_id_fkey', 'problems', type_='foreignkey')
    op.create_foreign_key('problems_contest_id_fkey', 'problems', 'contests', ['contest_id'], ['id'])
