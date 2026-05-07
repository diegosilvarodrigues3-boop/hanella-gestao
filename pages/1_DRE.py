import streamlit as st
import pandas as pd
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

st.set_page_config(page_title="DRE", page_icon="💰", layout="wide")

st.markdown("""
<style>
.dre-row { display:flex; justify-content:space-between; padding:6px 12px; border-radius:6px; margin:2px 0; }
.dre-total { background:#8B733622; font-weight:700; font-size:1.05rem; }
.dre-subtotal { background:#F0EDE655; font-weight:600; }
.dre-item { color:#555; font-size:0.92rem; }
.dre-margem { color:#8B7336; font-style:italic; font-weight:600; }
.pos { color:#00C853; } .neg { color:#FF1744; }
</style>""", unsafe_allow_html=True)

from utils.data_loader import carregar_todos_dados
from utils.metricas import calcular_dre
from utils.charts import grafico_dre_waterfall, grafico_despesas_tipo

vendas, cp, cr, usando_demo = carregar_todos_dados()

with st.sidebar:
    st.markdown("## 💰 DRE")
    ano = st.selectbox("Período", [2025, 2024, 2023])
    st.markdown("---")
    if st.button("🔄 Recarregar dados"):
        st.cache_data.clear()
        st.rerun()

st.markdown("# 💰 DRE — Demonstração do Resultado")
if usando_demo:
    st.info("Dados de demonstração. Conecte ao Google Sheets para dados reais.", icon="ℹ️")

dre_wf, dre_tab, despesas_tipo = calcular_dre(vendas, cp, ano)

# Waterfall
st.plotly_chart(grafico_dre_waterfall(dre_wf), use_container_width=True)

st.markdown("---")
col_dre, col_desp = st.columns([1, 1])

# Tabela DRE
with col_dre:
    st.markdown("### 📋 DRE Detalhada")
    TOTAIS = ["RECEITA BRUTA DE VENDAS", "= RECEITA LÍQUIDA", "= LUCRO BRUTO",
              "(-) Total Despesas Op.", "= EBITDA", "= EBIT", "= LAIR", "= LUCRO LÍQUIDO"]
    MARGENS = ["Margem Bruta (%)", "Margem EBITDA (%)", "Margem Líquida (%)"]

    receita_liq = dre_tab.get("= RECEITA LÍQUIDA", 1)

    for linha, valor in dre_tab.items():
        if linha in MARGENS:
            css = "dre-margem"
            v_str = f"{valor:.1f}%"
        elif linha in TOTAIS:
            css = "dre-total"
            cor = "pos" if valor >= 0 else "neg"
            v_str = f"<span class='{cor}'>R$ {valor:,.2f}</span>"
        else:
            css = "dre-item"
            cor = "pos" if valor >= 0 else "neg"
            v_str = f"<span class='{cor}'>R$ {valor:,.2f}</span>"

        if linha in MARGENS:
            st.markdown(f"<div class='dre-row {css}'><span>{linha}</span><span style='color:#FFC107'>{v_str}</span></div>",
                        unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='dre-row {css}'><span>{linha}</span>{v_str}</div>",
                        unsafe_allow_html=True)

with col_desp:
    st.markdown("### 📊 Composição das Despesas")
    st.plotly_chart(grafico_despesas_tipo(cp), use_container_width=True)

    # Mini tabela despesas
    st.markdown("#### Detalhamento por Tipo")
    df_desp = pd.DataFrame([
        {"Tipo": k, "Valor (R$)": v, "% Receita": (v / receita_liq * 100) if receita_liq else 0}
        for k, v in despesas_tipo.items() if v > 0
    ]).sort_values("Valor (R$)", ascending=False)
    st.dataframe(
        df_desp.style.format({"Valor (R$)": "R$ {:,.2f}", "% Receita": "{:.1f}%"}),
        hide_index=True, use_container_width=True
    )

# Export
st.markdown("---")
col_e1, col_e2 = st.columns(2)
with col_e1:
    dre_export = pd.DataFrame([
        {"Linha DRE": k, "Valor (R$)": v}
        for k, v in dre_tab.items()
    ])
    st.download_button(
        "⬇️ Exportar DRE (Excel)",
        data=dre_export.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig"),
        file_name=f"DRE_{ano}.csv",
        mime="text/csv"
    )
