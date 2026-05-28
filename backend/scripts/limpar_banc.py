import sys
from sqlalchemy.orm import Session
from backend.database import SessionLocal  # Importando a fábrica de sessões
from models import Produto, Cliente, Projeto, ValidacaoProjeto, HistoricoStatusProjeto

# Mapeia um nome amigável para a classe do modelo
TABELAS_MAP = {
    "clientes": Cliente,
    "produtos": Produto,
    "projetos": Projeto,
    "validacoes": ValidacaoProjeto,
    "historicos": HistoricoStatusProjeto
}

# Ordem correta para exclusão total, evitando erros de chave estrangeira
ORDEM_EXCLUSAO_TOTAL = [
    HistoricoStatusProjeto,
    ValidacaoProjeto,
    Projeto,
    Cliente,
    Produto
]

def limpar_tabela(session: Session, modelo):
    """Exclui todos os registros de um modelo específico dentro de uma sessão."""
    try:
        nome_tabela = modelo.__tablename__
        num_rows_deleted = session.query(modelo).delete()
        print(f"  - Tabela '{nome_tabela}': {num_rows_deleted} registro(s) excluído(s).")
        return True
    except Exception as e:
        print(f"❌ ERRO ao limpar a tabela '{modelo.__tablename__}': {e}")
        return False

def main():
    """Função principal que executa a interface de linha de comando."""
    print("--- Utilitário de Limpeza de Banco de Dados ---")
    print("\nEscolha a operação:")
    print("1. Limpar TODAS as tabelas do banco de dados")
    print("2. Limpar uma tabela específica")
    print("Qualquer outra tecla para sair.")

    escolha = input("> ")

    session = SessionLocal()  # Cria uma única sessão para a operação

    try:
        if escolha == '1':
            print("\n⚠️ ATENÇÃO! Esta ação irá apagar PERMANENTEMENTE todos os dados de todas as tabelas.")
            confirmacao = input("Digite 'DELETAR TUDO' para confirmar: ")
            if confirmacao == 'DELETAR TUDO':
                print("\nIniciando limpeza completa...")
                sucesso = True
                for modelo in ORDEM_EXCLUSAO_TOTAL:
                    if not limpar_tabela(session, modelo):
                        sucesso = False
                        break # Para a operação se uma tabela falhar
                
                if sucesso:
                    session.commit()
                    print("\n✅ SUCESSO: Todas as tabelas foram limpas e as alterações salvas.")
                else:
                    session.rollback()
                    print("\n❌ FALHA: A operação foi revertida devido a um erro.")
            else:
                print("Operação cancelada.")

        elif escolha == '2':
            print("\nQual tabela você deseja limpar? Opções:", ", ".join(TABELAS_MAP.keys()))
            nome_tabela_escolhida = input("> ").lower()

            if nome_tabela_escolhida in TABELAS_MAP:
                modelo_escolhido = TABELAS_MAP[nome_tabela_escolhida]
                print(f"\n⚠️ ATENÇÃO! Você está prestes a apagar todos os dados da tabela '{nome_tabela_escolhida}'.")
                print("Isso pode falhar se outros registros dependerem destes (ex: apagar clientes com projetos existentes).")
                confirmacao = input("Digite 'sim' para confirmar: ")

                if confirmacao.lower() == 'sim':
                    if limpar_tabela(session, modelo_escolhido):
                        session.commit()
                        print("\n✅ SUCESSO: Tabela limpa e alterações salvas.")
                    else:
                        session.rollback()
                        print("\n❌ FALHA: A operação foi revertida.")
                else:
                    print("Operação cancelada.")
            else:
                print("Nome de tabela inválido.")
        else:
            print("Saindo...")
    
    finally:
        session.close() # Garante que a sessão seja sempre fechada.

if __name__ == "__main__":
    main()