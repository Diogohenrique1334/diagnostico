from backend.models import Projeto, StatusProjeto

# pywin32 (Outlook COM) é Windows-only. O import é feito de forma "lazy" dentro
# de enviar_email_status para que o módulo continue importável em Linux/Docker
# (onde o envio de e-mail simplesmente não acontece).

def get_email_content(projeto: Projeto, novo_status: StatusProjeto):
    """
    Retorna o Assunto e o Corpo HTML do e-mail, personalizados para cada status.
    """
    nome_cliente = projeto.cliente.nome.split(" ")[0].capitalize()
    nome_projeto = projeto.nome_projeto

    # --- TEMPLATES DE E-MAIL ---
    # Aqui você pode personalizar a mensagem para cada etapa do projeto.
    
    assunto = f"Atualização do Projeto: '{nome_projeto}'"
    corpo_html = ""

    # Template base do HTML
    html_template = """
    <html>
    <head>
        <style>
            body {{ font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; color: #333; }}
            .corpo {{ max-width: 700px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 8px; }}
            .header {{ background-color: #005A9C; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
            .content {{ padding: 25px; background-color: #f8f9fa; }}
            .status-box {{ border-left: 10px solid #005A9C; padding: 15px; margin: 20px 0; background-color: #e7f3fe; }}
            .status-text {{ font-size: 1.2em; font-weight: bold; color: #005A9C; }}
            .rodape {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; color: #7f8c8d; font-size: 0.9em; text-align: center; }}
        </style>
    </head>
    <body>
        <div class="corpo">
            <div class="header">
                <h2>Atualização de Status do Projeto</h2>
            </div>
            <div class="content">
                <p>Olá, <strong>{nome_cliente}</strong>!</p>
                <p>Temos uma novidade sobre o andamento do seu projeto <span style="font-weight:bold;">'{nome_projeto}'</span>.</p>
                
                <div class="status-box">
                    O status foi atualizado para: <br>
                    <span class="status-text">{status_novo}</span>
                </div>
                
                <p>{mensagem_especifica}</p>
                
                <div class="rodape">
                    <p>Atenciosamente,<br><strong>Diogo Oliveira</strong></p>
                    <p style="font-size: 0.8em;">Este é um e-mail automático. Em caso de dúvidas, responda a este e-mail.</p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

    # Mensagens específicas para cada status
    if novo_status == StatusProjeto.RECEBIMENTO_BASES:
        mensagem_especifica = "Recebi as bases de dados que serão utilizadas no projeto. A partir deste ponto, o projeto entra oficialmente na esteira de desenvolvimento."
    elif novo_status == StatusProjeto.ANALISE_EXPLORATORIA:
        mensagem_especifica = "Iniciei a etapa de análise exploratória dos dados, com foco em compreender a estrutura, distribuição e possíveis inconsistências. Caso surjam dúvidas relevantes, entrarei em contato para esclarecimentos."    
    elif novo_status == StatusProjeto.CONSTRUCAO_PIPELINE:
        mensagem_especifica = "Concluí a análise exploratória e agora estou construindo a pipeline de dados, etapa crítica para garantir a robustez, escalabilidade e qualidade da solução final."
    elif novo_status == StatusProjeto.PRIMEIRA_VERSAO:
        mensagem_especifica = "Finalizei a primeira versão da solução, que está pronta para validação. Em breve, farei uma apresentação para coleta de feedback e alinhamento de expectativas."
    elif novo_status == StatusProjeto.AJUSTES:
        mensagem_especifica = "Recebi o feedback e já estou trabalhando nos ajustes necessários para refinar a solução e garantir maior aderência às necessidades do projeto."
    elif novo_status == StatusProjeto.DOCUMENTACAO:
        mensagem_especifica = "O projeto está em fase de finalização. Estou preparando a documentação técnica e de uso, visando garantir autonomia e facilidade na adoção da solução."
    elif novo_status == StatusProjeto.FINALIZADO:
        assunto = f"✅ Projeto Concluído: '{nome_projeto}'"
        mensagem_especifica = "Concluí o projeto com sucesso. Agradeço pela parceria e confiança. Espero que a solução entregue gere valor e resultados significativos."
    else:
        # Status que não enviam e-mail ou usam uma mensagem padrão
        return None, None

    corpo_html = html_template.format(
        nome_cliente=nome_cliente,
        nome_projeto=nome_projeto,
        status_novo=novo_status.value,
        mensagem_especifica=mensagem_especifica
    )

    return assunto, corpo_html

def enviar_email_status(projeto: Projeto, novo_status: StatusProjeto):
    """
    Envia um e-mail para o cliente principal e para os e-mails adicionais.
    """
    # Coletar todos os destinatários
    destinatarios = []
    
    # Cliente principal
    if projeto.cliente.email:
        destinatarios.append(projeto.cliente.email)

    # E-mails adicionais (relationship: lista de ProjetoEmail)
    ccs = [pe.email.strip() for pe in projeto.emails_adicionais if pe.email and pe.email.strip()]
    destinatarios.extend(ccs)

    if not destinatarios:
        print(f"AVISO: Nenhum e-mail encontrado para o projeto '{projeto.nome_projeto}'. E-mail não enviado.")
        return

    assunto, corpo_html = get_email_content(projeto, novo_status)
    if not assunto:
        print(f"INFO: Nenhum e-mail configurado para o status '{novo_status.value}'. E-mail não enviado.")
        return

    try:
        # Import lazy: só funciona no Windows com Outlook (não existe em Linux/Docker).
        import pythoncom
        import win32com.client as win32

        pythoncom.CoInitialize()
        print(f"Tentando enviar e-mail para {len(destinatarios)} destinatário(s): {', '.join(destinatarios)}")
        outlook = win32.Dispatch('outlook.application')
        
        # Criar e-mail
        email = outlook.CreateItem(0)
        email.To = projeto.cliente.email  # Cliente principal
        
        # Adicionar e-mails adicionais em CC
        if ccs:
            email.CC = ";".join(ccs)
        
        email.Subject = assunto
        email.HTMLBody = corpo_html
        email.Send()
        
        print(f"✅ SUCESSO: E-mail para o projeto '{projeto.nome_projeto}' enviado para {len(destinatarios)} destinatário(s).")
                
    except Exception as e:
        print(f"❌ ERRO: Falha ao tentar enviar o e-mail.")
        print(f"   Detalhes: {e}")