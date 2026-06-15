"""add_emails_adicionais_to_projetos

Revision ID: 1137741db60b
Revises: b9104f3e0b25
Create Date: 2025-08-26 11:41:43.071021

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1137741db60b'
down_revision: Union[str, Sequence[str], None] = 'b9104f3e0b25'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column('projetos', sa.Column('emails_adicionais', sa.String(), nullable=True))

def downgrade():
    op.drop_column('projetos', 'emails_adicionais')
