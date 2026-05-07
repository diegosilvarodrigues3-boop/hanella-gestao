import streamlit as st
import pandas as pd
import plotly.express as px
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

st.set_page_config(page_title="Análise de Vendas", page_icon="📊", layout="wide")

from utils.data_loader import carregar_todos_dados
from utils.charts import (grafico_mix_categoria, grafico_canal_pizza,
                           grafico_ticket_medio, grafico_receita_mensal,
                           grafico_margem_categoria, grafico_top_produtos, CORES)

vendas, cp, cr, usando_demo = carregar_todos_dados()

with st.sidebar:
    st.markdown("## 📊 Vendas")
    arquivo = st.file_uploader("Importar base de vendas", type=["xlsx", "xls", "csv"])
    if arquivo:
        vendas, cp, cr, usando_demo = carregar_todos_dados(arquivo)
    anos = sorted(vendas["ano"].unique().tolist()) if "ano" in vendas.columns else [2025]
    ano_sel = st.selectbox("Ano", anos, index=len(anos)-1)
    cats = sorted(vendas["categoria"].unique().tolist()) if "categoria" in vendas.columns else []
    cats_sel = st.multiselect("Categorias", cats, default=cats)
    canais = sorted(vendas["canal"].unique().tolist()) if "canal" in vendas.columns else []
    canais_sel = st.multiselect("Canais", canais, default=canais)

st.markdown("# 📊 Análise de Vendas — Volume e Mix")
if usando_demo:
    st.info("Dados de demonstração. Use o upload na barra lateral para sua base real.", icon="ℹ️")

# Filtrar
df = vendas.copy()
if "ano" in df.columns:
    df = df[df["ano"] == ano_sel]
if cats_sel and "categoria" in df.columns:
    df = df[df["categoria"].isin(cats_sel)]
if canais_sel and "canal" in df.columns:
    df = df[df["canal"].isin(canais_sel)]

# KPIs
c1, c2, c3, c4, c5 = st.columns(5)
total_pares = int(df["quantidade"].sum()) if "quantidade" in df.columns else len(df)
receita_bruta = df["receita_bruta"].sum() if "receita_bruta" in df.columns else 0
ticket = receita_bruta / total_pares if total_pares else 0
margem = (df["lucro_bruto"].sum() / df["receita_liquida"].sum() * 100) if "lucro_bruto" in df.columns and df["receita_liquida"].sum() > 0 else 0
num_trans = len(df)

for col, label, val, fmt in [
    (c1, "Pares Vendidos", total_pares, "int"),
    (c2, "Receita Bruta", receita_bruta, "moeda"),
    (c3, "Ticket Médio", ticket, "moeda"),
    (c4, "Margem Bruta", margem, "pct"),
    (c5, "Transações", num_trans, "int"),
]:
    if fmt == "moeda":
        v = f"R$ {val:,.0f}"
    elif fmt == "pct":
        v = f"{val:.1f}%"
    else:
        v = f"{int(val):,}"
    col.metric(label, v)

st.markdown("---")

# Gráficos linha 1
col_g1, col_g2 = st.columns([3, 2])
with col_g1:
    st.plotly_chart(grafico_receita_mensal(df), use_container_width=True)
with col_g2:
    # Se canal tem variação real, mostra pizza; senão mostra top produtos
    tem_canais = "canal" in df.columns and df["canal"].nunique() > 1
    if tem_canais:
        st.plotly_chart(grafico_canal_pizza(df), use_container_width=True)
    else:
        from utils.charts import grafico_top_produtos
        st.plotly_chart(grafico_top_produtos(df), use_container_width=True)

# Gráficos linha 2
col_g3, col_g4 = st.columns(2)
with col_g3:
    st.plotly_chart(grafico_mix_categoria(df), use_container_width=True)
with col_g4:
    st.plotly_chart(grafico_margem_categoria(df), use_container_width=True)

# Gráficos linha 3
col_g5, col_g6 = st.columns(2)
with col_g5:
    st.plotly_chart(grafico_ticket_medio(df), use_container_width=True)
with col_g6:
    st.plotly_chart(grafico_top_produtos(df, n=10), use_container_width=True)

# Heatmap mês × categoria
st.markdown("### 🗓️ Receita por Categoria × Mês")
if "mes" in df.columns and "categoria" in df.columns:
    pivot = df.groupby(["mes", "categoria"])["receita_bruta"].sum().reset_index()
    pivot["mes_str"] = pivot["mes"].astype(str)
    heat_df = pivot.pivot(index="categoria", columns="mes_str", values="receita_bruta").fillna(0)
    fig_heat = px.imshow(
        heat_df, color_continuous_scale=[[0, "#FFFFFF"], [0.5, "#8B0000"], [1, "#8B7336"]],
        text_auto=".0f", aspect="auto",
        labels=dict(color="Receita (R$)")
    )
    fig_heat.update_layout(paper_bgcolor="#FFFFFF", plot_bgcolor="#F7F7F7",
                           font=dict(color="#1A1A1A"), height=350,
                           margin=dict(l=20, r=20, t=30, b=20))
    st.plotly_chart(fig_heat, use_container_width=True)

# Tabela de detalhes
st.markdown("### 📋 Tabela de Vendas por Categoria")
tab_cat = df.groupby("categoria").agg(
    Pares=("quantidade", "sum") if "quantidade" in df.columns else ("receita_bruta", "count"),
    **{"Receita Bruta (R$)": ("receita_bruta", "sum")},
    **{"Receita Líquida (R$)": ("receita_liquida", "sum")} if "receita_liquida" in df.columns else {},
    **{"CMV (R$)": ("cmv", "sum")} if "cmv" in df.columns else {},
    **{"Lucro Bruto (R$)": ("lucro_bruto", "sum")} if "lucro_bruto" in df.columns else {},
).reset_index()

if "Receita Bruta (R$)" in tab_cat.columns and "Lucro Bruto (R$)" in tab_cat.columns:
    tab_cat["Margem Bruta (%)"] = (tab_cat["Lucro Bruto (R$)"] / tab_cat["Receita Bruta (R$)"] * 100).round(1)
if "Pares" in tab_cat.columns and "Receita Bruta (R$)" in tab_cat.columns:
    tab_cat["Ticket Médio (R$)"] = (tab_cat["Receita Bruta (R$)"] / tab_cat["Pares"]).round(2)

st.dataframe(
    tab_cat.style.format({
        "Receita Bruta (R$)": "R$ {:,.2f}",
        "Receita Líquida (R$)": "R$ {:,.2f}",
        "CMV (R$)": "R$ {:,.2f}",
        "Lucro Bruto (R$)": "R$ {:,.2f}",
        "Ticket Médio (R$)": "R$ {:,.2f}",
        "Margem Bruta (%)": "{:.1f}%",
        "Pares": "{:,}",
    }),
    hide_index=True, use_container_width=True
)

# Export
col_exp1, col_exp2 = st.columns(2)
with col_exp1:
    st.download_button(
        "⬇️ Exportar detalhes (CSV)",
        data=df.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig"),
        file_name=f"vendas_{ano_sel}.csv", mime="text/csv"
    )
