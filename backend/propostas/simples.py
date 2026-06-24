"""Modelo de proposta SIMPLES — amigos / projetos de validação.

Mantém a regra de risco compartilhado (50/50 do MVP). Cobrança por horas
(estimadas ou realizadas), com escopo, premissas/exclusões, pagamento,
garantia, validade e aceite.
"""

from __future__ import annotations

from reportlab.platypus import KeepTogether, Paragraph, Spacer

from backend.propostas import componentes as c
from backend.propostas.dados import (
    EXCLUSOES_PADRAO,
    PREMISSAS_PADRAO,
    DadosProposta,
    formatar_moeda,
    formatar_titulo,
)

_ETAPAS = [
    ("Diagnóstico Inicial",
     "Reunião para entendimento da necessidade, objetivos, expectativas e requisitos do projeto."),
    ("Desenvolvimento do MVP",
     "Criação de uma versão inicial da solução para validar a ideia e coletar feedbacks."),
    ("Apresentação do MVP",
     "Demonstração da solução desenvolvida, incluindo funcionalidades implementadas e tempo investido."),
    ("Decisão do Cliente",
     "Avaliação conjunta para definir se o projeto seguirá para as próximas etapas."),
    ("Continuidade do Projeto",
     "Em caso de aprovação, o projeto seguirá o fluxo normal de desenvolvimento e entregas."),
    ("Encerramento",
     "Caso não haja interesse na continuidade, o projeto será encerrado após a conclusão do MVP."),
]


def gerar(dados: DadosProposta) -> bytes:
    e = c.build_styles()
    estim = dados.valores_estimados
    flow = []

    flow.append(c.tabela_meta([
        ("Cliente", dados.cliente),
        ("Tipo", dados.tipo_projeto),
        ("Data", dados.data_formatada),
        ("Validade", f"até {dados.validade_formatada}"),
    ], e))
    flow.append(Spacer(1, 12))
    flow.append(c.faixa_kpis([
        (formatar_moeda(dados.total), "Investimento estimado (MVP)" if estim else "Investimento (MVP)"),
        (f"{dados.quantidade:.0f} h", "Horas do MVP" if estim else "Horas realizadas"),
        (dados.validade_formatada, "Válida até"),
    ], e))
    flow.append(Spacer(1, 16))

    # Objetivo
    flow.append(c.secao("Objetivo", e))
    flow.append(Spacer(1, 8))
    flow.append(Paragraph(
        "Este documento apresenta, de forma transparente, o modelo de trabalho e cobrança "
        "para o desenvolvimento do projeto em caráter colaborativo, voltado a projetos "
        "selecionados, com interesse mútuo na construção da solução e no aprendizado técnico.",
        e["lead"]))
    if dados.objetivo:
        flow.append(Paragraph(f"<b>Objetivo do projeto:</b> {dados.objetivo}", e["corpo"]))
    flow.append(Spacer(1, 14))

    # Escopo / entregáveis
    if dados.escopo:
        flow.append(c.secao("Escopo do MVP / Entregáveis", e))
        flow.append(Spacer(1, 8))
        flow.extend(c.bullets(dados.escopo, e))
        flow.append(Spacer(1, 14))

    # Modelo de cobrança + investimento
    flow.append(c.secao("Modelo de Cobrança", e))
    flow.append(Spacer(1, 8))
    flow.append(Paragraph(
        "A cobrança é realizada com base nas horas efetivamente investidas no projeto. "
        "O valor é aplicado a projetos selecionados, quando existe interesse mútuo na "
        "construção da solução e no desenvolvimento de novas habilidades e abordagens.",
        e["corpo"]))
    flow.append(Spacer(1, 8))
    flow.append(c.tabela_investimento(
        [(f"MVP - {dados.quantidade:.0f}h × {formatar_moeda(dados.valor_unitario)}/h",
          formatar_moeda(dados.total))],
        "Investimento estimado do MVP" if estim else "Investimento do MVP",
        formatar_moeda(dados.total), e,
    ))
    if estim:
        flow.append(Paragraph(
            "<font size=8 color='#5A6B7B'>* Estimativa do MVP. A cobrança final reflete as "
            "horas efetivamente investidas.</font>", e["corpo"]))
    flow.append(Spacer(1, 14))

    # Premissas e exclusões
    flow.append(c.premissas_exclusoes(
        dados.premissas or PREMISSAS_PADRAO, dados.exclusoes or EXCLUSOES_PADRAO, e))
    flow.append(Spacer(1, 14))

    # Fluxo de trabalho
    flow.append(c.secao("Fluxo de Trabalho", e))
    flow.append(Spacer(1, 10))
    for i, (titulo, desc) in enumerate(_ETAPAS, start=1):
        flow.append(c.etapa(i, titulo, desc, e))
        flow.append(Spacer(1, 6))
    flow.append(Spacer(1, 10))

    # Regra de risco compartilhado (mantida) — título + box juntos
    flow.append(KeepTogether([
        c.secao("Regra de Compartilhamento de Risco", e),
        Spacer(1, 10),
        c.destaque([
            Paragraph(
                "Após a apresentação do MVP, o cliente terá total liberdade para decidir pela "
                "continuidade ou não do projeto.", e["corpo"]),
            Spacer(1, 6),
            Paragraph("<b>Se o projeto continuar:</b> o desenvolvimento seguirá normalmente, "
                      "utilizando o mesmo modelo de cobrança por horas investidas.", e["corpo"]),
            Spacer(1, 4),
            Paragraph("<b>Se o projeto for encerrado:</b> como forma de compartilhamento de risco "
                      "entre as partes, o profissional absorverá 50% do tempo investido na "
                      "construção do MVP, ficando sob responsabilidade do cliente o pagamento dos "
                      "50% restantes.", e["corpo"]),
        ]),
    ]))
    flow.append(Spacer(1, 14))

    # Forma de pagamento
    flow.append(c.secao("Forma de Pagamento", e))
    flow.append(Spacer(1, 8))
    flow.append(Paragraph(
        "O pagamento é realizado após a apresentação do MVP, mediante o relatório de horas "
        "investidas. Em caso de continuidade, as etapas seguintes seguem a mesma base de "
        "cobrança, com fechamento combinado a cada entrega.", e["corpo"]))
    flow.append(Spacer(1, 14))

    # Garantia e suporte
    if dados.garantia_dias:
        flow.append(c.secao("Garantia e Suporte", e))
        flow.append(Spacer(1, 8))
        flow.append(Paragraph(
            f"Estão inclusos <b>{dados.garantia_dias} dias</b> de suporte e ajustes após a "
            "entrega do MVP, para correções dentro do escopo acordado.", e["corpo"]))
        flow.append(Spacer(1, 14))

    # Considerações finais
    flow.append(c.secao("Considerações Finais", e))
    flow.append(Spacer(1, 8))
    flow.append(Paragraph(
        "Este modelo foi criado para reduzir barreiras de entrada, aumentar a transparência do "
        "processo e permitir que o cliente avalie o potencial da solução antes de investimentos "
        "maiores. O objetivo é construir uma relação de confiança e alinhamento desde o início.",
        e["corpo"]))

    # Aceite
    if dados.incluir_aceite:
        flow.append(Spacer(1, 16))
        flow.append(KeepTogether([
            c.secao("Aceite", e),
            Spacer(1, 8),
            Paragraph("Ao assinar, as partes concordam com o escopo, os valores e as condições "
                      "descritos nesta proposta.", e["corpo"]),
            Spacer(1, 6),
            c.bloco_aceite(e, dados.profissional, dados.cargo, dados.assinatura_path),
        ]))

    return c.gerar_documento(
        flow,
        eyebrow="Proposta de Prestação de Serviços",
        titulo=formatar_titulo(dados.nome_projeto),
        profissional=dados.profissional, cargo=dados.cargo, contato=dados.contato,
        titulo_pdf=f"Proposta — {dados.nome_projeto}",
        foto_path=dados.foto_path, numero=dados.numero,
    )
