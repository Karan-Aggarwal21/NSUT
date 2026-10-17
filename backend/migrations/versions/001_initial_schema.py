"""Initial schema for Cognivia platform

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-10-17 13:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. users table
    op.create_table(
        'users',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('username', sa.String(length=150), nullable=False),
        sa.Column('email', sa.String(length=254), nullable=True),
        sa.Column('hashed_password', sa.String(length=512), nullable=False),
        sa.Column('role', sa.Enum('USER', 'CAREGIVER', 'ADMIN', name='user_role'), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    # 2. refresh_tokens table
    op.create_table(
        'refresh_tokens',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('token_hash', sa.String(length=512), nullable=False),
        sa.Column('is_revoked', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token_hash'),
    )
    op.create_index(op.f('ix_refresh_tokens_user_id'), 'refresh_tokens', ['user_id'], unique=False)

    # 3. user_profiles table
    op.create_table(
        'user_profiles',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('display_name', sa.String(length=200), nullable=True),
        sa.Column('age', sa.Integer(), nullable=True),
        sa.Column('gender', sa.String(length=50), nullable=True),
        sa.Column('preferred_language', sa.String(length=50), nullable=True),
        sa.Column('region', sa.String(length=100), nullable=True),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id'),
    )

    # 4. assessment_sessions table
    op.create_table(
        'assessment_sessions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('client_session_id', sa.String(length=255), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('activity_type', sa.String(length=100), nullable=False),
        sa.Column('activity_version', sa.String(length=20), nullable=False),
        sa.Column('difficulty', sa.Integer(), nullable=True),
        sa.Column('status', sa.Enum('STARTED', 'IN_PROGRESS', 'COMPLETED', 'ABANDONED', name='session_status'), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tasks_attempted', sa.Integer(), nullable=True),
        sa.Column('correct_count', sa.Integer(), nullable=True),
        sa.Column('incorrect_count', sa.Integer(), nullable=True),
        sa.Column('duration_seconds', sa.Float(), nullable=True),
        sa.Column('task_response_data', sa.Text(), nullable=True),
        sa.Column('sync_status', sa.String(length=50), nullable=False, server_default='synced'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_assessment_sessions_client_session_id'), 'assessment_sessions', ['client_session_id'], unique=True)
    op.create_index(op.f('ix_assessment_sessions_user_id'), 'assessment_sessions', ['user_id'], unique=False)

    # 5. activity_results table
    op.create_table(
        'activity_results',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('client_result_id', sa.String(length=255), nullable=True),
        sa.Column('session_id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('task_index', sa.Integer(), nullable=True),
        sa.Column('stimulus', sa.Text(), nullable=True),
        sa.Column('user_response', sa.Text(), nullable=True),
        sa.Column('is_correct', sa.Boolean(), nullable=True),
        sa.Column('response_time_ms', sa.Integer(), nullable=True),
        sa.Column('score', sa.Float(), nullable=True),
        sa.Column('metadata_json', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['assessment_sessions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_activity_results_client_result_id'), 'activity_results', ['client_result_id'], unique=True)
    op.create_index(op.f('ix_activity_results_session_id'), 'activity_results', ['session_id'], unique=False)
    op.create_index(op.f('ix_activity_results_user_id'), 'activity_results', ['user_id'], unique=False)

    # 6. personalized_items table
    op.create_table(
        'personalized_items',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('category', sa.Enum('FAMILIAR_PERSON', 'PLACE', 'OBJECT', 'PERSONAL_EVENT', name='item_category'), nullable=False),
        sa.Column('display_name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('image_reference', sa.String(length=500), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_personalized_items_user_id'), 'personalized_items', ['user_id'], unique=False)

    # 7. questionnaires table
    op.create_table(
        'questionnaires',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('slug', sa.String(length=100), nullable=False),
        sa.Column('title', sa.String(length=300), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_questionnaires_slug'), 'questionnaires', ['slug'], unique=True)

    # 8. questionnaire_versions table
    op.create_table(
        'questionnaire_versions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('questionnaire_id', sa.UUID(), nullable=False),
        sa.Column('version_label', sa.String(length=20), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['questionnaire_id'], ['questionnaires.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_questionnaire_versions_questionnaire_id'), 'questionnaire_versions', ['questionnaire_id'], unique=False)

    # 9. questionnaire_questions table
    op.create_table(
        'questionnaire_questions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('version_id', sa.UUID(), nullable=False),
        sa.Column('question_key', sa.String(length=100), nullable=False),
        sa.Column('question_text', sa.Text(), nullable=False),
        sa.Column('order_index', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_required', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('answer_type', sa.String(length=50), nullable=False, server_default='single_choice'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['version_id'], ['questionnaire_versions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_questionnaire_questions_version_id'), 'questionnaire_questions', ['version_id'], unique=False)

    # 10. questionnaire_options table
    op.create_table(
        'questionnaire_options',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('question_id', sa.UUID(), nullable=False),
        sa.Column('option_value', sa.String(length=100), nullable=False),
        sa.Column('option_label', sa.String(length=300), nullable=False),
        sa.Column('order_index', sa.Integer(), nullable=False, server_default='0'),
        sa.ForeignKeyConstraint(['question_id'], ['questionnaire_questions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_questionnaire_options_question_id'), 'questionnaire_options', ['question_id'], unique=False)

    # 11. questionnaire_responses table
    op.create_table(
        'questionnaire_responses',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('client_submission_id', sa.String(length=255), nullable=True),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('questionnaire_id', sa.UUID(), nullable=False),
        sa.Column('version_id', sa.UUID(), nullable=False),
        sa.Column('completion_status', sa.String(length=50), nullable=False, server_default='completed'),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['questionnaire_id'], ['questionnaires.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['version_id'], ['questionnaire_versions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_questionnaire_responses_client_submission_id'), 'questionnaire_responses', ['client_submission_id'], unique=True)
    op.create_index(op.f('ix_questionnaire_responses_user_id'), 'questionnaire_responses', ['user_id'], unique=False)

    # 12. questionnaire_answers table
    op.create_table(
        'questionnaire_answers',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('response_id', sa.UUID(), nullable=False),
        sa.Column('question_id', sa.UUID(), nullable=True),
        sa.Column('question_key', sa.String(length=100), nullable=False),
        sa.Column('answer_value', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['question_id'], ['questionnaire_questions.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['response_id'], ['questionnaire_responses.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_questionnaire_answers_response_id'), 'questionnaire_answers', ['response_id'], unique=False)

    # 13. audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('actor_id', sa.UUID(), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('resource_type', sa.String(length=100), nullable=True),
        sa.Column('resource_id', sa.String(length=255), nullable=True),
        sa.Column('detail', sa.Text(), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['actor_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_audit_logs_action'), 'audit_logs', ['action'], unique=False)
    op.create_index(op.f('ix_audit_logs_actor_id'), 'audit_logs', ['actor_id'], unique=False)
    op.create_index(op.f('ix_audit_logs_created_at'), 'audit_logs', ['created_at'], unique=False)


def downgrade() -> None:
    op.drop_table('audit_logs')
    op.drop_table('questionnaire_answers')
    op.drop_table('questionnaire_responses')
    op.drop_table('questionnaire_options')
    op.drop_table('questionnaire_questions')
    op.drop_table('questionnaire_versions')
    op.drop_table('questionnaires')
    op.drop_table('personalized_items')
    op.drop_table('activity_results')
    op.drop_table('assessment_sessions')
    op.drop_table('user_profiles')
    op.drop_table('refresh_tokens')
    op.drop_table('users')
    op.execute('DROP TYPE IF EXISTS item_category')
    op.execute('DROP TYPE IF EXISTS session_status')
    op.execute('DROP TYPE IF EXISTS user_role')
