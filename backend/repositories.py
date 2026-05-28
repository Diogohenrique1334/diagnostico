import datetime
from sqlalchemy.orm import Session, joinedload
from backend import models
from backend.emails import enviar_email_status
import pytz

class BaseRepository:

    def __init__(self, db_session: Session):
        self.db_session = db_session

    def commit(self):
        self.db_session.commit()

class ClienteRepository(BaseRepository):

    def get_all(self):
        return self.db_session.query(models.Cliente).order_by(models.Cliente.nome).all()

    def create(self, cliente: models.Cliente):
        self.db_session.add(cliente)
        self.commit()
        return cliente

class ProdutoRepository(BaseRepository):

    def get_all(self):
        return self.db_session.query(models.Produto).order_by(models.Produto.nome_produto).all()

    def create(self, produto: models.Produto):
        self.db_session.add(produto)
        self.commit()
        return produto

class ProjetoRepository(BaseRepository):
    def get_all(self):
        
        return self.db_session.query(models.Projeto).options(
            joinedload(models.Projeto.cliente),
            joinedload(models.Projeto.produto),
            joinedload(models.Projeto.validacoes),
            joinedload(models.Projeto.historico_status) # Carrega o histórico junto
        ).order_by(models.Projeto.id.desc()).all()
    
    def _get_brasilia_time(self):
        """Retorna a data e hora atual no fuso horário de Brasília."""
        return datetime.datetime.now(pytz.timezone('America/Sao_Paulo'))

    def create(self, projeto: models.Projeto):
        
        primeiro_historico = models.HistoricoStatusProjeto(
            status_anterior=None,
            status_novo=projeto.status_projeto,
            data_mudanca=self._get_brasilia_time()
        )
        projeto.historico_status.append(primeiro_historico)
        
        self.db_session.add(projeto)
        self.commit()
        return projeto

    def update_status(self, projeto_id: int, novo_status: models.StatusProjeto):
        
        projeto = self.db_session.query(models.Projeto).options(
            joinedload(models.Projeto.cliente) 
        ).filter(models.Projeto.id == projeto_id).first()
        
        if projeto and projeto.status_projeto != novo_status:
            status_antigo = projeto.status_projeto
            
            # Cria o novo registro de histórico
            novo_historico = models.HistoricoStatusProjeto(
                status_anterior=status_antigo,
                status_novo=novo_status,
                data_mudanca=self._get_brasilia_time(),
                projeto=projeto
            )
            self.db_session.add(novo_historico)
            
            # Atualiza o status do projeto
            projeto.status_projeto = novo_status
            self.commit() # Salva as mudanças no banco PRIMEIRO

            try:
                enviar_email_status(projeto, novo_status)
            except Exception as e:
                # Mesmo que o e-mail falhe, a aplicação não quebra,
                # pois o status já foi salvo no banco.
                print(f"ERRO no processo de e-mail, mas o status foi atualizado. Erro: {e}")
            
            return projeto
        return None
    
    def update_skills(self, projeto_id: int, skills_string: str or None):
        """
        Encontra um projeto pelo ID e atualiza sua lista de habilidades.
        """
        projeto = self.db_session.query(models.Projeto).filter(models.Projeto.id == projeto_id).first()
        if projeto:
            projeto.skills = skills_string
            self.commit()
        return projeto
    
    def update_emails_adicionais(self, projeto_id: int, emails_string: str or None):
        """
        Encontra um projeto pelo ID e atualiza sua lista de e-mails adicionais.
        """
        projeto = self.db_session.query(models.Projeto).filter(models.Projeto.id == projeto_id).first()
        if projeto:
            projeto.emails_adicionais = emails_string
            self.commit()
        return projeto

class ValidacaoRepository(BaseRepository):
    
    def create(self, validacao: models.ValidacaoProjeto):
        self.db_session.add(validacao)
        self.commit()
        return validacao
