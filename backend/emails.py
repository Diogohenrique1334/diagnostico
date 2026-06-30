import os

from backend.models import Projeto, StatusProjeto

# pywin32 (Outlook COM) é Windows-only. O import é feito de forma "lazy" dentro
# das funções de envio para que o módulo continue importável em Linux/Docker
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


# --------------------------------------------------------------------------- #
# Identidade visual compartilhada dos e-mails (fonte única de estilo).
# Cores sólidas + layout em tabelas: à prova do Outlook (que ignora muito CSS).
# --------------------------------------------------------------------------- #
_AZUL = "#14304F"      # primária (cabeçalho, destaques)
_DOURADO = "#C9A227"   # accent (faixa fina, fase atual do pipeline)
_VERDE = "#18990b"     # etapas concluídas / projeto finalizado
_CINZA = "#d5dae1"     # etapas ainda não alcançadas
_TXT = "#2c3e50"
_TXT_SUAVE = "#5a6675"

# Stepper do pipeline: 4 fases macro, na ordem do progresso.
_FASES_PIPELINE = ["Planejamento", "Desenvolvimento", "Validação", "Entrega"]
_FASE_DO_STATUS = {
    StatusProjeto.LEVANTAMENTO_REQUISITOS: 0,
    StatusProjeto.RECEBIMENTO_BASES: 1,
    StatusProjeto.ANALISE_EXPLORATORIA: 1,
    StatusProjeto.CONSTRUCAO_PIPELINE: 1,
    StatusProjeto.PRIMEIRA_VERSAO: 1,
    StatusProjeto.AJUSTES: 2,
    StatusProjeto.AJUSTES_FINOS: 2,
    StatusProjeto.DOCUMENTACAO: 3,
    StatusProjeto.FINALIZADO: 3,
}


def _formatar_nome_projeto(projeto: Projeto) -> str:
    """Title-case PT do nome do projeto (reusa a regra das propostas)."""
    try:
        from backend.propostas.dados import formatar_titulo
        return formatar_titulo(projeto.nome_projeto)
    except Exception:
        return (projeto.nome_projeto or "").title()


def _stepper_html(status: StatusProjeto) -> str:
    """Barra segmentada de 4 fases, destacando onde o projeto está agora."""
    idx = _FASE_DO_STATUS.get(status, 0)
    finalizado = status == StatusProjeto.FINALIZADO
    segmentos, rotulos = [], []
    for i, fase in enumerate(_FASES_PIPELINE):
        if finalizado:
            cor = _VERDE
        elif i < idx:
            cor = _AZUL
        elif i == idx:
            cor = _DOURADO
        else:
            cor = _CINZA
        segmentos.append(
            f'<td width="25%" style="padding:0 3px;">'
            f'<div style="height:8px;background-color:{cor};border-radius:4px;'
            f'font-size:0;line-height:8px;">&nbsp;</div></td>'
        )
        ativa = (i == idx) and not finalizado
        cor_rot = _AZUL if (i <= idx or finalizado) else "#9aa3af"
        peso = "bold" if (ativa or finalizado) else "600"
        rotulos.append(
            f'<td width="25%" align="center" style="padding:7px 2px 0;">'
            f'<span style="font-family:Segoe UI,Arial,sans-serif;font-size:11px;'
            f'font-weight:{peso};color:{cor_rot};">{fase}</span></td>'
        )
    return (
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
        'style="margin:6px 0 24px;"><tr>' + "".join(segmentos) + '</tr><tr>'
        + "".join(rotulos) + '</tr></table>'
    )


def _status_box(status_novo: str) -> str:
    """Caixa de destaque do status atual."""
    return (
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0">'
        f'<tr><td style="border-left:4px solid {_AZUL};background-color:#f4f7fb;'
        'padding:13px 18px;border-radius:0 6px 6px 0;">'
        '<div style="font-family:Segoe UI,Arial,sans-serif;font-size:11px;'
        'text-transform:uppercase;letter-spacing:.6px;color:#8a94a6;">Status atual</div>'
        f'<div style="font-family:Segoe UI,Arial,sans-serif;font-size:17px;font-weight:bold;'
        f'color:{_AZUL};margin-top:3px;">{status_novo}</div>'
        '</td></tr></table>'
    )


def _email_shell(titulo: str, subtitulo: str, corpo_interno: str) -> str:
    """Envelope visual comum: header azul + faixa dourada + corpo + assinatura.

    Fonte única de layout para todos os e-mails (status e início).
    """
    return f"""\
<html><body style="margin:0;padding:0;background-color:#eef1f5;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0"
       style="background-color:#eef1f5;padding:24px 0;">
<tr><td align="center">
  <table role="presentation" width="640" cellpadding="0" cellspacing="0"
         style="max-width:640px;width:100%;background-color:#ffffff;border-radius:10px;
                overflow:hidden;border:1px solid #e3e8ef;">
    <tr><td style="background-color:{_AZUL};padding:26px 30px;">
      <div style="color:#ffffff;font-family:Segoe UI,Arial,sans-serif;font-size:19px;
                  font-weight:600;">{titulo}</div>
      <div style="color:{_DOURADO};font-family:Segoe UI,Arial,sans-serif;font-size:13px;
                  font-weight:600;letter-spacing:.5px;margin-top:5px;">{subtitulo}</div>
    </td></tr>
    <tr><td style="height:3px;background-color:{_DOURADO};font-size:0;line-height:3px;">&nbsp;</td></tr>
    <tr><td style="padding:28px 30px;font-family:Segoe UI,Arial,sans-serif;color:{_TXT};">
      {corpo_interno}
    </td></tr>
    <tr><td style="padding:20px 30px;border-top:1px solid #eef1f5;background-color:#fafbfc;">
      <div style="font-family:Segoe UI,Arial,sans-serif;font-size:14px;color:{_TXT};">Atenciosamente,</div>
      <div style="font-family:Segoe UI,Arial,sans-serif;font-size:15px;font-weight:bold;
                  color:{_AZUL};margin-top:2px;">Diogo Oliveira</div>
      <div style="font-family:Segoe UI,Arial,sans-serif;font-size:12px;color:#8a94a6;">Cientista de Dados</div>
      <div style="font-family:Segoe UI,Arial,sans-serif;font-size:11px;color:#aab2bf;margin-top:12px;">
        Mensagem automática de acompanhamento. Em caso de dúvidas, basta responder a este e-mail.</div>
    </td></tr>
  </table>
</td></tr></table>
</body></html>"""


# Mensagem específica por status. Status fora deste dict não disparam e-mail
# (ex.: Levantamento de Requisitos, que tem e-mail de início próprio; Cancelado).
_MSG_STATUS = {
    StatusProjeto.RECEBIMENTO_BASES:
        "Recebi as bases de dados que serão utilizadas no projeto. A partir deste "
        "ponto, ele entra oficialmente na esteira de desenvolvimento.",
    StatusProjeto.ANALISE_EXPLORATORIA:
        "Iniciei a análise exploratória dos dados, com foco em compreender a "
        "estrutura, a distribuição e possíveis inconsistências. Se surgirem dúvidas "
        "relevantes, entro em contato para alinharmos.",
    StatusProjeto.CONSTRUCAO_PIPELINE:
        "Concluí a análise exploratória e estou construindo a pipeline de dados — "
        "etapa crítica para garantir a robustez, a escalabilidade e a qualidade da "
        "solução final.",
    StatusProjeto.PRIMEIRA_VERSAO:
        "Finalizei a primeira versão da solução, pronta para validação. Em breve "
        "farei uma apresentação para coletar o seu feedback e alinhar expectativas.",
    StatusProjeto.AJUSTES:
        "Recebi o feedback e já estou trabalhando nos ajustes necessários para "
        "refinar a solução e garantir maior aderência às suas necessidades.",
    StatusProjeto.AJUSTES_FINOS:
        "Estou nos ajustes finos da solução, refinando os últimos detalhes antes "
        "da entrega final.",
    StatusProjeto.DOCUMENTACAO:
        "O projeto está em fase de finalização. Estou preparando a documentação "
        "técnica e de uso para garantir autonomia e facilidade na adoção da solução.",
    StatusProjeto.FINALIZADO:
        "Concluí o projeto com sucesso. Agradeço pela parceria e pela confiança. "
        "Espero que a solução entregue gere valor e resultados significativos.",
}


def get_email_content(projeto: Projeto, novo_status: StatusProjeto):
    """Retorna (assunto, corpo_html) do e-mail de acompanhamento, por status.

    Retorna (None, None) para status que não disparam comunicação.
    """
    mensagem = _MSG_STATUS.get(novo_status)
    if mensagem is None:
        return None, None

    nome_cliente = projeto.cliente.nome.split(" ")[0].capitalize()
    nome_projeto = _formatar_nome_projeto(projeto)
    finalizado = novo_status == StatusProjeto.FINALIZADO

    assunto = (
        f"✅ Projeto Concluído: '{nome_projeto}'" if finalizado
        else f"Atualização do Projeto: '{nome_projeto}'"
    )

    selo = ""
    if finalizado:
        selo = (
            '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
            f'style="margin:0 0 18px;"><tr><td style="background-color:#eef7ec;'
            f'border-left:4px solid {_VERDE};padding:13px 18px;border-radius:0 6px 6px 0;'
            'font-family:Segoe UI,Arial,sans-serif;font-size:15px;font-weight:bold;'
            'color:#0E5E07;">✓ Projeto concluído</td></tr></table>'
        )

    corpo = (
        f'<p style="margin:0 0 16px;font-size:15px;">Olá, <strong>{nome_cliente}</strong>!</p>'
        f'<p style="margin:0 0 6px;font-size:15px;line-height:1.6;color:{_TXT_SUAVE};">'
        'Tenho uma atualização sobre o andamento do seu projeto. '
        'Veja em que fase ele está agora:</p>'
        f'{_stepper_html(novo_status)}'
        f'{selo}'
        f'{_status_box(novo_status.value)}'
        f'<p style="margin:22px 0 0;font-size:15px;line-height:1.6;">{mensagem}</p>'
    )
    return assunto, _email_shell("Atualização do seu projeto", nome_projeto, corpo)


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
    nome_projeto = _formatar_nome_projeto(projeto)

    usa_imagem = os.path.exists(CICLO_VIDA_IMG)
    if usa_imagem:
        ciclo_html = (
            '<div style="text-align:center;margin:10px 0;">'
            '<img src="cid:ciclovida" alt="Ciclo de vida do projeto" '
            'style="max-width:340px;width:100%;border-radius:10px;" /></div>'
        )
    else:
        ciclo_html = _ciclo_vida_html()

    prazo_box = (
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
        'style="margin:6px 0 22px;"><tr><td style="border-left:4px solid ' + _VERDE + ';'
        'background-color:#eef7ec;padding:14px 18px;border-radius:0 6px 6px 0;">'
        '<div style="font-family:Segoe UI,Arial,sans-serif;font-size:11px;'
        'text-transform:uppercase;letter-spacing:.6px;color:#6b8f63;">'
        'Previsão de entrega da primeira versão</div>'
        '<div style="font-family:Segoe UI,Arial,sans-serif;font-size:18px;font-weight:bold;'
        'color:#0E5E07;margin-top:3px;">' + str(dias) + ' dias úteis</div>'
        '</td></tr></table>'
    )

    corpo = (
        f'<p style="margin:0 0 16px;font-size:15px;">Olá, <strong>{nome_cliente}</strong>!</p>'
        '<p style="margin:0 0 18px;font-size:15px;line-height:1.6;color:' + _TXT_SUAVE + ';">'
        'É com satisfação que dou início ao seu projeto. A partir de agora, sigo com o '
        'levantamento de requisitos e o acesso às fontes de dados.</p>'
        + prazo_box +
        '<p style="margin:0 0 4px;font-size:15px;line-height:1.6;">Durante o desenvolvimento, '
        'você receberá uma comunicação automática a cada mudança de etapa. Veja abaixo o '
        'ciclo de vida que o projeto vai percorrer:</p>'
        f'<div style="font-family:Segoe UI,Arial,sans-serif;font-size:13px;font-weight:bold;'
        f'color:{_AZUL};margin:18px 0 8px;">Ciclo de vida do projeto</div>'
        + ciclo_html
    )

    assunto = f"Início do Projeto: '{nome_projeto}'"
    corpo_html = _email_shell("Início do seu projeto", nome_projeto, corpo)
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
