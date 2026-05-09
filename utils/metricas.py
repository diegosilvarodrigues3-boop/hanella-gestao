import pandas as pd
import numpy as np

# ── Parâmetros financeiros Hanella ────────────────────────────────────────────
TAXA_IMPOSTO = 0.04          # 4% sobre receita bruta
RECOMP_ESTOQUE = 0.0         # a definir — será informado posteriormente


def calcular_dre(df_vendas, df_cp, ano=None):
    if ano:
        vdf  = df_vendas[df_vendas["ano"] == ano] if "ano" in df_vendas.columns else df_vendas
        cpdf = df_cp[pd.to_datetime(df_cp["data_lancamento"], errors="coerce").dt.year == ano] \
               if not df_cp.empty else df_cp
    else:
        vdf  = df_vendas
        cpdf = df_cp

    # ── Receitas ──────────────────────────────────────────────────────────────
    receita_bruta = float(vdf["receita_bruta"].sum()) if "receita_bruta" in vdf.columns else 0.0

    # Deduções:
    #   1. Impostos: 4% fixo sobre receita bruta
    #   2. Recomposição de estoque: a definir (0 por ora)
    impostos         = receita_bruta * TAXA_IMPOSTO
    recomp_estoque   = receita_bruta * RECOMP_ESTOQUE   # será preenchido futuramente
    total_deducoes   = impostos + recomp_estoque

    receita_liquida  = receita_bruta - total_deducoes

    # ── CMV (direto da base de vendas) ────────────────────────────────────────
    if "cmv" in vdf.columns and vdf["cmv"].sum() > 0:
        cmv = float(vdf["cmv"].sum())
    elif not cpdf.empty and "tipo_despesa" in cpdf.columns:
        pagas  = cpdf[cpdf["status"].isin(["Pago","pago"])] if "status" in cpdf.columns else cpdf
        cmv_cp = pagas[pagas["tipo_despesa"] == "CMV"]["valor"].sum() if "valor" in pagas.columns else 0
        cmv    = float(cmv_cp) if cmv_cp else receita_bruta * 0.55
    else:
        cmv = receita_bruta * 0.55

    lucro_bruto = receita_liquida - cmv

    # ── Despesas operacionais (via Contas a Pagar) ────────────────────────────
    despesas_por_tipo = {}
    if not cpdf.empty and "tipo_despesa" in cpdf.columns:
        pagas = cpdf[cpdf["status"].isin(["Pago","pago"])] if "status" in cpdf.columns else cpdf
        for tipo in ["Marketing","Pessoal","Logística","Aluguel",
                     "Administrativo","Tecnologia","Outros"]:
            val = pagas[pagas["tipo_despesa"] == tipo]["valor"].sum() \
                  if "valor" in pagas.columns else 0
            despesas_por_tipo[tipo] = float(val) if val else 0
        if sum(despesas_por_tipo.values()) == 0:
            despesas_por_tipo = _estimativas_despesas(receita_liquida)
    else:
        despesas_por_tipo = _estimativas_despesas(receita_liquida)

    total_desp_op   = sum(despesas_por_tipo.values())
    ebitda          = lucro_bruto - total_desp_op
    depreciacao     = receita_bruta * 0.008
    ebit            = ebitda - depreciacao
    res_financeiro  = 0.0          # sem financiamento a prazo
    lair            = ebit + res_financeiro
    ir_csll         = max(0.0, lair * 0.25)
    lucro_liquido   = lair - ir_csll

    # ── DRE para waterfall ────────────────────────────────────────────────────
    dre_waterfall = {
        "Receita Bruta":      receita_bruta,
        "(-) Impostos 4%":    -impostos,
        "(-) Recomp. Estoque": -recomp_estoque,
        "= Receita Líquida":  receita_liquida,
        "(-) CMV":            -cmv,
        "= Lucro Bruto":      lucro_bruto,
        "(-) Despesas Op.":   -total_desp_op,
        "= EBITDA":           ebitda,
        "(-) Depreciação":    -depreciacao,
        "= EBIT":             ebit,
        "= Lucro Líquido":    lucro_liquido,
    }

    # ── DRE para tabela detalhada ─────────────────────────────────────────────
    dre_tabela = {
        "RECEITA BRUTA":                 receita_bruta,
        "  (-) Impostos (4%)":           -impostos,
        "  (-) Recomp. Estoque":         -recomp_estoque,
        "= RECEITA LÍQUIDA":             receita_liquida,
        "(-) CMV":                       -cmv,
        "= LUCRO BRUTO":                 lucro_bruto,
        "Margem Bruta (%)":              (lucro_bruto / receita_liquida * 100) if receita_liquida else 0,
        **{f"  (-) {k}": -v for k, v in despesas_por_tipo.items()},
        "(-) Total Despesas Op.":        -total_desp_op,
        "= EBITDA":                      ebitda,
        "Margem EBITDA (%)":             (ebitda / receita_liquida * 100) if receita_liquida else 0,
        "(-) Depreciação":               -depreciacao,
        "= EBIT":                        ebit,
        "(-) IR/CSLL (25%)":             -ir_csll,
        "= LUCRO LÍQUIDO":               lucro_liquido,
        "Margem Líquida (%)":            (lucro_liquido / receita_liquida * 100) if receita_liquida else 0,
    }

    return dre_waterfall, dre_tabela, despesas_por_tipo


def _estimativas_despesas(receita_liquida):
    """Estimativas percentuais quando CP não tem dados reais."""
    return {
        "Marketing":      receita_liquida * 0.07,
        "Pessoal":        receita_liquida * 0.12,
        "Logística":      receita_liquida * 0.05,
        "Aluguel":        receita_liquida * 0.04,
        "Administrativo": receita_liquida * 0.03,
        "Tecnologia":     receita_liquida * 0.015,
        "Outros":         receita_liquida * 0.01,
    }


def calcular_indicadores(df_vendas, df_cp, df_cr):
    ind = {}

    if not df_vendas.empty:
        receita_bruta   = float(df_vendas["receita_bruta"].sum()) if "receita_bruta" in df_vendas.columns else 0
        # Receita líquida = bruta - 4% impostos - recomposição (0 por ora)
        receita_liquida = receita_bruta * (1 - TAXA_IMPOSTO - RECOMP_ESTOQUE)

        ind["receita_bruta"]    = receita_bruta
        ind["receita_liquida"]  = receita_liquida
        ind["pares_vendidos"]   = int(df_vendas["quantidade"].sum()) if "quantidade" in df_vendas.columns else len(df_vendas)
        ind["ticket_medio"]     = receita_bruta / ind["pares_vendidos"] if ind["pares_vendidos"] else 0
        ind["num_transacoes"]   = len(df_vendas)
        ind["lucro_bruto"]      = float(df_vendas["lucro_bruto"].sum()) if "lucro_bruto" in df_vendas.columns else receita_liquida * 0.45
        ind["margem_bruta"]     = (ind["lucro_bruto"] / receita_liquida * 100) if receita_liquida else 0
    else:
        for k in ["receita_bruta","receita_liquida","pares_vendidos","ticket_medio",
                  "num_transacoes","lucro_bruto","margem_bruta"]:
            ind[k] = 0

    # Contas a Pagar — todos os lançamentos contam como despesa
    if not df_cp.empty and "valor" in df_cp.columns:
        pagas     = df_cp[df_cp["status"].isin(["Pago","pago"])] if "status" in df_cp.columns else df_cp
        em_aberto = df_cp[df_cp["status"].isin(["Em aberto","Vencido"])] if "status" in df_cp.columns else pd.DataFrame()
        ind["total_pago"]     = float(pagas["valor"].sum())
        ind["total_a_pagar"]  = float(em_aberto["valor"].sum()) if not em_aberto.empty else 0
        ind["contas_vencidas"]= float(df_cp[df_cp["status"] == "Vencido"]["valor"].sum()) if "status" in df_cp.columns else 0
    else:
        ind["total_pago"] = ind["total_a_pagar"] = ind["contas_vencidas"] = 0

    # Contas a Receber — 100% consideradas recebidas (sem prazo)
    if not df_cr.empty and "valor" in df_cr.columns:
        ind["total_recebido"] = float(df_cr["valor"].sum())   # tudo é recebido
        ind["total_a_receber"] = 0                             # não trabalhamos a prazo
    else:
        ind["total_recebido"] = ind["total_a_receber"] = 0

    ind["pct_despesa_receita"]  = (ind["total_pago"] / ind["receita_liquida"] * 100) if ind["receita_liquida"] else 0
    ind["resultado_operacional"]= ind["receita_liquida"] - ind["total_pago"]

    return ind
