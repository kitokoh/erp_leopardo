"""Initial migration

Revision ID: a6de7289bbd6
Revises:
Create Date: 2025-08-18 10:35:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a6de7289bbd6'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Auth Tables
    op.create_table('permissions',
        sa.Column('permission_key', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('permission_key')
    )
    op.create_table('roles',
        sa.Column('role_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('role_name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.PrimaryKeyConstraint('role_id'),
        sa.UniqueConstraint('role_name')
    )
    op.create_table('users',
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('username', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('full_name', sa.String(), nullable=True),
        sa.Column('role_id', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('1'), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), server_default=sa.text('0'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_fingerprint_auth_enabled', sa.Boolean(), server_default=sa.text('0'), nullable=True),
        sa.Column('fingerprint_template_id', sa.Text(), nullable=True),
        sa.Column('is_face_auth_enabled', sa.Boolean(), server_default=sa.text('0'), nullable=True),
        sa.Column('face_template_id', sa.Text(), nullable=True),
        sa.Column('is_voice_auth_enabled', sa.Boolean(), server_default=sa.text('0'), nullable=True),
        sa.Column('voice_profile_id', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['role_id'], ['roles.role_id'], ),
        sa.PrimaryKeyConstraint('user_id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('username')
    )
    op.create_table('role_permissions',
        sa.Column('role_id', sa.Integer(), nullable=False),
        sa.Column('permission_key', sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(['permission_key'], ['permissions.permission_key'], ),
        sa.ForeignKeyConstraint(['role_id'], ['roles.role_id'], ),
        sa.PrimaryKeyConstraint('role_id', 'permission_key')
    )

    # Location Tables
    op.create_table('countries',
        sa.Column('country_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('country_name', sa.String(), nullable=False),
        sa.Column('iso_a2_code', sa.String(length=2), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)')),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('(CURRENT_TIMESTAMP)')),
        sa.PrimaryKeyConstraint('country_id'),
        sa.UniqueConstraint('country_name')
    )
    op.create_table('cities',
        sa.Column('city_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('country_id', sa.Integer(), nullable=False),
        sa.Column('city_name', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)')),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('(CURRENT_TIMESTAMP)')),
        sa.ForeignKeyConstraint(['country_id'], ['countries.country_id'], ),
        sa.PrimaryKeyConstraint('city_id')
    )
    op.create_table('item_locations',
        sa.Column('location_id', sa.Text(), nullable=False),
        sa.Column('location_name', sa.Text(), nullable=True),
        sa.Column('location_type', sa.Text(), nullable=True),
        sa.Column('parent_location_id', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('location_id')
    )
    op.create_table('item_storage_locations',
        sa.Column('item_storage_location_id', sa.Text(), nullable=False),
        sa.Column('item_id', sa.Text(), nullable=True),
        sa.Column('location_id', sa.Text(), nullable=True),
        sa.Column('quantity_at_location', sa.REAL(), nullable=True),
        sa.Column('last_updated', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('item_storage_location_id')
    )

    # Client Tables
    op.create_table('clients',
        sa.Column('client_id', sa.String(), nullable=False),
        sa.Column('client_name', sa.String(), nullable=False),
        sa.Column('company_name', sa.String(), nullable=True),
        sa.Column('primary_need_description', sa.Text(), nullable=True),
        sa.Column('project_identifier', sa.String(), nullable=True),
        sa.Column('country_id', sa.Integer(), nullable=True),
        sa.Column('city_id', sa.Integer(), nullable=True),
        sa.Column('default_base_folder_path', sa.String(), nullable=True),
        sa.Column('status_id', sa.Integer(), nullable=True),
        sa.Column('selected_languages', sa.String(), nullable=True),
        sa.Column('price', sa.Float(), server_default='0', nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('category', sa.String(), nullable=True),
        sa.Column('distributor_specific_info', sa.Text(), nullable=True),
        sa.Column('default_template_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), onupdate=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('created_by_user_id', sa.String(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), server_default=sa.text('0'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('lead_source', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['city_id'], ['cities.city_id'], ),
        sa.ForeignKeyConstraint(['country_id'], ['countries.country_id'], ),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.user_id'], ),
        sa.PrimaryKeyConstraint('client_id'),
        sa.UniqueConstraint('default_base_folder_path')
    )
    op.create_table('client_notes',
        sa.Column('note_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('client_id', sa.Text(), nullable=False),
        sa.Column('user_id', sa.Text(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.Column('note_text', sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(['client_id'], ['clients.client_id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ),
        sa.PrimaryKeyConstraint('note_id')
    )
    op.create_table('client_visits',
        sa.Column('visit_id', sa.Text(), nullable=False),
        sa.Column('client_id', sa.Text(), nullable=False),
        sa.Column('visit_date', sa.Text(), nullable=False),
        sa.Column('visit_type', sa.Text(), nullable=True),
        sa.Column('visit_purpose', sa.Text(), nullable=True),
        sa.Column('notes_impressions', sa.Text(), nullable=True),
        sa.Column('created_by_user_id', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['client_id'], ['clients.client_id'], ),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.user_id'], ),
        sa.PrimaryKeyConstraint('visit_id')
    )
    op.create_table('client_document_notes',
        sa.Column('note_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('client_id', sa.String(), nullable=False),
        sa.Column('document_type', sa.Text(), nullable=False),
        sa.Column('note_content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['client_id'], ['clients.client_id'], ),
        sa.PrimaryKeyConstraint('note_id')
    )
    op.create_table('client_contacts',
        sa.Column('client_contact_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('client_id', sa.Text(), nullable=False),
        sa.Column('contact_id', sa.Integer(), nullable=False),
        sa.Column('is_primary_for_client', sa.Boolean(), nullable=True),
        sa.Column('can_receive_documents', sa.Boolean(), nullable=True),
        sa.Column('added_by_user_id', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['added_by_user_id'], ['users.user_id'], ),
        sa.ForeignKeyConstraint(['client_id'], ['clients.client_id'], ),
        sa.PrimaryKeyConstraint('client_contact_id')
    )

    # Document Tables
    op.create_table('document_categories',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_table('document_types',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_table('business_selected_documents',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('business_profile_id', sa.Integer(), nullable=False),
        sa.Column('document_type_id', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table('default_document_notes',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('document_type', sa.Text(), nullable=False),
        sa.Column('language_code', sa.Text(), nullable=False),
        sa.Column('note_content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table('partner_documents',
        sa.Column('document_id', sa.Text(), nullable=False),
        sa.Column('file_path_relative', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('document_id')
    )
    op.create_table('employees',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('first_name', sa.String(), nullable=False),
        sa.Column('last_name', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('phone_number', sa.String(), nullable=True),
        sa.Column('position', sa.String(), nullable=True),
        sa.Column('department', sa.String(), nullable=True),
        sa.Column('salary', sa.Float(), nullable=True),
        sa.Column('start_date', sa.DateTime(), nullable=False),
        sa.Column('end_date', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), onupdate=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    op.create_table('client_documents',
        sa.Column('document_id', sa.String(), nullable=False),
        sa.Column('client_id', sa.String(), nullable=True),
        sa.Column('project_id', sa.String(), nullable=True),
        sa.Column('order_identifier', sa.String(), nullable=True),
        sa.Column('document_name', sa.String(), nullable=True),
        sa.Column('file_name_on_disk', sa.String(), nullable=True),
        sa.Column('file_path_relative', sa.String(), nullable=True),
        sa.Column('document_type_generated', sa.String(), nullable=True),
        sa.Column('source_template_id', sa.Integer(), nullable=True),
        sa.Column('version_tag', sa.String(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('footer_notes', sa.Text(), nullable=True),
        sa.Column('created_by_user_id', sa.String(), nullable=True),
        sa.Column('parent_document_id', sa.String(), nullable=True),
        sa.Column('is_latest_version', sa.Boolean(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)')),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('(CURRENT_TIMESTAMP)')),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['client_id'], ['clients.client_id'], ),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.user_id'], ),
        sa.ForeignKeyConstraint(['parent_document_id'], ['client_documents.document_id'], ),
        sa.PrimaryKeyConstraint('document_id')
    )
    op.create_table('employee_documents',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('employee_id', sa.String(), nullable=True),
        sa.Column('document_category_id', sa.Integer(), nullable=True),
        sa.Column('file_name', sa.String(), nullable=True),
        sa.Column('file_path_or_key', sa.String(), nullable=True),
        sa.Column('file_type', sa.String(), nullable=True),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('uploaded_at', sa.DateTime(), nullable=True),
        sa.Column('uploaded_by_id', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['employee_id'], ['employees.id'], ),
        sa.ForeignKeyConstraint(['document_category_id'], ['document_categories.id'], ),
        sa.ForeignKeyConstraint(['uploaded_by_id'], ['users.user_id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Leave Tables
    op.create_table('leave_types',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('default_days_entitled', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_table('leave_balances',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('employee_id', sa.String(), nullable=False),
        sa.Column('leave_type_id', sa.Integer(), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('entitled_days', sa.Float(), nullable=False),
        sa.Column('used_days', sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(['employee_id'], ['employees.id'], ),
        sa.ForeignKeyConstraint(['leave_type_id'], ['leave_types.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('employee_id', 'leave_type_id', 'year', name='uq_employee_leave_year')
    )
    op.create_table('leave_requests',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('employee_id', sa.String(), nullable=False),
        sa.Column('leave_type_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'APPROVED', 'REJECTED', 'CANCELLED', name='leaverequeststatusenum'), nullable=False),
        sa.Column('start_date', sa.DateTime(), nullable=False),
        sa.Column('end_date', sa.DateTime(), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('num_days', sa.Float(), nullable=False),
        sa.Column('request_date', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('approved_by_id', sa.String(), nullable=True),
        sa.Column('processed_date', sa.DateTime(), nullable=True),
        sa.Column('comments', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['approved_by_id'], ['users.user_id'], ),
        sa.ForeignKeyConstraint(['employee_id'], ['employees.id'], ),
        sa.ForeignKeyConstraint(['leave_type_id'], ['leave_types.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Misc Tables
    op.create_table('activity_log',
        sa.Column('log_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.String(), nullable=True),
        sa.Column('action_type', sa.String(), nullable=True),
        sa.Column('details', sa.Text(), nullable=True),
        sa.Column('related_entity_type', sa.String(), nullable=True),
        sa.Column('related_entity_id', sa.String(), nullable=True),
        sa.Column('related_client_id', sa.String(), nullable=True),
        sa.Column('ip_address', sa.String(), nullable=True),
        sa.Column('user_agent', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['related_client_id'], ['clients.client_id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ),
        sa.PrimaryKeyConstraint('log_id')
    )
    op.create_table('company_assets',
        sa.Column('asset_id', sa.String(), nullable=False),
        sa.Column('asset_name', sa.String(), nullable=True),
        sa.Column('asset_type', sa.String(), nullable=True),
        sa.Column('serial_number', sa.String(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('purchase_date', sa.Date(), nullable=True),
        sa.Column('purchase_value', sa.REAL(), nullable=True),
        sa.Column('current_status', sa.String(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('asset_id')
    )
    op.create_table('companies',
        sa.Column('company_id', sa.String(), nullable=False),
        sa.Column('company_name', sa.String(), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('payment_info', sa.Text(), nullable=True),
        sa.Column('logo_path', sa.String(), nullable=True),
        sa.Column('other_info', sa.Text(), nullable=True),
        sa.Column('is_default', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('company_id')
    )
    op.create_table('company_personnel',
        sa.Column('personnel_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('company_id', sa.Text(), nullable=False),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('role', sa.String(), nullable=True),
        sa.Column('phone', sa.String(), nullable=True),
        sa.Column('email', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.company_id'], ),
        sa.PrimaryKeyConstraint('personnel_id')
    )
    op.create_table('asset_assignments',
        sa.Column('assignment_id', sa.String(), nullable=False),
        sa.Column('asset_id', sa.Text(), nullable=False),
        sa.Column('personnel_id', sa.Integer(), nullable=False),
        sa.Column('assignment_date', sa.DateTime(), nullable=True),
        sa.Column('expected_return_date', sa.DateTime(), nullable=True),
        sa.Column('actual_return_date', sa.DateTime(), nullable=True),
        sa.Column('assignment_status', sa.String(), nullable=True),
        sa.Column('notes', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['asset_id'], ['company_assets.asset_id'], ),
        sa.ForeignKeyConstraint(['personnel_id'], ['company_personnel.personnel_id'], ),
        sa.PrimaryKeyConstraint('assignment_id')
    )
    op.create_table('media_items',
        sa.Column('media_item_id', sa.Text(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('item_type', sa.String(length=50), nullable=True),
        sa.Column('tags', sa.JSON(), nullable=True),
        sa.Column('thumbnail_path', sa.String(), nullable=True),
        sa.Column('media_metadata', sa.JSON(), nullable=True),
        sa.Column('filepath', sa.String(), nullable=True),
        sa.Column('url', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)')),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('(CURRENT_TIMESTAMP)')),
        sa.PrimaryKeyConstraint('media_item_id')
    )
    op.create_table('asset_media_links',
        sa.Column('link_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('asset_id', sa.Text(), nullable=False),
        sa.Column('media_item_id', sa.Text(), nullable=False),
        sa.Column('display_order', sa.Integer(), nullable=True),
        sa.Column('alt_text', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['asset_id'], ['company_assets.asset_id'], ),
        sa.ForeignKeyConstraint(['media_item_id'], ['media_items.media_item_id'], ),
        sa.PrimaryKeyConstraint('link_id')
    )

    # Settings Tables
    op.create_table('application_settings',
    sa.Column('setting_key', sa.Text(), nullable=False),
    sa.Column('setting_value', sa.Text(), nullable=True),
    sa.PrimaryKeyConstraint('setting_key')
    )

def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('asset_media_links')
    op.drop_table('media_items')
    op.drop_table('asset_assignments')
    op.drop_table('company_personnel')
    op.drop_table('companies')
    op.drop_table('company_assets')
    op.drop_table('activity_log')
    op.drop_table('leave_requests')
    op.drop_table('leave_balances')
    op.drop_table('leave_types')
    op.drop_table('employee_documents')
    op.drop_table('employees')
    op.drop_table('client_documents')
    op.drop_table('partner_documents')
    op.drop_table('default_document_notes')
    op.drop_table('business_selected_documents')
    op.drop_table('document_types')
    op.drop_table('document_categories')
    op.drop_table('client_contacts')
    op.drop_table('client_document_notes')
    op.drop_table('client_visits')
    op.drop_table('client_notes')
    op.drop_table('clients')
    op.drop_table('item_storage_locations')
    op.drop_table('item_locations')
    op.drop_table('cities')
    op.drop_table('countries')
    op.drop_table('role_permissions')
    op.drop_table('users')
    op.drop_table('roles')
    op.drop_table('permissions')
    op.drop_table('application_settings')
