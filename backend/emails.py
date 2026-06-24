import os

from backend.models import Projeto, StatusProjeto

# pywin32 (Outlook COM) é Windows-only. O import é feito de forma "lazy" dentro
# de enviar_email_status para que o módulo continue importável em Linux/Docker
# (onde o envio de e-mail simplesmente não acontece).

# Imagem do ciclo de vida (anexada inline no e-mail de início). Se o arquivo não
# existir, o e-mail usa um fallback em HTML (mesmo conteúdo, desenhado com texto).
_ASSETS = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")
CICLO_VIDA_IMG = os.path.join(_ASSETS, "ciclo_de_vida.png")

# Fases do ciclo de vida: (fase, [(emoji, texto, destaque)]). Renderizado em HTML
# à prova de Outlook (tabelas). `destaque=True` pinta de verde (marco de validação).
_CICLO_FASES = [
    ("Planejamento", [("📄", "Diagnóstico e levantamento de requisitos", False)]),
    ("Desenvolvimento", [
        ("🔍", "Levantamento das bases e análise exploratória", False),
        ("⚙️", "Construção da pipeline de dados", False),
        ("📊", "Construção da primeira versão", False),
    ]),
    ("Validação", [("👥", "Apresentação da versão inicial", True)]),
    ("Entrega", [
        ("📦", "Documentar, compartilhar e/ou colocar em produção", False),
        ("🏁", "Entrega da solução e encerramento do projeto", False),
    ]),
]

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


# --------------------------------------------------------------------------- #
# E-mail de INÍCIO de projeto (gatilho), enviado direto como os de evolução
# --------------------------------------------------------------------------- #
_CSS_EMAIL = """
<style>
    body { font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; color: #333; }
    .corpo { max-width: 700px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 8px; }
    .header { background-color: #005A9C; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }
    .content { padding: 25px; background-color: #f8f9fa; }
    .prazo-box { border-left: 10px solid #18990b; padding: 15px; margin: 20px 0; background-color: #eef7ec; }
    .prazo-text { font-size: 1.25em; font-weight: bold; color: #0E5E07; }
    .ciclo-titulo { font-size: 1.05em; font-weight: bold; color: #005A9C; margin: 22px 0 8px; }
    .rodape { margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; color: #7f8c8d; font-size: 0.9em; text-align: center; }
</style>
"""


def _ciclo_card(emoji: str, texto: str, destaque: bool) -> str:
    bg = "#2E7D52" if destaque else "#7a1f1f"
    return (
        '<table role="presentation" cellpadding="0" cellspacing="0" align="center" '
        'style="margin:0 auto;"><tr>'
        f'<td bgcolor="{bg}" style="background-color:{bg};color:#ffffff;border-radius:8px;'
        'padding:11px 18px;font-size:13px;font-weight:600;text-align:center;'
        f'font-family:Segoe UI,Arial,sans-serif;">{emoji}&nbsp;&nbsp;{texto}</td>'
        '</tr></table>'
    )


def _ciclo_seta() -> str:
    return ('<div style="text-align:center;color:#b9c0cb;font-size:15px;'
            'line-height:18px;margin:0;">&#9660;</div>')


def _ciclo_fase_label(fase: str) -> str:
    return ('<div style="text-align:center;color:#7a1f1f;font-weight:bold;font-style:italic;'
            'font-size:11px;text-transform:uppercase;letter-spacing:.6px;'
            'margin:14px 0 6px;">' + fase + '</div>')


def _ciclo_vida_html() -> str:
    """Ciclo de vida desenhado em HTML à prova de Outlook (tabelas + cores sólidas)."""
    blocos = []
    primeiro_card = True
    for fase, etapas in _CICLO_FASES:
        blocos.append(_ciclo_fase_label(fase))
        for emoji, texto, destaque in etapas:
            if not primeiro_card:
                blocos.append(_ciclo_seta())
            blocos.append(_ciclo_card(emoji, texto, destaque))
            primeiro_card = False
            if destaque:
                blocos.append(
                    '<div style="text-align:center;color:#7f8c8d;font-style:italic;'
                    'font-size:11px;margin:4px 0;">&#8635; com ciclos de ajustes conforme feedback</div>'
                )
    interno = "".join(blocos)
    # Container centralizado com largura limitada (reflui bem no mobile).
    return (
        '<table role="presentation" cellpadding="0" cellspacing="0" align="center" '
        'style="margin:6px auto;max-width:380px;width:100%;"><tr><td>'
        f'{interno}</td></tr></table>'
    )


def get_email_inicio_content(projeto: Projeto, dias: int):
    """Retorna (assunto, corpo_html, usa_imagem) do e-mail de início do projeto."""
    nome_cliente = (projeto.cliente.nome or "").split(" ")[0].capitalize() or "tudo bem"
    try:
        from backend.propostas.dados import formatar_titulo
        nome_projeto = formatar_titulo(projeto.nome_projeto)
    except Exception:
        nome_projeto = (projeto.nome_projeto or "").title()

    usa_imagem = os.path.exists(CICLO_VIDA_IMG)
    if usa_imagem:
        ciclo_html = (
            '<div style="text-align:center;margin:10px 0;">'
            '<img src="cid:ciclovida" alt="Ciclo de vida do projeto" '
            'style="max-width:340px;width:100%;border-radius:10px;" /></div>'
        )
    else:
        ciclo_html = _ciclo_vida_html()

    assunto = f"Início do Projeto: '{nome_projeto}'"
    corpo_html = f"""
    <html>
    <head>{_CSS_EMAIL}</head>
    <body>
        <div class="corpo">
            <div class="header"><h2>Início do Projeto</h2></div>
            <div class="content">
                <p>Olá, <strong>{nome_cliente}</strong>!</p>
                <p>É com satisfação que dou início ao projeto
                   <span style="font-weight:bold;">'{nome_projeto}'</span>.
                   A partir de agora, sigo com o levantamento de requisitos e o acesso às
                   fontes de dados.</p>

                <div class="prazo-box">
                    Previsão de entrega da primeira versão:<br>
                    <span class="prazo-text">{dias} dias úteis</span>
                </div>

                <p>Durante o desenvolvimento, você receberá uma comunicação automática a cada
                   mudança de etapa. Veja abaixo o ciclo de vida que o projeto vai percorrer:</p>

                <div class="ciclo-titulo">Ciclo de vida do projeto</div>
                {ciclo_html}

                <div class="rodape">
                    <p>Atenciosamente,<br><strong>Diogo Oliveira</strong><br>Cientista de Dados</p>
                    <p style="font-size: 0.8em;">Este é um e-mail automático. Em caso de dúvidas, responda a este e-mail.</p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    return assunto, corpo_html, usa_imagem


def enviar_email_inicio_projeto(projeto: Projeto, dias: int) -> None:
    """Envia o e-mail de início do projeto (To = cliente, CC = e-mails adicionais).

    Levanta exceção em caso de falha para o chamador reportar ao usuário.
    """
    ccs = [pe.email.strip() for pe in projeto.emails_adicionais if pe.email and pe.email.strip()]
    if not projeto.cliente.email and not ccs:
        raise ValueError("Projeto sem e-mail de cliente cadastrado.")

    assunto, corpo_html, usa_imagem = get_email_inicio_content(projeto, dias)

    # Import lazy: só funciona no Windows com Outlook.
    import pythoncom
    import win32com.client as win32

    destino = projeto.cliente.email or ccs[0]

    pythoncom.CoInitialize()
    outlook = win32.Dispatch('outlook.application')
    email = outlook.CreateItem(0)
    email.To = destino
    if ccs:
        email.CC = ";".join(ccs)
    email.Subject = assunto
    if usa_imagem:
        anexo = email.Attachments.Add(CICLO_VIDA_IMG)
        # Define o Content-Id para referenciar a imagem inline via cid:ciclovida.
        anexo.PropertyAccessor.SetProperty(
            "http://schemas.microsoft.com/mapi/proptag/0x3712001F", "ciclovida"
        )
    email.HTMLBody = corpo_html
    email.Send()
    print(f"✅ E-mail de início do projeto '{projeto.nome_projeto}' enviado para {destino}.")
    return destino