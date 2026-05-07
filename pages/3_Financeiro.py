import streamlit as st
import pandas as pd
import plotly.express as px
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

st.set_page_config(page_title="Financeiro", page_icon="💳", layout="wide")

from utils.data_loader import carregar_todos_dados
from utils.charts import grafico_fluxo_caixa, grafico_despesas_tipo, CORES

vendas, cp, cr, usando_demo = carregar_todos_dados()

with st.sidebar:
    st.markdown("## 💳 Financeiro")
    aba_sel = st.radio("Visualizar", ["Visão Geral", "Contas a Pagar", "Contas a Receber"])
    st.markdown("---")
    status_cp = st.multiselect("Status CP", ["Pago", "Em aberto", "Vencido"], default=["Pago", "Em aberto", "Vencido"])
    status_cr = st.multiselect("Status CR", ["Recebido", "A receber", "Atrasado"], default=["Recebido", "A receber", "Atrasado"])

st.markdown("# 💳 Gestão Financeira")
if usando_demo:
    st.info("Dados de demonstração. Configure Google Forms + Sheets para dados reais.", icon="ℹ️")

# Filtros
cp_filt = cp[cp["status"].isin(status_cp)] if "status" in cp.columns and not cp.empty else cp
cr_filt = cr[cr["status"].isin(status_cr)] if "status" in cr.columns and not cr.empty else cr

# ── Visão Geral ───────────────────────────────────────────────────────────────
if aba_sel == "Visão Geral":
    total_pagar = cp["valor"].sum() if not cp.empty and "valor" in cp.columns else 0
    total_pago = cp[cp["status"] == "Pago"]["valor"].sum() if not cp.empty and "status" in cp.columns else 0
    total_receber = cr["valor"].sum() if not cr.empty and "valor" in cr.columns else 0
    total_recebido = cr[cr["status"] == "Recebido"]["valor"].sum() if not cr.empty and "status" in cr.columns else 0
    vencidas = cp[cp["status"] == "Vencido"]["valor"].sum() if not cp.empty and "status" in cp.columns else 0
    atrasadas = cr[cr["status"] == "Atrasado"]["valor"].sum() if not cr.empty and "status" in cr.columns else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total a Pagar", f"R$ {total_pagar:,.2f}", f"-R$ {vencidas:,.2f} vencido" if vencidas else "")
    c2.metric("Total Pago", f"R$ {total_pago:,.2f}")
    c3.metric("Total a Receber", f"R$ {total_receber:,.2f}", f"-R$ {atrasadas:,.2f} atrasado" if atrasadas else "")
    c4.metric("Total Recebido", f"R$ {total_recebido:,.2f}")

    st.markdown("---")
    st.plotly_chart(grafico_fluxo_caixa(cp, cr), use_container_width=True)

    col_p, col_r = st.columns(2)
    with col_p:
        st.plotly_chart(grafico_despesas_tipo(cp), use_container_width=True)
    with col_r:
        if not cr.empty and "tipo_receita" in cr.columns:
            rec_tipo = cr[cr["status"] == "Recebido"].groupby("tipo_receita")["valor"].sum().reset_index()
            fig = px.pie(rec_tipo, names="tipo_receita", values="valor", hole=0.4,
                         color_discrete_sequence=CORES["paleta"],
                         title="Receitas por Tipo (Recebidas)")
            fig.update_layout(paper_bgcolor="#1A1A1A", plot_bgcolor="#1A1A1A",
                               font=dict(color="white"), height=380)
            st.plotly_chart(fig, use_container_width=True)

    # Alertas
    st.markdown("### ⚠️ Alertas Financeiros")
    alertas = []
    if not cp.empty and "status" in cp.columns:
        venc_df = cp[cp["status"] == "Vencido"]
        if not venc_df.empty:
            alertas.append(f"🔴 **{len(venc_df)} conta(s) a pagar VENCIDA(S)** — Total: R$ {venc_df['valor'].sum():,.2f}")
    if not cr.empty and "status" in cr.columns:
        atr_df = cr[cr["status"] == "Atrasado"]
        if not atr_df.empty:
            alertas.append(f"🟡 **{len(atr_df)} conta(s) a receber ATRASADA(S)** — Total: R$ {atr_df['valor'].sum():,.2f}")
    if alertas:
        for a in alertas:
            st.warning(a)
    else:
        st.success("✅ Nenhum alerta financeiro no momento.")

# ── Contas a Pagar ────────────────────────────────────────────────────────────
elif aba_sel == "Contas a Pagar":
    st.markdown("## 📤 Contas a Pagar")

    col_link, col_info = st.columns([1, 2])
    with col_link:
        st.markdown("""
        ### 📝 Inserir lançamento
        **[📤 Abrir Formulário Contas a Pagar](https://docs.google.com/forms/d/e/1FAIpQLScibj5eQHjaL33CzlajW7spAjOppZhgXz-rXqVFvzoysXCisw/viewform)**

        *Dados sincronizados automaticamente com o Google Sheets.*
        """)

    # Filtros adicionais
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        tipos = sorted(cp_filt["tipo_despesa"].unique().tolist()) if not cp_filt.empty and "tipo_despesa" in cp_filt.columns else []
        tipo_sel = st.multiselect("Tipo de Despesa", tipos, default=tipos, key="tipo_cp")
    with col_f2:
        resp = sorted(cp_filt["responsavel"].unique().tolist()) if not cp_filt.empty and "responsavel" in cp_filt.columns else []
        resp_sel = st.multiselect("Responsável", resp, default=resp, key="resp_cp")

    df_cp_view = cp_filt.copy()
    if tipo_sel and "tipo_despesa" in df_cp_view.columns:
        df_cp_view = df_cp_view[df_cp_view["tipo_despesa"].isin(tipo_sel)]
    if resp_sel and "responsavel" in df_cp_view.columns:
        df_cp_view = df_cp_view[df_cp_view["responsavel"].isin(resp_sel)]

    # Resumo por status
    if not df_cp_view.empty and "status" in df_cp_view.columns:
        res_status = df_cp_view.groupby("status")["valor"].agg(["sum", "count"]).reset_index()
        cols_status = st.columns(len(res_status))
        for i, row in res_status.iterrows():
            cor = "🟢" if row["status"] == "Pago" else ("🔴" if row["status"] == "Vencido" else "🟡")
            cols_status[i].metric(f"{cor} {row['status']}", f"R$ {row['sum']:,.2f}", f"{int(row['count'])} lançamentos")

    # Tabela
    cols_show = [c for c in ["data_lancamento", "tipo_despesa", "descricao", "valor",
                              "responsavel", "data_vencimento", "data_pagamento", "status", "comentarios"]
                 if c in df_cp_view.columns]
    st.dataframe(
        df_cp_view[cols_show].style.format({
            "valor": "R$ {:,.2f}",
        }).apply(lambda row: [
            "background-color: #1a0000" if row.get("status") == "Vencido" else
            ("background-color: #001a00" if row.get("status") == "Pago" else "")
            for _ in row
        ], axis=1),
        hide_index=True, use_container_width=True, height=400
    )

    # Export
    st.download_button("⬇️ Exportar CSV",
                        data=df_cp_view[cols_show].to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig"),
                        file_name="contas_a_pagar.csv", mime="text/csv")

# ── Contas a Receber ──────────────────────────────────────────────────────────
elif aba_sel == "Contas a Receber":
    st.markdown("## 📥 Contas a Receber")

    st.markdown("""
    ### 📝 Inserir lançamento
    **[📥 Abrir Formulário Contas a Receber](https://docs.google.com/forms/d/e/1FAIpQLSfZDvLRZAZXNF_2LNe5sw7fwW9IzQkZaOUcoeuS0u1pj90J5A/viewform)**

    *Dados sincronizados automaticamente com o Google Sheets.*
    """)

    col_f1, col_f2 = st.columns(2)
    with col_f1:
        tipos_cr = sorted(cr_filt["tipo_receita"].unique().tolist()) if not cr_filt.empty and "tipo_receita" in cr_filt.columns else []
        tipo_cr_sel = st.multiselect("Tipo de Receita", tipos_cr, default=tipos_cr)
    with col_f2:
        resp_cr = sorted(cr_filt["responsavel"].unique().tolist()) if not cr_filt.empty and "responsavel" in cr_filt.columns else []
        resp_cr_sel = st.multiselect("Responsável", resp_cr, default=resp_cr, key="resp_cr")

    df_cr_view = cr_filt.copy()
    if tipo_cr_sel and "tipo_receita" in df_cr_view.columns:
        df_cr_view = df_cr_view[df_cr_view["tipo_receita"].isin(tipo_cr_sel)]
    if resp_cr_sel and "responsavel" in df_cr_view.columns:
        df_cr_view = df_cr_view[df_cr_view["responsavel"].isin(resp_cr_sel)]

    if not df_cr_view.empty and "status" in df_cr_view.columns:
        res_status = df_cr_view.groupby("status")["valor"].agg(["sum", "count"]).reset_index()
        cols_status = st.columns(len(res_status))
        for i, row in res_status.iterrows():
            cor = "🟢" if row["status"] == "Recebido" else ("🔴" if row["status"] == "Atrasado" else "🟡")
            cols_status[i].metric(f"{cor} {row['status']}", f"R$ {row['sum']:,.2f}", f"{int(row['count'])} lançamentos")

    cols_show = [c for c in ["data_lancamento", "tipo_receita", "descricao", "valor",
                              "responsavel", "data_prevista", "data_recebimento", "status", "comentarios"]
                 if c in df_cr_view.columns]
    st.dataframe(df_cr_view[cols_show].style.format({"valor": "R$ {:,.2f}"}),
                 hide_index=True, use_container_width=True, height=400)

    st.download_button("⬇️ Exportar CSV",
                        data=df_cr_view[cols_show].to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig"),
                        file_name="contas_a_receber.csv", mime="text/csv")
