import streamlit as st
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

st.set_page_config(
    page_title="Gestão Marca de Sapatos",
    page_icon="👟",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS global
st.markdown("""
<style>
    .metric-card {
        background: #1A1A1A;
        border: 1px solid #333;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
    }
    .metric-value { font-size: 2rem; font-weight: 700; color: #C8102E; }
    .metric-label { font-size: 0.85rem; color: #999; margin-top: 4px; }
    .metric-delta { font-size: 0.8rem; margin-top: 4px; }
    .positive { color: #00C853; }
    .negative { color: #FF1744; }
    .section-header {
        font-size: 1.3rem; font-weight: 600;
        border-left: 4px solid #C8102E;
        padding-left: 12px; margin: 20px 0 12px 0;
    }
    div[data-testid="stSidebar"] { background: #111; }
    .banner {
        background: linear-gradient(135deg, #C8102E 0%, #8B0000 100%);
        padding: 20px 30px; border-radius: 12px; margin-bottom: 20px;
    }
    .stTabs [data-baseweb="tab"] { color: #ccc; }
    .stTabs [data-baseweb="tab"][aria-selected="true"] { color: #C8102E; border-bottom: 2px solid #C8102E; }
</style>
""", unsafe_allow_html=True)

from utils.data_loader import carregar_todos_dados
from utils.metricas import calcular_indicadores

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 👟 Hanella")
    st.markdown("---")

    st.markdown("### 📂 Base de Vendas")
    arquivo = st.file_uploader("Upload Excel/CSV (formato Vol&Mix)", type=["xlsx", "xls", "csv"], key="vendas_upload")

    st.markdown("---")
    st.markdown("### 🔗 Google Forms")
    st.markdown("""
**Contas a Pagar:**
[📝 Abrir formulário](#)

**Contas a Receber:**
[📝 Abrir formulário](#)

*(configure os links após criar os Forms)*
""")
    st.markdown("---")
    st.markdown("### 🎛️ Filtros")
    filtro_ano = st.selectbox("Ano", [2025, 2024, 2023], index=0)
    filtro_mes = st.multiselect("Mês", list(range(1, 13)),
                                format_func=lambda m: ["Jan","Fev","Mar","Abr","Mai","Jun",
                                                        "Jul","Ago","Set","Out","Nov","Dez"][m-1])

# ── Carregar dados ────────────────────────────────────────────────────────────
vendas, cp, cr, usando_demo = carregar_todos_dados(arquivo)

if filtro_mes and "data" in vendas.columns:
    vendas = vendas[vendas["data"].dt.month.isin(filtro_mes)]
if "data" in vendas.columns and "ano" in vendas.columns:
    vendas_ano = vendas[vendas["ano"] == filtro_ano]
else:
    vendas_ano = vendas

if usando_demo:
    st.info("🎯 **Modo demonstração** — dados fictícios. Conecte ao Google Sheets ou importe sua base de vendas para dados reais.", icon="ℹ️")

# ── Banner ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class='banner'>
    <h1 style='margin:0;color:white;font-size:2rem;'>👟 Central de Gestão</h1>
    <p style='margin:4px 0 0;color:rgba(255,255,255,0.8);'>Resultado Financeiro · Vendas · Operacional</p>
</div>
""", unsafe_allow_html=True)

# ── KPIs principais ───────────────────────────────────────────────────────────
ind = calcular_indicadores(vendas_ano, cp, cr)

col1, col2, col3, col4, col5, col6 = st.columns(6)

def kpi(col, label, valor, formato="moeda", delta=None):
    if formato == "moeda":
        v_str = f"R$ {valor:,.0f}"
    elif formato == "int":
        v_str = f"{int(valor):,}"
    elif formato == "pct":
        v_str = f"{valor:.1f}%"
    else:
        v_str = str(valor)

    delta_html = ""
    if delta is not None:
        cls = "positive" if delta >= 0 else "negative"
        sinal = "▲" if delta >= 0 else "▼"
        delta_html = f"<div class='metric-delta {cls}'>{sinal} {abs(delta):.1f}%</div>"

    col.markdown(f"""
    <div class='metric-card'>
        <div class='metric-value'>{v_str}</div>
        <div class='metric-label'>{label}</div>
        {delta_html}
    </div>""", unsafe_allow_html=True)

kpi(col1, "Receita Bruta", ind["receita_bruta"])
kpi(col2, "Receita Líquida", ind["receita_liquida"])
kpi(col3, "Lucro Bruto", ind["lucro_bruto"])
kpi(col4, "Pares Vendidos", ind["pares_vendidos"], "int")
kpi(col5, "Margem Bruta", ind["margem_bruta"], "pct")
kpi(col6, "Ticket Médio", ind["ticket_medio"])

st.markdown("<br>", unsafe_allow_html=True)

col_a, col_b, col_c = st.columns(3)
kpi(col_a, "Total Pago (Despesas)", ind["total_pago"])
kpi(col_b, "A Receber", ind["total_a_receber"])
kpi(col_c, "% Despesa / Receita", ind["pct_despesa_receita"], "pct")

st.markdown("---")

# ── Gráficos principais ───────────────────────────────────────────────────────
from utils.charts import (grafico_receita_mensal, grafico_canal_pizza,
                           grafico_mix_categoria, grafico_evolucao_resultado)

col_g1, col_g2 = st.columns([2, 1])
with col_g1:
    st.plotly_chart(grafico_receita_mensal(vendas_ano), use_container_width=True)
with col_g2:
    st.plotly_chart(grafico_canal_pizza(vendas_ano), use_container_width=True)

st.plotly_chart(grafico_mix_categoria(vendas_ano), use_container_width=True)
st.plotly_chart(grafico_evolucao_resultado(vendas_ano, cp), use_container_width=True)

# ── Rodapé ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("<p style='text-align:center;color:#555;font-size:0.8rem;'>Gestão Marca de Sapatos • Atualizado automaticamente a cada 5 min</p>",
            unsafe_allow_html=True)
