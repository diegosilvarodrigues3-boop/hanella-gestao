import streamlit as st
import pandas as pd
import os, sys

sys.path.insert(0, os.path.dirname(__file__))

st.set_page_config(
    page_title="Hanella — Gestão",
    page_icon="👟",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    /* Dark theme base */
    .stApp { background-color: #0D0D0D; }
    div[data-testid="stSidebar"] {
        background: #111111;
        border-right: 1px solid #222222;
    }

    /* KPI Cards */
    .kpi-card {
        background: #1C1C1C;
        border: 1px solid #2A2A2A;
        border-radius: 14px;
        padding: 18px 16px;
        text-align: center;
    }
    .kpi-value { font-size: 1.7rem; font-weight: 700; color: #C9A84C; line-height: 1.2; }
    .kpi-label { font-size: 0.72rem; color: #666; margin-top: 4px; text-transform: uppercase; letter-spacing: 0.6px; }
    .pos { color: #4CAF82; } .neg { color: #E05252; }

    /* Filtro */
    .filter-label { font-size: 0.72rem; color: #555; text-transform: uppercase; letter-spacing: 0.6px; margin-bottom: 4px; }

    /* Divisor */
    hr { border: none; border-top: 1px solid #222; margin: 16px 0; }

    /* Tabs */
    .stTabs [data-baseweb="tab"] { color: #555; }
    .stTabs [data-baseweb="tab"][aria-selected="true"] { color: #C9A84C; border-bottom: 2px solid #C9A84C; }

    /* Títulos */
    h1, h2, h3 { color: #F0F0F0 !important; }

    .block-container { padding-top: 1.5rem !important; }
    .footer { text-align: center; color: #444; font-size: 0.75rem; padding: 12px 0; }
</style>
""", unsafe_allow_html=True)

from utils.data_loader import carregar_todos_dados
from utils.metricas import calcular_indicadores

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 📂 Base de Vendas")
    arquivo = st.file_uploader("Upload Excel/CSV (Vol&Mix)", type=["xlsx", "xls", "csv"], key="vendas_upload")
    st.markdown("---")
    st.markdown("### 🔗 Lançamentos")
    st.markdown("""
[📤 Contas a Pagar](https://docs.google.com/forms/d/e/1FAIpQLScibj5eQHjaL33CzlajW7spAjOppZhgXz-rXqVFvzoysXCisw/viewform)

[📥 Contas a Receber](https://docs.google.com/forms/d/e/1FAIpQLSfZDvLRZAZXNF_2LNe5sw7fwW9IzQkZaOUcoeuS0u1pj90J5A/viewform)
""")
    st.markdown("---")
    filtro_ano = st.selectbox("Ano", [2025, 2024, 2023], index=0)
    if st.button("🔄 Atualizar dados"):
        st.cache_data.clear()
        st.rerun()

# ── Dados ─────────────────────────────────────────────────────────────────────
vendas, cp, cr, usando_demo = carregar_todos_dados(arquivo)

# ── Header com Logo ───────────────────────────────────────────────────────────
LOGO_PATH = os.path.join(os.path.dirname(__file__), "assets", "logo.png")
col_logo, col_titulo, col_spacer = st.columns([1, 5, 2])

with col_logo:
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, width=90)

with col_titulo:
    st.markdown("""
    <div style='padding-top:10px;'>
        <div style='font-size:1.6rem;font-weight:700;color:#F0F0F0;line-height:1.1;'>Central de Gestão</div>
        <div style='font-size:0.82rem;color:#666;margin-top:3px;'>Resultado Financeiro · Vendas · Indicadores Operacionais</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<hr>", unsafe_allow_html=True)

# ── Filtro central de meses ───────────────────────────────────────────────────
NOMES_MESES = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
               "Jul", "Ago", "Set", "Out", "Nov", "Dez"]

meses_disponiveis = sorted(
    vendas[vendas["ano"] == filtro_ano]["data"].dt.month.dropna().unique().tolist()
) if "data" in vendas.columns and "ano" in vendas.columns else list(range(1, 13))

st.markdown("<div class='filter-label'>Filtrar por período</div>", unsafe_allow_html=True)
fcol1, fcol2 = st.columns([3, 1])
with fcol1:
    filtro_mes = st.multiselect(
        "Meses",
        options=meses_disponiveis,
        default=meses_disponiveis,
        format_func=lambda m: NOMES_MESES[m - 1],
        label_visibility="collapsed",
        key="filtro_meses_central"
    )
with fcol2:
    st.markdown(f"<div style='padding-top:8px;font-size:0.82rem;color:#999;'>{len(filtro_mes)} de {len(meses_disponiveis)} meses selecionados</div>", unsafe_allow_html=True)

st.markdown("<hr>", unsafe_allow_html=True)

# ── Aplicar filtros ───────────────────────────────────────────────────────────
vendas_ano = vendas[vendas["ano"] == filtro_ano].copy() if "ano" in vendas.columns else vendas.copy()
if filtro_mes and "data" in vendas_ano.columns:
    vendas_ano = vendas_ano[vendas_ano["data"].dt.month.isin(filtro_mes)]

if usando_demo:
    st.info("Modo demonstração — importe sua base de vendas ou conecte ao Google Sheets.", icon="ℹ️")

# ── KPIs ──────────────────────────────────────────────────────────────────────
ind = calcular_indicadores(vendas_ano, cp, cr)

def kpi(col, label, valor, fmt="moeda"):
    if fmt == "moeda":  v_str = f"R$ {valor:,.0f}"
    elif fmt == "int":  v_str = f"{int(valor):,}"
    elif fmt == "pct":  v_str = f"{valor:.1f}%"
    else:               v_str = str(valor)
    col.markdown(f"""
    <div class='kpi-card'>
        <div class='kpi-value'>{v_str}</div>
        <div class='kpi-label'>{label}</div>
    </div>""", unsafe_allow_html=True)

c1, c2, c3, c4, c5, c6 = st.columns(6)
kpi(c1, "Receita Bruta",      ind["receita_bruta"])
kpi(c2, "Receita Líquida",    ind["receita_liquida"])
kpi(c3, "Lucro Bruto",        ind["lucro_bruto"])
kpi(c4, "Pares Vendidos",     ind["pares_vendidos"],      "int")
kpi(c5, "Margem Bruta",       ind["margem_bruta"],        "pct")
kpi(c6, "Ticket Médio",       ind["ticket_medio"])

st.markdown("<br>", unsafe_allow_html=True)
c7, c8, c9 = st.columns(3)
kpi(c7, "Total Pago (Despesas)", ind["total_pago"])
kpi(c8, "A Receber",             ind["total_a_receber"])
kpi(c9, "% Despesa / Receita",   ind["pct_despesa_receita"], "pct")

st.markdown("<hr>", unsafe_allow_html=True)

# ── Gráficos ──────────────────────────────────────────────────────────────────
from utils.charts import (grafico_receita_mensal, grafico_canal_pizza,
                           grafico_mix_categoria, grafico_evolucao_resultado)

col_g1, col_g2 = st.columns([2, 1])
with col_g1:
    st.plotly_chart(grafico_receita_mensal(vendas_ano), use_container_width=True)
with col_g2:
    st.plotly_chart(grafico_canal_pizza(vendas_ano), use_container_width=True)

st.plotly_chart(grafico_mix_categoria(vendas_ano), use_container_width=True)
st.plotly_chart(grafico_evolucao_resultado(vendas_ano, cp), use_container_width=True)

st.markdown("<div class='footer'>Hanella Gestão • Atualizado a cada 5 min</div>", unsafe_allow_html=True)
