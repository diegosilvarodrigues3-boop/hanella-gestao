import pandas as pd
import numpy as np


def calcular_dre(df_vendas, df_cp, ano=None):
    if ano:
        vdf = df_vendas[df_vendas["ano"] == ano] if "ano" in df_vendas.columns else df_vendas
        cpdf = df_cp[pd.to_datetime(df_cp["data_lancamento"], errors="coerce").dt.year == ano] if not df_cp.empty else df_cp
    else:
        vdf = df_vendas
        cpdf = df_cp

    receita_bruta = vdf["receita_bruta"].sum() if "receita_bruta" in vdf.columns else 0
    descontos = vdf["desconto"].sum() if "desconto" in vdf.columns else receita_bruta * 0.04
    deducoes = receita_bruta * 0.085  # impostos estimados
    receita_liquida = receita_bruta - descontos - deducoes

    # CMV: prioriza coluna direta na base de vendas
    if "cmv" in vdf.columns and vdf["cmv"].sum() > 0:
        cmv = float(vdf["cmv"].sum())
    elif not cpdf.empty and "tipo_despesa" in cpdf.columns:
        pagas = cpdf[cpdf["status"].isin(["Pago", "pago"])] if "status" in cpdf.columns else cpdf
        cmv_cp = pagas[pagas["tipo_despesa"] == "CMV"]["valor"].sum() if "valor" in pagas.columns else 0
        cmv = float(cmv_cp) if cmv_cp else receita_bruta * 0.40
    else:
        cmv = receita_bruta * 0.40

    despesas_por_tipo = {}
    if not cpdf.empty and "tipo_despesa" in cpdf.columns:
        pagas = cpdf[cpdf["status"].isin(["Pago", "pago"])] if "status" in cpdf.columns else cpdf
        for tipo in ["Marketing", "Pessoal", "Logística", "Aluguel", "Administrativo",
                     "Tecnologia", "Impostos", "Outros"]:
            val = pagas[pagas["tipo_despesa"] == tipo]["valor"].sum() if "valor" in pagas.columns else 0
            despesas_por_tipo[tipo] = float(val) if val else 0
        # Se todas zeradas (CP ainda não preenchido via Form), usa estimativas
        if sum(despesas_por_tipo.values()) == 0:
            despesas_por_tipo = {
                "Marketing": receita_liquida * 0.07, "Pessoal": receita_liquida * 0.12,
                "Logística": receita_liquida * 0.05, "Aluguel": receita_liquida * 0.04,
                "Administrativo": receita_liquida * 0.03, "Tecnologia": receita_liquida * 0.015,
                "Impostos": receita_liquida * 0.02, "Outros": receita_liquida * 0.01,
            }
    else:
        despesas_por_tipo = {
            "Marketing": receita_liquida * 0.07, "Pessoal": receita_liquida * 0.12,
            "Logística": receita_liquida * 0.05, "Aluguel": receita_liquida * 0.04,
            "Administrativo": receita_liquida * 0.03, "Tecnologia": receita_liquida * 0.015,
            "Impostos": receita_liquida * 0.02, "Outros": receita_liquida * 0.01,
        }

    lucro_bruto = receita_liquida - cmv
    total_desp_op = sum(despesas_por_tipo.values())
    ebitda = lucro_bruto - total_desp_op
    depreciacao = receita_bruta * 0.008
    ebit = ebitda - depreciacao
    resultado_financeiro = -receita_bruta * 0.005
    lair = ebit + resultado_financeiro
    ir_csll = max(0, lair * 0.25)
    lucro_liquido = lair - ir_csll

    dre_waterfall = {
        "Receita Bruta": receita_bruta,
        "(-) Deduções": -(deducoes + descontos),
        "= Receita Líquida": receita_liquida,
        "(-) CMV": -cmv,
        "= Lucro Bruto": lucro_bruto,
        "(-) Despesas Op.": -total_desp_op,
        "= EBITDA": ebitda,
        "(-) Depreciação": -depreciacao,
        "= EBIT": ebit,
        "Res. Financeiro": resultado_financeiro,
        "(-) IR/CSLL": -ir_csll,
        "= Lucro Líquido": lucro_liquido,
    }

    dre_tabela = {
        "RECEITA BRUTA DE VENDAS": receita_bruta,
        "(-) Deduções e Descontos": -(deducoes + descontos),
        "= RECEITA LÍQUIDA": receita_liquida,
        "(-) CMV": -cmv,
        "= LUCRO BRUTO": lucro_bruto,
        "Margem Bruta (%)": (lucro_bruto / receita_liquida * 100) if receita_liquida else 0,
        **{f"  (-) {k}": -v for k, v in despesas_por_tipo.items()},
        "(-) Total Despesas Op.": -total_desp_op,
        "= EBITDA": ebitda,
        "Margem EBITDA (%)": (ebitda / receita_liquida * 100) if receita_liquida else 0,
        "(-) Depreciação": -depreciacao,
        "= EBIT": ebit,
        "Resultado Financeiro": resultado_financeiro,
        "= LAIR": lair,
        "(-) IR/CSLL (25%)": -ir_csll,
        "= LUCRO LÍQUIDO": lucro_liquido,
        "Margem Líquida (%)": (lucro_liquido / receita_liquida * 100) if receita_liquida else 0,
    }

    return dre_waterfall, dre_tabela, despesas_por_tipo


def calcular_indicadores(df_vendas, df_cp, df_cr):
    ind = {}

    if not df_vendas.empty:
        ind["receita_bruta"] = df_vendas["receita_bruta"].sum() if "receita_bruta" in df_vendas.columns else 0
        ind["receita_liquida"] = df_vendas["receita_liquida"].sum() if "receita_liquida" in df_vendas.columns else ind["receita_bruta"] * 0.91
        ind["pares_vendidos"] = int(df_vendas["quantidade"].sum()) if "quantidade" in df_vendas.columns else len(df_vendas)
        ind["ticket_medio"] = ind["receita_bruta"] / ind["pares_vendidos"] if ind["pares_vendidos"] else 0
        ind["num_transacoes"] = len(df_vendas)
        ind["lucro_bruto"] = df_vendas["lucro_bruto"].sum() if "lucro_bruto" in df_vendas.columns else ind["receita_liquida"] * 0.40
        ind["margem_bruta"] = (ind["lucro_bruto"] / ind["receita_liquida"] * 100) if ind["receita_liquida"] else 0
    else:
        for k in ["receita_bruta", "receita_liquida", "pares_vendidos", "ticket_medio",
                  "num_transacoes", "lucro_bruto", "margem_bruta"]:
            ind[k] = 0

    if not df_cp.empty and "valor" in df_cp.columns:
        pagas = df_cp[df_cp["status"].isin(["Pago", "pago"])] if "status" in df_cp.columns else df_cp
        em_aberto = df_cp[df_cp["status"].isin(["Em aberto", "Vencido"])] if "status" in df_cp.columns else pd.DataFrame()
        ind["total_pago"] = pagas["valor"].sum()
        ind["total_a_pagar"] = em_aberto["valor"].sum() if not em_aberto.empty else 0
        ind["contas_vencidas"] = df_cp[df_cp["status"] == "Vencido"]["valor"].sum() if "status" in df_cp.columns else 0
    else:
        ind["total_pago"] = 0
        ind["total_a_pagar"] = 0
        ind["contas_vencidas"] = 0

    if not df_cr.empty and "valor" in df_cr.columns:
        recebidas = df_cr[df_cr["status"].isin(["Recebido", "recebido"])] if "status" in df_cr.columns else df_cr
        a_receber = df_cr[df_cr["status"].isin(["A receber", "Atrasado"])] if "status" in df_cr.columns else pd.DataFrame()
        ind["total_recebido"] = recebidas["valor"].sum()
        ind["total_a_receber"] = a_receber["valor"].sum() if not a_receber.empty else 0
    else:
        ind["total_recebido"] = 0
        ind["total_a_receber"] = 0

    ind["pct_despesa_receita"] = (ind["total_pago"] / ind["receita_liquida"] * 100) if ind["receita_liquida"] else 0
    ind["resultado_operacional"] = ind["receita_liquida"] - ind["total_pago"]

    return ind
