"""mudanca na estrutura dos dados, agora um projeto pode tre multiplos clientes

Revision ID: b9104f3e0b25
Revises: 0a802b9e7e19
Create Date: 2025-08-25 14:15:21.051729

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b9104f3e0b25'
down_revision: Union[str, Sequence[str], None] = '0a802b9e7e19'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Criar tabela de associação
    op.create_table(
        'projeto_cliente',
        sa.Column('projeto_id', sa.Integer(), sa.ForeignKey('projetos.id'), primary_key=True),
        sa.Column('cliente_id', sa.Integer(), sa.ForeignKey('clientes.id'), primary_key=True)
    )

    # Copiar os dados existentes da coluna id_cliente para a nova tabela
    connection = op.get_bind()
    results = connection.execute("SELECT id, id_cliente FROM projetos WHERE id_cliente IS NOT NULL")
    for projeto_id, cliente_id in results:
        connection.execute(
            "INSERT INTO projeto_cliente (projeto_id, cliente_id) VALUES (%s, %s)",
            projeto_id, cliente_id
        )

    # Remover a coluna id_cliente da tabela projetos
    op.drop_column('projetos', 'id_cliente')

def downgrade():
    # Adicionar a coluna id_cliente de volta
    op.add_column('projetos', sa.Column('id_cliente', sa.Integer(), sa.ForeignKey('clientes.id')))

    # Copiar os dados de volta (apenas o primeiro cliente de cada projeto)
    connection = op.get_bind()
    results = connection.execute("SELECT projeto_id, cliente_id FROM projeto_cliente")
    for projeto_id, cliente_id in results:
        connection.execute(
            "UPDATE projetos SET id_cliente = %s WHERE id = %s",
            cliente_id, projeto_id
        )

    # Remover a tabela de associação
    op.drop_table('projeto_cliente')
