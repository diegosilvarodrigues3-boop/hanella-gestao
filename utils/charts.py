import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

# ── Paleta de cores ───────────────────────────────────────────────────────────
CORES = {
    "primaria":    "#C9A84C",   # dourado Hanella
    "secundaria":  "#E8C97A",   # dourado claro
    "positivo":    "#4CAF82",   # verde escuro suave
    "negativo":    "#E05252",   # vermelho suave
    "neutro":      "#E8C97A",   # âmbar
    "fundo":       "#0D0D0D",
    "fundo_alt":   "#161616",
    "fundo_card":  "#1C1C1C",
    "texto":       "#F0F0F0",
    "texto_sub":   "#888888",
    "grade":       "#2A2A2A",
    "paleta": ["#C9A84C","#E8C97A","#A07828","#D4B86A","#7A5C1E",
               "#F0D080","#6B4F18","#B89040","#503C10","#DFC060"],
}

# Cor fixa por categoria — consistente em TODOS os gráficos
CORES_CATEGORIA = {
    "Chinelo":     "#C9A84C",   # dourado primário — maior categoria
    "Sandália":    "#E8C97A",   # dourado claro
    "Rasteirinha": "#D4913A",   # âmbar alaranjado
    "Mule":        "#A07828",   # dourado escuro
    "Bolsa":       "#7A9E7E",   # verde acinzentado (acessório)
    "Papete":      "#C97A4C",   # terracota dourado
    "Sapatilha":   "#B8A0D4",   # lilás suave
    "Tamanco":     "#7AACE8",   # azul aço
    "Tênis":       "#E87A7A",   # rose suave
    "Outros":      "#888888",
}

def _cor_categoria(cat):
    return CORES_CATEGORIA.get(cat, CORES["paleta"][hash(cat) % len(CORES["paleta"])])

def _cores_lista(categorias):
    return [_cor_categoria(c) for c in categorias]

LAYOUT_BASE = dict(
    paper_bgcolor=CORES["fundo"],
    plot_bgcolor=CORES["fundo_alt"],
    font=dict(color=CORES["texto"], family="Arial"),
    margin=dict(l=40, r=40, t=50, b=40),
    xaxis=dict(gridcolor=CORES["grade"], zerolinecolor=CORES["grade"],
               linecolor=CORES["grade"]),
    yaxis=dict(gridcolor=CORES["grade"], zerolinecolor=CORES["grade"],
               linecolor=CORES["grade"]),
)


def _apply_layout(fig, title="", height=400):
    fig.update_layout(
        **LAYOUT_BASE,
        title=dict(text=title, font=dict(size=15, color=CORES["texto"])),
        height=height,
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=CORES["texto"])),
    )
    return fig


# ── Gráficos ──────────────────────────────────────────────────────────────────

def grafico_dre_waterfall(dre_dict):
    labels = list(dre_dict.keys())
    values = list(dre_dict.values())
    measures = []
    for l in labels:
        if l in ["Receita Bruta"]:                 measures.append("absolute")
        elif l in ["= Receita Líquida","= Lucro Bruto","= EBITDA","= EBIT","= Lucro Líquido"]:
                                                    measures.append("total")
        else:                                       measures.append("relative")

    fig = go.Figure(go.Waterfall(
        name="DRE", orientation="v", measure=measures,
        x=labels, y=values,
        connector=dict(line=dict(color=CORES["grade"], width=1)),
        increasing=dict(marker=dict(color=CORES["positivo"])),
        decreasing=dict(marker=dict(color=CORES["negativo"])),
        totals=dict(marker=dict(color=CORES["primaria"])),
        text=[f"R$ {v:,.0f}" for v in values], textposition="outside",
    ))
    return _apply_layout(fig, "DRE — Cascata", height=500)


def grafico_receita_mensal(df_vendas):
    if "mes" not in df_vendas.columns or "receita_bruta" not in df_vendas.columns:
        return go.Figure()
    cols = {"receita_bruta": "sum"}
    if "receita_liquida" in df_vendas.columns: cols["receita_liquida"] = "sum"
    if "lucro_bruto"     in df_vendas.columns: cols["lucro_bruto"]     = "sum"
    mensal = df_vendas.groupby("mes").agg(**{k: (k, v) for k, v in cols.items()}).reset_index()
    mensal["mes_str"] = mensal["mes"].astype(str)

    fig = go.Figure()
    fig.add_trace(go.Bar(x=mensal["mes_str"], y=mensal["receita_bruta"],
                         name="Receita Bruta", marker_color=CORES["primaria"], opacity=0.85))
    if "receita_liquida" in mensal:
        fig.add_trace(go.Bar(x=mensal["mes_str"], y=mensal["receita_liquida"],
                             name="Receita Líquida", marker_color=CORES["secundaria"], opacity=0.75))
    if "lucro_bruto" in mensal:
        fig.add_trace(go.Scatter(x=mensal["mes_str"], y=mensal["lucro_bruto"],
                                 name="Lucro Bruto", mode="lines+markers",
                                 line=dict(color=CORES["positivo"], width=2.5),
                                 marker=dict(size=7)))
    fig.update_layout(barmode="overlay")
    return _apply_layout(fig, "Receita e Lucro Bruto Mensal", height=400)


def grafico_mix_categoria(df_vendas):
    if "categoria" not in df_vendas.columns: return go.Figure()
    mix = df_vendas.groupby("categoria").agg(
        receita=("receita_bruta", "sum"),
        pares=("quantidade", "sum") if "quantidade" in df_vendas.columns else ("receita_bruta", "count")
    ).sort_values("receita", ascending=False).reset_index()

    cores = _cores_lista(mix["categoria"].tolist())
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=mix["categoria"], y=mix["receita"], name="Receita (R$)",
        marker_color=cores, yaxis="y",
        text=[f"R$ {v/1000:.1f}k" for v in mix["receita"]], textposition="outside",
    ))
    fig.add_trace(go.Scatter(
        x=mix["categoria"], y=mix["pares"], name="Pares", mode="lines+markers",
        line=dict(color=CORES["secundaria"], width=2), marker=dict(size=8), yaxis="y2",
    ))
    fig.update_layout(
        yaxis2=dict(overlaying="y", side="right", gridcolor=CORES["grade"],
                    title="Pares", color=CORES["texto"]),
    )
    return _apply_layout(fig, "Receita e Volume por Categoria", height=420)


def grafico_canal_pizza(df_vendas):
    if "canal" not in df_vendas.columns: return go.Figure()
    canal = df_vendas.groupby("canal")["receita_bruta"].sum().reset_index()
    if len(canal) == 1 and canal["canal"].iloc[0] in ("Não informado", "N\xe3o informado"):
        return grafico_top_produtos(df_vendas)
    fig = go.Figure(go.Pie(
        labels=canal["canal"], values=canal["receita_bruta"], hole=0.45,
        marker=dict(colors=CORES["paleta"][:len(canal)]),
        textinfo="label+percent", textfont=dict(color=CORES["texto"]),
    ))
    return _apply_layout(fig, "Receita por Canal de Venda", height=380)


def grafico_top_produtos(df_vendas, n=10):
    if "descricao" not in df_vendas.columns: return go.Figure()
    top = (df_vendas.groupby("descricao")
           .agg(receita=("receita_bruta","sum"), qtd=("quantidade","sum"))
           .sort_values("receita", ascending=False).head(n).reset_index())
    fig = go.Figure(go.Bar(
        x=top["receita"], y=top["descricao"], orientation="h",
        marker_color=CORES["primaria"],
        text=[f"R$ {v:.0f}" for v in top["receita"]], textposition="outside",
    ))
    fig.update_layout(yaxis=dict(autorange="reversed"))
    return _apply_layout(fig, f"Top {n} Produtos por Receita", height=380)


def grafico_margem_categoria(df_vendas):
    if "categoria" not in df_vendas.columns or "lucro_bruto" not in df_vendas.columns:
        return go.Figure()
    mg = df_vendas.groupby("categoria").agg(
        receita=("receita_bruta","sum"), lucro=("lucro_bruto","sum")
    ).reset_index()
    mg["margem_pct"] = (mg["lucro"] / mg["receita"] * 100).round(1)
    mg = mg.sort_values("margem_pct", ascending=False)
    cores = [CORES["positivo"] if v >= 40 else (CORES["neutro"] if v >= 30 else CORES["negativo"])
             for v in mg["margem_pct"]]
    fig = go.Figure(go.Bar(
        x=mg["categoria"], y=mg["margem_pct"], marker_color=cores,
        text=[f"{v:.1f}%" for v in mg["margem_pct"]], textposition="outside",
    ))
    fig.add_hline(y=40, line_dash="dash", line_color=CORES["primaria"],
                  annotation_text="Meta 40%", annotation_font_color=CORES["primaria"])
    return _apply_layout(fig, "Margem Bruta % por Categoria", height=380)


def grafico_ticket_medio(df_vendas):
    if "categoria" not in df_vendas.columns: return go.Figure()
    ticket = df_vendas.groupby("categoria").apply(
        lambda x: x["receita_bruta"].sum() / x["quantidade"].sum()
        if "quantidade" in x.columns else x["receita_bruta"].mean()
    ).sort_values(ascending=False).reset_index()
    ticket.columns = ["categoria", "ticket_medio"]
    cores = _cores_lista(ticket["categoria"].tolist())
    fig = go.Figure(go.Bar(
        x=ticket["categoria"], y=ticket["ticket_medio"],
        marker_color=cores,
        text=[f"R$ {v:.2f}" for v in ticket["ticket_medio"]], textposition="outside",
    ))
    return _apply_layout(fig, "Ticket Médio por Categoria (R$)", height=380)


def grafico_despesas_tipo(df_cp):
    if df_cp.empty or "tipo_despesa" not in df_cp.columns: return go.Figure()
    desp = (df_cp.groupby("tipo_despesa")["valor"].sum()
            .sort_values(ascending=True).reset_index())
    fig = go.Figure(go.Bar(
        x=desp["valor"], y=desp["tipo_despesa"], orientation="h",
        marker_color=CORES["primaria"],
        text=[f"R$ {v:,.0f}" for v in desp["valor"]], textposition="outside",
    ))
    return _apply_layout(fig, "Despesas por Tipo (Pagas)", height=380)


def grafico_evolucao_resultado(df_vendas, df_cp):
    if df_vendas.empty: return go.Figure()
    rec_col = "receita_liquida" if "receita_liquida" in df_vendas.columns else "receita_bruta"
    rec_mensal = df_vendas.groupby("mes")[rec_col].sum()
    desp_mensal = pd.Series(dtype=float)
    if not df_cp.empty and "data_lancamento" in df_cp.columns:
        df_cp2 = df_cp.copy()
        df_cp2["mes"] = pd.to_datetime(df_cp2["data_lancamento"], errors="coerce").dt.to_period("M")
        desp_mensal = df_cp2.groupby("mes")["valor"].sum()
    resultado = pd.DataFrame({"receita": rec_mensal, "despesas": desp_mensal}).fillna(0)
    resultado["resultado"] = resultado["receita"] - resultado["despesas"]
    resultado = resultado.reset_index()
    resultado["mes_str"] = resultado["mes"].astype(str)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=resultado["mes_str"], y=resultado["receita"],
                             name="Receita", fill="tozeroy",
                             line=dict(color=CORES["positivo"], width=2),
                             fillcolor="rgba(76,175,130,0.15)"))
    fig.add_trace(go.Scatter(x=resultado["mes_str"], y=resultado["despesas"],
                             name="Despesas", fill="tozeroy",
                             line=dict(color=CORES["negativo"], width=2),
                             fillcolor="rgba(224,82,82,0.15)"))
    fig.add_trace(go.Scatter(x=resultado["mes_str"], y=resultado["resultado"],
                             name="Resultado", mode="lines+markers",
                             line=dict(color=CORES["primaria"], width=3, dash="dot"),
                             marker=dict(size=7)))
    return _apply_layout(fig, "Evolução: Receita vs Despesas vs Resultado", height=420)


def grafico_fluxo_caixa(df_cp, df_cr):
    entradas = pd.Series(dtype=float)
    saidas   = pd.Series(dtype=float)
    if not df_cr.empty and "data_lancamento" in df_cr.columns:
        df_cr2 = df_cr.copy()
        df_cr2["mes"] = pd.to_datetime(df_cr2["data_lancamento"], errors="coerce").dt.to_period("M")
        entradas = df_cr2.groupby("mes")["valor"].sum()
    if not df_cp.empty and "data_lancamento" in df_cp.columns:
        df_cp2 = df_cp.copy()
        df_cp2["mes"] = pd.to_datetime(df_cp2["data_lancamento"], errors="coerce").dt.to_period("M")
        saidas = df_cp2.groupby("mes")["valor"].sum()
    fluxo = pd.DataFrame({"entradas": entradas, "saidas": saidas}).fillna(0)
    fluxo["saldo"] = fluxo["entradas"] - fluxo["saidas"]
    fluxo["saldo_acumulado"] = fluxo["saldo"].cumsum()
    fluxo = fluxo.reset_index()
    fluxo["mes_str"] = fluxo["mes"].astype(str)

    fig = go.Figure()
    fig.add_trace(go.Bar(x=fluxo["mes_str"], y=fluxo["entradas"],
                         name="Entradas", marker_color=CORES["positivo"], opacity=0.85))
    fig.add_trace(go.Bar(x=fluxo["mes_str"], y=-fluxo["saidas"],
                         name="Saídas", marker_color=CORES["negativo"], opacity=0.85))
    fig.add_trace(go.Scatter(x=fluxo["mes_str"], y=fluxo["saldo_acumulado"],
                             name="Saldo Acumulado", mode="lines+markers",
                             line=dict(color=CORES["primaria"], width=2.5), yaxis="y2"))
    fig.update_layout(
        barmode="overlay",
        yaxis2=dict(overlaying="y", side="right", gridcolor=CORES["grade"],
                    title="Saldo Acumulado", color=CORES["texto"]),
    )
    return _apply_layout(fig, "Fluxo de Caixa Mensal", height=420)
