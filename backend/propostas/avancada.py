"""Modelo de proposta AVANÇADA — projetos maiores / clientes reais.

MVP de escopo fechado pago integralmente. Inclui escopo, investimento,
premissas/exclusões, fluxo, pagamento, garantia, propriedade/confidencialidade,
validade e aceite. Sem regra de risco 50/50.
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
    ("Diagnóstico e Alinhamento",
     "Entendimento aprofundado do problema de negócio, requisitos, dados disponíveis e critérios de sucesso."),
    ("Desenvolvimento do MVP",
     "Construção da solução de escopo fechado acordado, com checkpoints de acompanhamento."),
    ("Entrega e Validação",
     "Apresentação da solução, validação dos critérios de aceite e ajustes previstos no escopo."),
    ("Evolução (opcional)",
     "Novas funcionalidades e melhorias seguem em escopos/contratos complementares acordados à parte."),
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
    kpis = [
        (formatar_moeda(dados.total), "Investimento (preço fechado)"),
        (f"{dados.quantidade:.0f} h", "Esforço estimado" if estim else "Horas realizadas"),
    ]
    if dados.prazo_dias:
        kpis.append((f"{dados.prazo_dias} dias", "Prazo de entrega"))
    flow.append(c.faixa_kpis(kpis, e))
    flow.append(Spacer(1, 16))

    # Objetivo
    flow.append(c.secao("Objetivo", e))
    flow.append(Spacer(1, 8))
    flow.append(Paragraph(
        "Esta proposta apresenta o escopo, o investimento e as condições para o desenvolvimento "
        "da solução, com entregáveis e critérios claros para garantir previsibilidade a ambas as "
        "partes.", e["lead"]))
    if dados.objetivo:
        flow.append(Paragraph(f"<b>Objetivo do projeto:</b> {dados.objetivo}", e["corpo"]))
    flow.append(Spacer(1, 14))

    # Escopo e entregáveis
    flow.append(c.secao("Escopo e Entregáveis", e))
    flow.append(Spacer(1, 8))
    if dados.escopo:
        flow.extend(c.bullets(dados.escopo, e))
    else:
        flow.append(Paragraph(
            "O escopo detalhado dos entregáveis será anexado e acordado antes do início.",
            e["corpo"]))
    flow.append(Spacer(1, 14))

    # Investimento (preço fechado)
    flow.append(c.secao("Investimento", e))
    flow.append(Spacer(1, 8))
    prazo = f" Prazo estimado de entrega: {dados.prazo_dias} dias." if dados.prazo_dias else ""
    flow.append(Paragraph(
        "O MVP é entregue por <b>preço fechado</b>, dando previsibilidade total de custo ao "
        f"cliente.{prazo}", e["corpo"]))
    flow.append(Spacer(1, 8))
    rotulo_horas = "h" if estim else "h realizadas"
    flow.append(c.tabela_investimento(
        [(f"MVP de escopo fechado - {dados.quantidade:.0f}{rotulo_horas} × "
          f"{formatar_moeda(dados.valor_unitario)}/h", formatar_moeda(dados.total))],
        "Investimento total do MVP", formatar_moeda(dados.total), e,
    ))
    flow.append(Spacer(1, 14))

    # Premissas e exclusões
    flow.append(c.premissas_exclusoes(
        dados.premissas or PREMISSAS_PADRAO, dados.exclusoes or EXCLUSOES_PADRAO, e))
    flow.append(Spacer(1, 14))

    # Fluxo
    flow.append(c.secao("Fluxo de Trabalho", e))
    flow.append(Spacer(1, 10))
    for i, (titulo, desc) in enumerate(_ETAPAS, start=1):
        flow.append(c.etapa(i, titulo, desc, e))
        flow.append(Spacer(1, 6))
    flow.append(Spacer(1, 12))

    # Forma e prazo de pagamento
    flow.append(c.secao("Forma e Prazo de Pagamento", e))
    flow.append(Spacer(1, 8))
    flow.append(Paragraph(
        "<b>50%</b> na aprovação desta proposta (início dos trabalhos) e <b>50%</b> na entrega "
        "do MVP validado. Pagamento via PIX ou transferência, com vencimento de até 5 dias úteis "
        "após cada marco.", e["corpo"]))
    flow.append(Spacer(1, 14))

    # Garantia e suporte
    if dados.garantia_dias:
        flow.append(c.secao("Garantia e Suporte", e))
        flow.append(Spacer(1, 8))
        flow.append(Paragraph(
            f"Estão inclusos <b>{dados.garantia_dias} dias</b> de garantia após a entrega, para "
            "correção de defeitos e ajustes dentro do escopo acordado.", e["corpo"]))
        flow.append(Spacer(1, 14))

    # Propriedade e confidencialidade
    flow.append(c.secao("Propriedade e Confidencialidade", e))
    flow.append(Spacer(1, 8))
    flow.append(Paragraph(
        "Após a quitação integral, todo o código e os artefatos produzidos pertencem ao cliente. "
        "As informações e dados compartilhados são tratados de forma confidencial e usados "
        "exclusivamente para a execução deste projeto.", e["corpo"]))
    flow.append(Spacer(1, 14))

    # Validade
    flow.append(c.secao("Validade da Proposta", e))
    flow.append(Spacer(1, 8))
    flow.append(Paragraph(
        f"Esta proposta é válida até <b>{dados.validade_formatada}</b>. Após essa data, valores "
        "e prazos podem ser revistos.", e["corpo"]))

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
        eyebrow="Proposta Comercial",
        titulo=formatar_titulo(dados.nome_projeto),
        profissional=dados.profissional, cargo=dados.cargo, contato=dados.contato,
        titulo_pdf=f"Proposta — {dados.nome_projeto}",
        foto_path=dados.foto_path, numero=dados.numero,
    )
