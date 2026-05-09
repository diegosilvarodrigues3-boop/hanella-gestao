import streamlit as st
import pandas as pd
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

st.set_page_config(page_title="DRE", page_icon="💰", layout="wide")

st.markdown("""
<style>
.dre-row { display:flex; justify-content:space-between; padding:6px 12px; border-radius:6px; margin:2px 0; }
.dre-total { background:#C9A84C22; font-weight:700; font-size:1.05rem; border-left:3px solid #C9A84C; }
.dre-subtotal { background:#1C1C1C; font-weight:600; }
.dre-item { color:#888; font-size:0.92rem; }
.dre-margem { color:#C9A84C; font-style:italic; font-weight:600; }
.pos { color:#4CAF82; } .neg { color:#E05252; }
.periodo-card {
    background:#1C1C1C; border:1px solid #2A2A2A; border-radius:10px;
    padding:14px 18px; text-align:center;
}
.periodo-label { font-size:0.7rem; color:#666; text-transform:uppercase; letter-spacing:.6px; }
.periodo-valor { font-size:1.3rem; font-weight:700; color:#C9A84C; margin-top:4px; }
.periodo-delta { font-size:0.82rem; margin-top:4px; }
</style>""", unsafe_allow_html=True)

from utils.data_loader import carregar_todos_dados
from utils.metricas import calcular_dre
from utils.charts import grafico_bridge_dre, grafico_dre_waterfall, grafico_despesas_tipo

vendas, cp, cr, usando_demo = carregar_todos_dados()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 💰 DRE")
    ano = st.selectbox("Ano", [2025, 2024, 2023])
    st.markdown("---")
    st.markdown("**Modo de visualização**")
    modo = st.radio("", ["Comparação de Períodos", "DRE Acumulada"], label_visibility="collapsed")
    st.markdown("---")
    if st.button("🔄 Recarregar"):
        st.cache_data.clear()
        st.rerun()

st.markdown("# 💰 DRE — Demonstração do Resultado")
if usando_demo:
    st.info("Dados de demonstração.", icon="ℹ️")

# Meses disponíveis
NOMES = {1:"Janeiro",2:"Fevereiro",3:"Março",4:"Abril",5:"Maio",6:"Junho",
         7:"Julho",8:"Agosto",9:"Setembro",10:"Outubro",11:"Novembro",12:"Dezembro"}

if "data" in vendas.columns and "ano" in vendas.columns:
    meses_disp = sorted(vendas[vendas["ano"]==ano]["data"].dt.month.dropna().unique().tolist())
else:
    meses_disp = list(range(1,5))

# ═══════════════════════════════════════════════════════════════════════════════
# MODO 1 — COMPARAÇÃO DE PERÍODOS (Bridge Chart)
# ═══════════════════════════════════════════════════════════════════════════════
if modo == "Comparação de Períodos":

    if len(meses_disp) < 2:
        st.warning("É necessário ao menos 2 meses de dados para comparar períodos.")
    else:
        col_sel1, col_seta, col_sel2 = st.columns([2, 1, 2])
        with col_sel1:
            mes_a = st.selectbox("📅 Período base",
                                 options=meses_disp,
                                 format_func=lambda m: NOMES.get(m, str(m)),
                                 index=0)
        with col_seta:
            st.markdown("<div style='text-align:center;font-size:2rem;padding-top:28px;color:#C9A84C;'>→</div>",
                        unsafe_allow_html=True)
        with col_sel2:
            opcoes_b = [m for m in meses_disp if m != mes_a]
            mes_b = st.selectbox("📅 Período comparação",
                                 options=opcoes_b,
                                 format_func=lambda m: NOMES.get(m, str(m)),
                                 index=len(opcoes_b)-1)

        # Calcular DRE para cada período (filtrando por mês)
        def dre_mes(mes):
            df_mes = vendas[(vendas["ano"]==ano) & (vendas["data"].dt.month==mes)] \
                     if "data" in vendas.columns else vendas
            cp_mes = cp[pd.to_datetime(cp["data_lancamento"],errors="coerce").dt.month==mes] \
                     if not cp.empty and "data_lancamento" in cp.columns else cp
            wf, tab, desp = calcular_dre(df_mes, cp_mes)
            return wf, tab, desp

        wf_a, tab_a, desp_a = dre_mes(mes_a)
        wf_b, tab_b, desp_b = dre_mes(mes_b)
        label_a = NOMES.get(mes_a, str(mes_a))
        label_b = NOMES.get(mes_b, str(mes_b))

        # ── KPIs comparativos ─────────────────────────────────────────────────
        st.markdown("<br>", unsafe_allow_html=True)
        linhas_kpi = [
            ("Receita Bruta",    "= Receita Líquida", wf_a, wf_b, "receita_bruta",  "moeda"),
            ("Receita Líquida",  "= Receita Líquida", wf_a, wf_b, "receita_liq",    "moeda"),
            ("Lucro Bruto",      "= Lucro Bruto",     wf_a, wf_b, "lucro_bruto",    "moeda"),
            ("EBITDA",           "= EBITDA",          wf_a, wf_b, "ebitda",         "moeda"),
            ("Lucro Líquido",    "= Lucro Líquido",   wf_a, wf_b, "ll",             "moeda"),
        ]

        cols_kpi = st.columns(5)
        kpi_data = [
            ("Receita Bruta",  wf_a.get("Receita Bruta",0),    wf_b.get("Receita Bruta",0)),
            ("Receita Líquida",wf_a.get("= Receita Líquida",0),wf_b.get("= Receita Líquida",0)),
            ("Lucro Bruto",    wf_a.get("= Lucro Bruto",0),    wf_b.get("= Lucro Bruto",0)),
            ("EBITDA",         wf_a.get("= EBITDA",0),         wf_b.get("= EBITDA",0)),
            ("Lucro Líquido",  wf_a.get("= Lucro Líquido",0),  wf_b.get("= Lucro Líquido",0)),
        ]
        for col, (nome, val_a, val_b) in zip(cols_kpi, kpi_data):
            var = val_b - val_a
            pct = (var / abs(val_a) * 100) if val_a else 0
            sinal = "▲" if var >= 0 else "▼"
            cor = "#4CAF82" if var >= 0 else "#E05252"
            col.markdown(f"""
            <div class='periodo-card'>
                <div class='periodo-label'>{nome}</div>
                <div class='periodo-valor'>R$ {val_b:,.0f}</div>
                <div class='periodo-delta' style='color:{cor};'>{sinal} R$ {abs(var):,.0f} ({abs(pct):.1f}%)</div>
                <div style='font-size:.7rem;color:#555;margin-top:2px;'>base: R$ {val_a:,.0f}</div>
            </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Bridge Chart ──────────────────────────────────────────────────────
        st.plotly_chart(
            grafico_bridge_dre(wf_a, wf_b, label_a, label_b),
            use_container_width=True
        )

        st.markdown("---")

        # ── Tabelas lado a lado ───────────────────────────────────────────────
        st.markdown("### 📋 DRE Comparativa")
        col_ta, col_tb = st.columns(2)

        TOTAIS  = ["RECEITA BRUTA","= RECEITA LÍQUIDA","= LUCRO BRUTO",
                   "(-) Total Despesas Op.","= EBITDA","= EBIT","= LUCRO LÍQUIDO"]
        MARGENS = ["Margem Bruta (%)","Margem EBITDA (%)","Margem Líquida (%)"]

        def render_dre_col(col, tab, titulo):
            with col:
                st.markdown(f"**{titulo}**")
                for linha, valor in tab.items():
                    if linha in MARGENS:
                        st.markdown(f"<div class='dre-row dre-margem'><span>{linha}</span><span>{valor:.1f}%</span></div>",
                                    unsafe_allow_html=True)
                    elif linha in TOTAIS:
                        cor = "pos" if valor >= 0 else "neg"
                        st.markdown(f"<div class='dre-row dre-total'><span>{linha}</span><span class='{cor}'>R$ {valor:,.2f}</span></div>",
                                    unsafe_allow_html=True)
                    else:
                        cor = "pos" if valor >= 0 else "neg"
                        st.markdown(f"<div class='dre-row dre-item'><span>{linha}</span><span class='{cor}'>R$ {valor:,.2f}</span></div>",
                                    unsafe_allow_html=True)

        render_dre_col(col_ta, tab_a, f"📅 {label_a}")
        render_dre_col(col_tb, tab_b, f"📅 {label_b}")

        # ── Variação linha a linha ────────────────────────────────────────────
        st.markdown("### Δ Variação linha a linha")
        linhas_comuns = [l for l in tab_a if l in tab_b]
        rows = []
        for l in linhas_comuns:
            va, vb = tab_a[l], tab_b[l]
            if isinstance(va, float) and isinstance(vb, float):
                delta = vb - va
                pct_d = (delta / abs(va) * 100) if va else 0
                rows.append({"Linha": l, label_a: va, label_b: vb,
                             "Variação R$": delta, "Variação %": pct_d})
        if rows:
            df_var = pd.DataFrame(rows)
            st.dataframe(
                df_var.style
                .format({label_a:"R$ {:,.2f}", label_b:"R$ {:,.2f}",
                         "Variação R$":"R$ {:,.2f}", "Variação %":"{:+.1f}%"})
                .applymap(lambda v: "color:#4CAF82" if isinstance(v,float) and v>0
                          else ("color:#E05252" if isinstance(v,float) and v<0 else ""),
                          subset=["Variação R$","Variação %"]),
                hide_index=True, use_container_width=True
            )

# ═══════════════════════════════════════════════════════════════════════════════
# MODO 2 — DRE ACUMULADA (waterfall original)
# ═══════════════════════════════════════════════════════════════════════════════
else:
    dre_wf, dre_tab, despesas_tipo = calcular_dre(vendas, cp, ano)
    st.plotly_chart(grafico_dre_waterfall(dre_wf), use_container_width=True)
    st.markdown("---")

    col_dre, col_desp = st.columns([1, 1])
    TOTAIS  = ["RECEITA BRUTA","= RECEITA LÍQUIDA","= LUCRO BRUTO",
               "(-) Total Despesas Op.","= EBITDA","= EBIT","= LUCRO LÍQUIDO"]
    MARGENS = ["Margem Bruta (%)","Margem EBITDA (%)","Margem Líquida (%)"]

    with col_dre:
        st.markdown("### 📋 DRE Detalhada")
        receita_liq = dre_tab.get("= RECEITA LÍQUIDA", 1)
        for linha, valor in dre_tab.items():
            if linha in MARGENS:
                st.markdown(f"<div class='dre-row dre-margem'><span>{linha}</span><span>{valor:.1f}%</span></div>",
                            unsafe_allow_html=True)
            elif linha in TOTAIS:
                cor = "pos" if valor >= 0 else "neg"
                st.markdown(f"<div class='dre-row dre-total'><span>{linha}</span><span class='{cor}'>R$ {valor:,.2f}</span></div>",
                            unsafe_allow_html=True)
            else:
                cor = "pos" if valor >= 0 else "neg"
                st.markdown(f"<div class='dre-row dre-item'><span>{linha}</span><span class='{cor}'>R$ {valor:,.2f}</span></div>",
                            unsafe_allow_html=True)

    with col_desp:
        st.markdown("### 📊 Despesas Operacionais")
        st.plotly_chart(grafico_despesas_tipo(cp), use_container_width=True)
        df_desp = pd.DataFrame([
            {"Tipo": k, "Valor (R$)": v, "% Rec. Líq.": (v/receita_liq*100) if receita_liq else 0}
            for k, v in despesas_tipo.items() if v > 0
        ]).sort_values("Valor (R$)", ascending=False)
        st.dataframe(df_desp.style.format({"Valor (R$)":"R$ {:,.2f}","% Rec. Líq.":"{:.1f}%"}),
                     hide_index=True, use_container_width=True)

    st.markdown("---")
    dre_export = pd.DataFrame([{"Linha DRE": k, "Valor (R$)": v} for k, v in dre_tab.items()])
    st.download_button("⬇️ Exportar DRE (CSV)",
                       data=dre_export.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig"),
                       file_name=f"DRE_{ano}.csv", mime="text/csv")
