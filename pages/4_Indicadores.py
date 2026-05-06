import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

st.set_page_config(page_title="Indicadores", page_icon="📈", layout="wide")

from utils.data_loader import carregar_todos_dados
from utils.metricas import calcular_indicadores
from utils.charts import CORES, LAYOUT_BASE

vendas, cp, cr, usando_demo = carregar_todos_dados()

with st.sidebar:
    st.markdown("## 📈 Indicadores")
    anos = sorted(vendas["ano"].unique().tolist()) if "ano" in vendas.columns else [2025]
    ano_sel = st.selectbox("Ano base", anos, index=len(anos)-1)
    comparar = st.checkbox("Comparar com ano anterior", value=True)

st.markdown("# 📈 Indicadores Operacionais e de Vendas")
if usando_demo:
    st.info("Dados de demonstração.", icon="ℹ️")

df_ano = vendas[vendas["ano"] == ano_sel] if "ano" in vendas.columns else vendas
ind = calcular_indicadores(df_ano, cp, cr)

if comparar and len(anos) > 1:
    ano_ant = anos[max(0, len(anos) - 2)]
    df_ant = vendas[vendas["ano"] == ano_ant] if "ano" in vendas.columns else pd.DataFrame()
    ind_ant = calcular_indicadores(df_ant, cp, cr) if not df_ant.empty else {}
else:
    ind_ant = {}

def delta_pct(atual, anterior):
    if not anterior or anterior == 0:
        return None
    return ((atual - anterior) / abs(anterior)) * 100


def gauge(title, value, min_v, max_v, threshold_ok, threshold_warn, fmt="%"):
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=value,
        number={"suffix": fmt, "font": {"color": "white", "size": 28}},
        title={"text": title, "font": {"color": "white", "size": 14}},
        gauge={
            "axis": {"range": [min_v, max_v], "tickcolor": "white"},
            "bar": {"color": CORES["primaria"]},
            "bgcolor": "#222",
            "steps": [
                {"range": [min_v, threshold_warn], "color": "#330000"},
                {"range": [threshold_warn, threshold_ok], "color": "#332200"},
                {"range": [threshold_ok, max_v], "color": "#003300"},
            ],
            "threshold": {"line": {"color": CORES["neutro"], "width": 3},
                          "thickness": 0.75, "value": threshold_ok}
        }
    ))
    fig.update_layout(paper_bgcolor="#1A1A1A", font=dict(color="white"),
                      height=220, margin=dict(l=20, r=20, t=40, b=10))
    return fig


# ── KPIs principais ───────────────────────────────────────────────────────────
st.markdown("### 🎯 Principais KPIs")
c1, c2, c3, c4, c5, c6 = st.columns(6)

kpis = [
    (c1, "Pares Vendidos", ind["pares_vendidos"],
     ind_ant.get("pares_vendidos"), "{:,}", False),
    (c2, "Receita Bruta", ind["receita_bruta"],
     ind_ant.get("receita_bruta"), "R$ {:,.0f}", False),
    (c3, "Ticket Médio", ind["ticket_medio"],
     ind_ant.get("ticket_medio"), "R$ {:,.2f}", False),
    (c4, "Margem Bruta", ind["margem_bruta"],
     ind_ant.get("margem_bruta"), "{:.1f}%", False),
    (c5, "% Despesa/Receita", ind["pct_despesa_receita"],
     ind_ant.get("pct_despesa_receita"), "{:.1f}%", True),
    (c6, "Resultado Op.", ind["resultado_operacional"],
     ind_ant.get("resultado_operacional"), "R$ {:,.0f}", False),
]

for col, label, val, val_ant, fmt, inverso in kpis:
    d = delta_pct(val, val_ant)
    d_str = None
    if d is not None:
        sinal = "▲" if d >= 0 else "▼"
        d_str = f"{sinal} {abs(d):.1f}% vs {ano_sel-1}"
    col.metric(label, fmt.format(val), d_str)

st.markdown("---")

# ── Gauges ────────────────────────────────────────────────────────────────────
st.markdown("### 🔢 Gauges de Desempenho")
g1, g2, g3, g4 = st.columns(4)

with g1:
    st.plotly_chart(gauge("Margem Bruta (%)", ind["margem_bruta"], 0, 70, 40, 25), use_container_width=True)
with g2:
    st.plotly_chart(gauge("% Despesa/Receita", ind["pct_despesa_receita"], 0, 100, 60, 75, "%"), use_container_width=True)
with g3:
    ebitda_margin = max(0, (ind["resultado_operacional"] / ind["receita_liquida"] * 100) if ind["receita_liquida"] else 0)
    st.plotly_chart(gauge("Margem EBITDA (%)", min(ebitda_margin, 40), 0, 40, 15, 8), use_container_width=True)
with g4:
    tick = min(ind["ticket_medio"], 600)
    st.plotly_chart(gauge("Ticket Médio (R$)", tick, 0, 600, 350, 200, ""), use_container_width=True)

st.markdown("---")

# ── Evolução de indicadores ───────────────────────────────────────────────────
st.markdown("### 📉 Evolução Mensal de Indicadores")

if "mes" in df_ano.columns:
    mensal = df_ano.groupby("mes").agg(
        receita=("receita_bruta", "sum"),
        pares=("quantidade", "sum") if "quantidade" in df_ano.columns else ("receita_bruta", "count"),
        lucro_bruto=("lucro_bruto", "sum") if "lucro_bruto" in df_ano.columns else ("receita_bruta", lambda x: x.sum()*0.40),
        receita_liq=("receita_liquida", "sum") if "receita_liquida" in df_ano.columns else ("receita_bruta", lambda x: x.sum()*0.91),
    ).reset_index()
    mensal["mes_str"] = mensal["mes"].astype(str)
    mensal["margem_bruta_pct"] = (mensal["lucro_bruto"] / mensal["receita_liq"] * 100).round(1)
    mensal["ticket"] = (mensal["receita"] / mensal["pares"]).round(2)

    tab1, tab2, tab3 = st.tabs(["Pares Vendidos", "Margem Bruta %", "Ticket Médio"])

    with tab1:
        fig = go.Figure()
        fig.add_trace(go.Bar(x=mensal["mes_str"], y=mensal["pares"],
                             marker_color=CORES["primaria"],
                             text=mensal["pares"].apply(lambda x: f"{int(x):,}"),
                             textposition="outside"))
        fig.update_layout(**LAYOUT_BASE, height=350, title="Pares Vendidos por Mês")
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=mensal["mes_str"], y=mensal["margem_bruta_pct"],
                                  mode="lines+markers+text",
                                  line=dict(color=CORES["positivo"], width=3),
                                  marker=dict(size=8),
                                  text=mensal["margem_bruta_pct"].apply(lambda x: f"{x:.1f}%"),
                                  textposition="top center"))
        fig.add_hline(y=40, line_dash="dash", line_color=CORES["neutro"],
                      annotation_text="Meta 40%", annotation_font_color=CORES["neutro"])
        fig.update_layout(**LAYOUT_BASE, height=350, title="Margem Bruta % por Mês")
        st.plotly_chart(fig, use_container_width=True)

    with tab3:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=mensal["mes_str"], y=mensal["ticket"],
                                  mode="lines+markers",
                                  line=dict(color=CORES["secundaria"], width=3),
                                  marker=dict(size=8),
                                  fill="tozeroy", fillcolor="rgba(200,16,46,0.1)"))
        fig.update_layout(**LAYOUT_BASE, height=350, title="Ticket Médio por Mês (R$)")
        st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# ── Análise por UF / Região ───────────────────────────────────────────────────
if "uf" in df_ano.columns:
    st.markdown("### 🗺️ Análise por Estado")
    uf_data = df_ano.groupby("uf").agg(
        receita=("receita_bruta", "sum"),
        pares=("quantidade", "sum") if "quantidade" in df_ano.columns else ("receita_bruta", "count")
    ).sort_values("receita", ascending=False).reset_index()

    col_uf1, col_uf2 = st.columns(2)
    with col_uf1:
        fig_uf = px.bar(uf_data, x="uf", y="receita", color="receita",
                        color_continuous_scale=[[0, "#8B0000"], [1, "#C8102E"]],
                        text=uf_data["receita"].apply(lambda x: f"R$ {x/1000:.0f}k"),
                        labels={"uf": "Estado", "receita": "Receita (R$)"})
        fig_uf.update_traces(textposition="outside")
        fig_uf.update_layout(paper_bgcolor="#1A1A1A", plot_bgcolor="#1A1A1A",
                              font=dict(color="white"), height=320, showlegend=False,
                              coloraxis_showscale=False,
                              title="Receita por Estado")
        st.plotly_chart(fig_uf, use_container_width=True)
    with col_uf2:
        st.dataframe(
            uf_data.style.format({"receita": "R$ {:,.2f}", "pares": "{:,}"}),
            hide_index=True, use_container_width=True, height=300
        )

# ── Análise por Vendedor ──────────────────────────────────────────────────────
if "vendedor" in df_ano.columns:
    st.markdown("### 👤 Ranking de Vendedores")
    vend = df_ano.groupby("vendedor").agg(
        receita=("receita_bruta", "sum"),
        pares=("quantidade", "sum") if "quantidade" in df_ano.columns else ("receita_bruta", "count"),
        transacoes=("receita_bruta", "count")
    ).sort_values("receita", ascending=False).reset_index()
    vend["ticket_medio"] = (vend["receita"] / vend["pares"]).round(2)
    vend["share_pct"] = (vend["receita"] / vend["receita"].sum() * 100).round(1)

    fig_vend = px.bar(vend, x="vendedor", y="receita",
                      color="receita", color_continuous_scale=[[0, "#8B0000"], [1, "#C8102E"]],
                      text=vend["receita"].apply(lambda x: f"R$ {x/1000:.0f}k"))
    fig_vend.update_traces(textposition="outside")
    fig_vend.update_layout(paper_bgcolor="#1A1A1A", plot_bgcolor="#1A1A1A",
                            font=dict(color="white"), height=340, showlegend=False,
                            coloraxis_showscale=False, title="Receita por Vendedor")
    st.plotly_chart(fig_vend, use_container_width=True)

    st.dataframe(
        vend.style.format({
            "receita": "R$ {:,.2f}", "pares": "{:,}",
            "ticket_medio": "R$ {:,.2f}", "share_pct": "{:.1f}%"
        }),
        hide_index=True, use_container_width=True
    )
