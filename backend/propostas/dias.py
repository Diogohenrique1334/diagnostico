"""Modelo DIAS — projetos do emprego formal (sem cobrança).

Não envolve dinheiro: o Diogo é assalariado. O documento comunica a **previsão
de dias de trabalho para a entrega da primeira versão**, estimada a partir de
projetos semelhantes já realizados. O e-mail que acompanha serve para
**formalizar o gatilho de início** do projeto.
"""

from __future__ import annotations

from reportlab.platypus import Paragraph, Spacer

from backend.propostas import componentes as c
from backend.propostas.dados import DadosProposta, formatar_titulo


def _texto_referencias(dados: DadosProposta) -> str:
    if not dados.referencias:
        return ""
    return "; ".join(f"{nome} (~{qtd:.0f} dias)" for nome, qtd in dados.referencias)


def gerar(dados: DadosProposta) -> bytes:
    e = c.build_styles()
    flow = []

    flow.append(c.tabela_meta([
        ("Projeto", dados.nome_projeto),
        ("Tipo", dados.tipo_projeto),
        ("Solicitante", dados.destinatario or dados.cliente),
        ("Data de início", dados.data_formatada),
    ], e))
    flow.append(Spacer(1, 12))

    kpis = [(f"{dados.quantidade:.0f} dias", "Previsão da 1ª versão"),
            (dados.tipo_projeto, "Tipo de projeto")]
    if dados.referencias:
        kpis.append((str(len(dados.referencias)), "Projetos de base"))
    flow.append(c.faixa_kpis(kpis, e))
    flow.append(Spacer(1, 16))

    # Previsão de entrega
    flow.append(c.secao("Previsão de Entrega", e))
    flow.append(Spacer(1, 8))
    flow.append(Paragraph(
        f"Previsão de <b>{dados.quantidade:.0f} dias de trabalho</b> para a entrega da "
        "<b>primeira versão</b> do projeto, dimensionada a partir do histórico de projetos "
        "semelhantes já entregues. A data efetiva pode variar conforme prioridades e "
        "disponibilidade de dados/acessos.", e["lead"]))
    if dados.objetivo:
        flow.append(Paragraph(f"<b>Objetivo:</b> {dados.objetivo}", e["corpo"]))
    flow.append(Spacer(1, 14))

    # Base da estimativa (projetos de referência)
    if dados.referencias:
        flow.append(c.secao("Base da Estimativa", e))
        flow.append(Spacer(1, 8))
        flow.append(Paragraph(
            "A previsão considera a similaridade de tipo de projeto e de habilidades técnicas "
            "com os seguintes projetos de referência:", e["corpo"]))
        flow.extend(c.bullets(
            [f"{nome} — aproximadamente {qtd:.0f} dias" for nome, qtd in dados.referencias], e))
        flow.append(Spacer(1, 14))

    # Atividades / entregáveis da 1ª versão
    if dados.escopo:
        flow.append(c.secao("Escopo da Primeira Versão", e))
        flow.append(Spacer(1, 8))
        flow.extend(c.bullets(dados.escopo, e))
        flow.append(Spacer(1, 14))

    # Próximos passos
    flow.append(c.secao("Próximos Passos", e))
    flow.append(Spacer(1, 8))
    flow.append(Paragraph(
        "Com o aceite desta previsão, considero o projeto <b>iniciado</b> e passo ao "
        "levantamento de requisitos e ao acesso às fontes de dados. Eventuais ajustes de "
        "escopo que impactem o prazo serão comunicados assim que identificados.", e["corpo"]))

    return c.gerar_documento(
        flow,
        eyebrow="Previsão de Entrega — 1ª Versão",
        titulo=formatar_titulo(dados.nome_projeto),
        profissional=dados.profissional, cargo=dados.cargo, contato=dados.contato,
        titulo_pdf=f"Previsão de entrega — {dados.nome_projeto}",
        foto_path=dados.foto_path, numero=dados.numero,
    )


def gerar_email_dias(dados: DadosProposta) -> tuple[str, str]:
    """Gera (assunto, corpo) do e-mail que formaliza o início do projeto."""
    assunto = f"Início do projeto — {formatar_titulo(dados.nome_projeto)} (previsão da 1ª versão)"

    saudacao = f"Olá {dados.destinatario}," if dados.destinatario else "Olá,"
    referencias = _texto_referencias(dados)
    base = (
        f" A estimativa foi dimensionada a partir de projetos semelhantes já entregues "
        f"({referencias})." if referencias else
        " A estimativa foi dimensionada a partir do histórico de projetos semelhantes já entregues."
    )

    corpo = (
        f"{saudacao}\n\n"
        f"Este e-mail formaliza o início do projeto \"{formatar_titulo(dados.nome_projeto)}\".\n\n"
        f"Com base no escopo levantado e na comparação com projetos de perfil parecido "
        f"(mesmo tipo de trabalho e habilidades técnicas envolvidas), a previsão é de "
        f"aproximadamente {dados.quantidade:.0f} dias de trabalho para a entrega da primeira "
        f"versão.{base}\n\n"
        f"A partir desta confirmação, considero o projeto iniciado e sigo com o levantamento "
        f"de requisitos e o acesso às fontes de dados. Qualquer mudança de escopo que afete o "
        f"prazo será comunicada assim que identificada.\n\n"
        f"Segue em anexo o documento com o detalhamento da previsão e da base de comparação.\n\n"
        f"Atenciosamente,\n{dados.profissional}\n{dados.contato}"
    )
    return assunto, corpo
