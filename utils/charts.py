import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

CORES = {
    "primaria": "#C8102E",
    "secundaria": "#FF6B6B",
    "positivo": "#00C853",
    "negativo": "#FF1744",
    "neutro": "#FFC107",
    "fundo": "#1A1A1A",
    "texto": "#FFFFFF",
    "grade": "#333333",
    "paleta": ["#C8102E", "#FF6B6B", "#FF9800", "#FFC107", "#4CAF50",
               "#2196F3", "#9C27B0", "#00BCD4", "#795548", "#607D8B"]
}

LAYOUT_BASE = dict(
    paper_bgcolor=CORES["fundo"],
    plot_bgcolor=CORES["fundo"],
    font=dict(color=CORES["texto"], family="Arial"),
    margin=dict(l=40, r=40, t=50, b=40),
    xaxis=dict(gridcolor=CORES["grade"], zerolinecolor=CORES["grade"]),
    yaxis=dict(gridcolor=CORES["grade"], zerolinecolor=CORES["grade"]),
)


def _apply_layout(fig, title="", height=400):
    fig.update_layout(**LAYOUT_BASE, title=dict(text=title, font=dict(size=16, color=CORES["texto"])),
                      height=height)
    return fig


def grafico_dre_waterfall(dre_dict):
    labels = list(dre_dict.keys())
    values = list(dre_dict.values())
    measures = []
    for i, l in enumerate(labels):
        if l in ["Receita Bruta"]:
            measures.append("absolute")
        elif l in ["Lucro Bruto", "EBITDA", "EBIT", "Lucro Líquido"]:
            measures.append("total")
        else:
            measures.append("relative")

    fig = go.Figure(go.Waterfall(
        name="DRE",
        orientation="v",
        measure=measures,
        x=labels,
        y=values,
        connector=dict(line=dict(color=CORES["grade"], width=1)),
        increasing=dict(marker=dict(color=CORES["positivo"])),
        decreasing=dict(marker=dict(color=CORES["negativo"])),
        totals=dict(marker=dict(color=CORES["primaria"])),
        text=[f"R$ {v:,.0f}" for v in values],
        textposition="outside",
    ))
    return _apply_layout(fig, "DRE — Cascata", height=500)


def grafico_receita_mensal(df_vendas):
    if "mes" not in df_vendas.columns or "receita_bruta" not in df_vendas.columns:
        return go.Figure()
    mensal = df_vendas.groupby("mes").agg(
        receita_bruta=("receita_bruta", "sum"),
        receita_liquida=("receita_liquida", "sum") if "receita_liquida" in df_vendas.columns else ("receita_bruta", "sum"),
        lucro_bruto=("lucro_bruto", "sum") if "lucro_bruto" in df_vendas.columns else ("receita_bruta", lambda x: x.sum() * 0.35)
    ).reset_index()
    mensal["mes_str"] = mensal["mes"].astype(str)

    fig = go.Figure()
    fig.add_trace(go.Bar(x=mensal["mes_str"], y=mensal["receita_bruta"],
                         name="Receita Bruta", marker_color=CORES["primaria"], opacity=0.8))
    fig.add_trace(go.Bar(x=mensal["mes_str"], y=mensal["receita_liquida"],
                         name="Receita Líquida", marker_color=CORES["secundaria"], opacity=0.8))
    fig.add_trace(go.Scatter(x=mensal["mes_str"], y=mensal["lucro_bruto"],
                             name="Lucro Bruto", mode="lines+markers",
                             line=dict(color=CORES["positivo"], width=2),
                             marker=dict(size=6)))
    fig.update_layout(barmode="overlay")
    return _apply_layout(fig, "Receita e Lucro Bruto Mensal", height=400)


def grafico_mix_categoria(df_vendas):
    if "categoria" not in df_vendas.columns:
        return go.Figure()
    mix = df_vendas.groupby("categoria").agg(
        receita=("receita_bruta", "sum"),
        pares=("quantidade", "sum") if "quantidade" in df_vendas.columns else ("receita_bruta", "count")
    ).sort_values("receita", ascending=False).reset_index()

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=mix["categoria"], y=mix["receita"],
        name="Receita (R$)", marker_color=CORES["paleta"][:len(mix)],
        yaxis="y", text=[f"R$ {v/1000:.0f}k" for v in mix["receita"]],
        textposition="outside"
    ))
    fig.add_trace(go.Scatter(
        x=mix["categoria"], y=mix["pares"],
        name="Pares Vendidos", mode="lines+markers",
        line=dict(color=CORES["neutro"], width=2),
        marker=dict(size=8), yaxis="y2"
    ))
    fig.update_layout(
        yaxis2=dict(overlaying="y", side="right", gridcolor=CORES["grade"],
                    title="Pares", color=CORES["texto"]),
        legend=dict(bgcolor="rgba(0,0,0,0)")
    )
    return _apply_layout(fig, "Receita e Volume por Categoria", height=420)


def grafico_canal_pizza(df_vendas):
    if "canal" not in df_vendas.columns:
        return go.Figure()
    canal = df_vendas.groupby("canal")["receita_bruta"].sum().reset_index()
    # Se só há 1 canal genérico, mostra top produtos em vez disso
    if len(canal) == 1 and canal["canal"].iloc[0] in ("Não informado", "N?o informado"):
        return grafico_top_produtos(df_vendas)
    fig = go.Figure(go.Pie(
        labels=canal["canal"], values=canal["receita_bruta"],
        hole=0.45, marker=dict(colors=CORES["paleta"][:len(canal)]),
        textinfo="label+percent", textfont=dict(color=CORES["texto"])
    ))
    fig.update_layout(showlegend=True, legend=dict(bgcolor="rgba(0,0,0,0)"))
    return _apply_layout(fig, "Receita por Canal de Venda", height=380)


def grafico_top_produtos(df_vendas, n=10):
    if "descricao" not in df_vendas.columns:
        return go.Figure()
    top = (df_vendas.groupby("descricao")
           .agg(receita=("receita_bruta", "sum"), qtd=("quantidade", "sum"))
           .sort_values("receita", ascending=False)
           .head(n)
           .reset_index())
    fig = go.Figure(go.Bar(
        x=top["receita"], y=top["descricao"],
        orientation="h",
        marker_color=CORES["primaria"],
        text=[f"R$ {v:.0f}" for v in top["receita"]],
        textposition="outside"
    ))
    fig.update_layout(yaxis=dict(autorange="reversed"))
    return _apply_layout(fig, f"Top {n} Produtos por Receita", height=380)


def grafico_despesas_tipo(df_cp):
    if df_cp.empty or "tipo_despesa" not in df_cp.columns:
        return go.Figure()
    desp = df_cp[df_cp["status"] == "Pago"].groupby("tipo_despesa")["valor"].sum().sort_values(ascending=True).reset_index()
    fig = go.Figure(go.Bar(
        x=desp["valor"], y=desp["tipo_despesa"],
        orientation="h",
        marker_color=CORES["primaria"],
        text=[f"R$ {v:,.0f}" for v in desp["valor"]],
        textposition="outside"
    ))
    return _apply_layout(fig, "Despesas por Tipo (Pagas)", height=380)


def grafico_evolucao_resultado(df_vendas, df_cp):
    if df_vendas.empty:
        return go.Figure()
    rec_mensal = df_vendas.groupby("mes")["receita_liquida" if "receita_liquida" in df_vendas.columns else "receita_bruta"].sum()

    desp_mensal = pd.Series(dtype=float)
    if not df_cp.empty and "data_lancamento" in df_cp.columns:
        df_cp2 = df_cp[df_cp["status"] == "Pago"].copy()
        df_cp2["mes"] = pd.to_datetime(df_cp2["data_lancamento"], errors="coerce").dt.to_period("M")
        desp_mensal = df_cp2.groupby("mes")["valor"].sum()

    resultado = pd.DataFrame({"receita": rec_mensal, "despesas": desp_mensal}).fillna(0)
    resultado["resultado"] = resultado["receita"] - resultado["despesas"]
    resultado = resultado.reset_index()
    resultado["mes_str"] = resultado["mes"].astype(str)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=resultado["mes_str"], y=resultado["receita"],
                             name="Receita", fill="tozeroy",
                             line=dict(color=CORES["positivo"], width=2)))
    fig.add_trace(go.Scatter(x=resultado["mes_str"], y=resultado["despesas"],
                             name="Despesas", fill="tozeroy",
                             line=dict(color=CORES["negativo"], width=2)))
    fig.add_trace(go.Scatter(x=resultado["mes_str"], y=resultado["resultado"],
                             name="Resultado Líquido",
                             line=dict(color=CORES["neutro"], width=3, dash="dot"),
                             mode="lines+markers"))
    return _apply_layout(fig, "Evolução: Receita vs Despesas vs Resultado", height=420)


def grafico_margem_categoria(df_vendas):
    if "categoria" not in df_vendas.columns or "lucro_bruto" not in df_vendas.columns:
        return go.Figure()
    mg = df_vendas.groupby("categoria").agg(
        receita=("receita_bruta", "sum"),
        lucro=("lucro_bruto", "sum")
    ).reset_index()
    mg["margem_pct"] = (mg["lucro"] / mg["receita"] * 100).round(1)
    mg = mg.sort_values("margem_pct", ascending=False)

    cores_barra = [CORES["positivo"] if v >= 40 else (CORES["neutro"] if v >= 30 else CORES["negativo"])
                   for v in mg["margem_pct"]]
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=mg["categoria"], y=mg["margem_pct"],
        marker_color=cores_barra,
        text=[f"{v:.1f}%" for v in mg["margem_pct"]],
        textposition="outside"
    ))
    fig.add_hline(y=40, line_dash="dash", line_color=CORES["neutro"],
                  annotation_text="Meta 40%", annotation_font_color=CORES["neutro"])
    return _apply_layout(fig, "Margem Bruta % por Categoria", height=380)


def grafico_ticket_medio(df_vendas):
    if "categoria" not in df_vendas.columns:
        return go.Figure()
    ticket = df_vendas.groupby("categoria").apply(
        lambda x: x["receita_bruta"].sum() / x["quantidade"].sum() if "quantidade" in x.columns else x["receita_bruta"].mean()
    ).sort_values(ascending=False).reset_index()
    ticket.columns = ["categoria", "ticket_medio"]
    fig = go.Figure(go.Bar(
        x=ticket["categoria"], y=ticket["ticket_medio"],
        marker_color=CORES["paleta"][:len(ticket)],
        text=[f"R$ {v:.0f}" for v in ticket["ticket_medio"]],
        textposition="outside"
    ))
    return _apply_layout(fig, "Ticket Médio por Categoria", height=380)


def grafico_fluxo_caixa(df_cp, df_cr):
    entradas = pd.Series(dtype=float)
    saidas = pd.Series(dtype=float)

    if not df_cr.empty and "data_lancamento" in df_cr.columns:
        df_cr2 = df_cr[df_cr["status"] == "Recebido"].copy()
        df_cr2["mes"] = pd.to_datetime(df_cr2["data_lancamento"], errors="coerce").dt.to_period("M")
        entradas = df_cr2.groupby("mes")["valor"].sum()

    if not df_cp.empty and "data_lancamento" in df_cp.columns:
        df_cp2 = df_cp[df_cp["status"] == "Pago"].copy()
        df_cp2["mes"] = pd.to_datetime(df_cp2["data_lancamento"], errors="coerce").dt.to_period("M")
        saidas = df_cp2.groupby("mes")["valor"].sum()

    fluxo = pd.DataFrame({"entradas": entradas, "saidas": saidas}).fillna(0)
    fluxo["saldo"] = fluxo["entradas"] - fluxo["saidas"]
    fluxo["saldo_acumulado"] = fluxo["saldo"].cumsum()
    fluxo = fluxo.reset_index()
    fluxo["mes_str"] = fluxo["mes"].astype(str)

    fig = go.Figure()
    fig.add_trace(go.Bar(x=fluxo["mes_str"], y=fluxo["entradas"],
                         name="Entradas", marker_color=CORES["positivo"], opacity=0.8))
    fig.add_trace(go.Bar(x=fluxo["mes_str"], y=-fluxo["saidas"],
                         name="Saídas", marker_color=CORES["negativo"], opacity=0.8))
    fig.add_trace(go.Scatter(x=fluxo["mes_str"], y=fluxo["saldo_acumulado"],
                             name="Saldo Acumulado", mode="lines+markers",
                             line=dict(color=CORES["neutro"], width=2.5),
                             yaxis="y2"))
    fig.update_layout(
        barmode="overlay",
        yaxis2=dict(overlaying="y", side="right", gridcolor=CORES["grade"],
                    title="Saldo Acumulado", color=CORES["texto"])
    )
    return _apply_layout(fig, "Fluxo de Caixa Mensal", height=420)
