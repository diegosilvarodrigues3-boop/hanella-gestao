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
    /* Fundo geral */
    .stApp { background-color: #F7F7F7; }

    /* Sidebar clean */
    div[data-testid="stSidebar"] {
        background: #FFFFFF;
        border-right: 1px solid #E8E8E8;
    }
    div[data-testid="stSidebar"] * { color: #1A1A1A !important; }

    /* Cards de KPI */
    .kpi-card {
        background: #FFFFFF;
        border: 1px solid #EBEBEB;
        border-radius: 14px;
        padding: 18px 16px;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    }
    .kpi-value { font-size: 1.7rem; font-weight: 700; color: #C8102E; line-height: 1.2; }
    .kpi-label { font-size: 0.75rem; color: #888; margin-top: 4px; text-transform: uppercase; letter-spacing: 0.5px; }
    .kpi-delta { font-size: 0.78rem; margin-top: 5px; }
    .pos { color: #1DB954; } .neg { color: #E53935; }

    /* Header */
    .header-bar {
        display: flex;
        align-items: center;
        gap: 16px;
        padding: 18px 24px;
        background: #FFFFFF;
        border-radius: 14px;
        border: 1px solid #EBEBEB;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }
    .header-title { font-size: 1.5rem; font-weight: 700; color: #1A1A1A; margin: 0; }
    .header-sub { font-size: 0.82rem; color: #999; margin: 2px 0 0 0; }
    .red-dot { width: 10px; height: 10px; border-radius: 50%; background: #C8102E; display: inline-block; margin-right: 4px; }

    /* Filtro central */
    .filter-bar {
        background: #FFFFFF;
        border: 1px solid #EBEBEB;
        border-radius: 12px;
        padding: 14px 20px;
        margin-bottom: 20px;
        box-shadow: 0 1px 4px rgba(0,0,0,0.04);
    }
    .filter-label { font-size: 0.72rem; color: #999; text-transform: uppercase; letter-spacing: 0.6px; margin-bottom: 6px; }

    /* Divisor */
    hr { border: none; border-top: 1px solid #EBEBEB; margin: 16px 0; }

    /* Tabs */
    .stTabs [data-baseweb="tab"] { color: #888; }
    .stTabs [data-baseweb="tab"][aria-selected="true"] { color: #C8102E; border-bottom: 2px solid #C8102E; }

    /* Remover padding excessivo do main */
    .block-container { padding-top: 1.5rem !important; }

    /* Rodapé */
    .footer { text-align: center; color: #BBB; font-size: 0.75rem; padding: 12px 0; }
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
        st.image(LOGO_PATH, width=80)
    else:
        st.markdown("""
        <div style='background:#C8102E;border-radius:10px;width:64px;height:64px;
        display:flex;align-items:center;justify-content:center;margin-top:4px;'>
        <span style='color:white;font-size:1.6rem;'>👟</span></div>
        """, unsafe_allow_html=True)

with col_titulo:
    st.markdown("""
    <div style='padding-top:6px;'>
        <div style='font-size:1.6rem;font-weight:700;color:#1A1A1A;line-height:1.1;'>Hanella</div>
        <div style='font-size:0.82rem;color:#999;margin-top:2px;'>Central de Gestão · Resultado Financeiro & Vendas</div>
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
