import pandas as pd
import numpy as np
import streamlit as st
from datetime import datetime, timedelta
import random

DEMO_CATEGORIAS = ["Chinelo", "Sandália", "Rasteirinha", "Mule", "Bolsa",
                   "Papete", "Sapatilha", "Tamanco", "Tênis"]

DEMO_CANAIS = ["Loja Própria", "E-commerce", "Atacado", "Marketplace", "Consignado"]

DEMO_TIPOS_DESPESA = ["CMV", "Marketing", "Pessoal", "Logística", "Aluguel",
                      "Administrativo", "Tecnologia", "Impostos", "Outros"]

MESES_PT = {
    "JANEIRO": 1, "FEVEREIRO": 2, "MARÇO": 3, "MARCO": 3, "MARÇO": 3,
    "MAR?O": 3, "MAR�O": 3, "MAR\x3fO": 3,
    "ABRIL": 4, "MAIO": 5, "JUNHO": 6, "JULHO": 7, "AGOSTO": 8,
    "SETEMBRO": 9, "OUTUBRO": 10, "NOVEMBRO": 11, "DEZEMBRO": 12,
}

# Normaliza mês com acentuação inconsistente
def _normalizar_mes(s):
    if not isinstance(s, str):
        return s
    s = s.strip().upper()
    # Tenta exato primeiro
    if s in MESES_PT:
        return s
    # Fallback: remove caracteres não-ASCII e testa variações para MARÇO
    import unicodedata
    s_norm = unicodedata.normalize("NFD", s)
    s_ascii = "".join(c for c in s_norm if unicodedata.category(c) != "Mn")
    mapa_ascii = {"MARCO": "MARÇO", "SANDALIA": "SANDÁLIA"}
    if s_ascii in MESES_PT:
        return s_ascii
    if s_ascii in mapa_ascii:
        return mapa_ascii[s_ascii]
    return s


def _mes_para_data(mes_str, ano=2025):
    """Converte nome de mês PT para datetime (dia 15 do mês)."""
    mes_norm = _normalizar_mes(str(mes_str))
    num = MESES_PT.get(mes_norm)
    if num is None:
        # tenta encontrar parcialmente
        for k, v in MESES_PT.items():
            if mes_norm[:3] in k:
                num = v
                break
    if num is None:
        return pd.NaT
    return pd.Timestamp(year=ano, month=num, day=15)


def _normalizar_categoria(s):
    if not isinstance(s, str):
        return "Outros"
    import unicodedata
    s_orig = s.strip().upper()
    # Normaliza para ASCII para comparação robusta
    s_norm = unicodedata.normalize("NFD", s_orig)
    s_ascii = "".join(c for c in s_norm if unicodedata.category(c) != "Mn").upper()
    mapa = {
        "SANDALIA": "Sandália",   # ASCII normalizado de SANDÁLIA
        "CHINELO": "Chinelo",
        "MULE": "Mule",
        "PAPETE": "Papete",
        "RASTEIRINHA": "Rasteirinha",
        "SAPATILHA": "Sapatilha",
        "TAMANCO": "Tamanco",
        "TENIS": "Tênis",
        "BOLSA": "Bolsa",
    }
    return mapa.get(s_ascii, s_orig.capitalize())


def carregar_base_hanella(arquivo, ano=2025):
    """Parser específico para o formato 'Base Vol&Mix' da Hanella."""
    ext = arquivo.name.split(".")[-1].lower() if hasattr(arquivo, "name") else "xlsx"
    if ext == "csv":
        raw = pd.read_csv(arquivo, header=None)
    else:
        raw = pd.read_excel(arquivo, sheet_name=0, header=None)

    # Encontra a linha onde começa o cabeçalho (contém "Mês" ou "Mes" ou "Quantidade")
    header_row = 0
    for i, row in raw.iterrows():
        vals = [str(v).upper() for v in row.values]
        if any("QUANT" in v or "M" in v[:3] for v in vals if isinstance(v, str)):
            header_row = i
            break

    df = pd.read_excel(arquivo, sheet_name=0, skiprows=header_row + 1, header=0) \
        if ext != "csv" else pd.read_csv(arquivo, skiprows=header_row + 1, header=0)

    # Mapear colunas pelo posição (independe de encoding)
    df.columns = ["mes", "codigo", "codigo_original", "descricao",
                  "categoria", "quantidade", "preco_total", "preco_unit",
                  "custo_ref", "custo_unit", "custo_total", "margem"][:len(df.columns)]

    # Remove linhas sem mês ou com mês = "Mês" (cabeçalho duplicado)
    df = df[df["mes"].apply(lambda x: isinstance(x, str) and len(str(x)) > 2)]
    df = df[~df["mes"].str.upper().str.strip().isin(["MES", "MÊS", "M?S", "MÊS", "MS"])]

    # Converte numéricos
    for col in ["quantidade", "preco_total", "preco_unit", "custo_ref", "custo_unit", "custo_total", "margem"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["preco_total", "quantidade"])
    df = df[df["quantidade"] > 0]

    # Cria coluna data a partir do mês
    df["data"] = df["mes"].apply(lambda m: _mes_para_data(m, ano))
    df["mes_nome"] = df["mes"].apply(_normalizar_mes)
    df["mes"] = df["data"].dt.to_period("M")
    df["ano"] = ano

    # Normaliza categoria
    df["categoria"] = df["categoria"].apply(_normalizar_categoria)

    # Renomeia para o schema interno
    df = df.rename(columns={
        "preco_total": "receita_bruta",
        "custo_total": "cmv",
        "margem": "lucro_bruto",
        "preco_unit": "preco_unitario",
    })
    df["desconto"] = 0.0
    df["receita_liquida"] = df["receita_bruta"]  # sem info de desconto/imposto na base
    df["canal"] = "Não informado"

    return df


def _gerar_vendas_demo(n=400):
    random.seed(42)
    np.random.seed(42)
    # Demo usa os 4 meses da base real (Jan-Abr 2025)
    meses = ["2025-01", "2025-02", "2025-03", "2025-04"]
    datas = []
    for _ in range(n):
        m = random.choice(meses)
        y, mo = map(int, m.split("-"))
        datas.append(pd.Timestamp(year=y, month=mo, day=random.randint(1, 28)))
    datas = pd.DatetimeIndex(datas)

    precos_base = {
        "Chinelo": 27, "Sandália": 41, "Rasteirinha": 34, "Mule": 39,
        "Bolsa": 32, "Papete": 43, "Sapatilha": 20, "Tamanco": 35, "Tênis": 20,
    }
    categorias = np.random.choice(
        DEMO_CATEGORIAS, n,
        p=[0.30, 0.10, 0.13, 0.04, 0.07, 0.03, 0.01, 0.003, 0.317]
    )
    # Fix probabilidades para somar 1
    categorias = np.random.choice(
        DEMO_CATEGORIAS, n,
        p=[0.30, 0.10, 0.13, 0.04, 0.07, 0.03, 0.01, 0.003, 0.317]
    )
    canais = np.random.choice(DEMO_CANAIS, n, p=[0.50, 0.20, 0.15, 0.10, 0.05])
    precos = [precos_base.get(c, 30) * np.random.uniform(0.9, 1.1) for c in categorias]
    qtd = np.random.randint(1, 5, n)
    cmv_pct = np.random.uniform(0.52, 0.58, n)

    df = pd.DataFrame({
        "data": datas,
        "categoria": categorias,
        "canal": canais,
        "descricao": [f"Produto {c}" for c in categorias],
        "quantidade": qtd,
        "preco_unitario": np.round(precos, 2),
        "receita_bruta": np.round(np.array(precos) * qtd, 2),
        "cmv": np.round(np.array(precos) * qtd * cmv_pct, 2),
        "desconto": 0.0,
    })
    df["receita_liquida"] = df["receita_bruta"]
    df["lucro_bruto"] = df["receita_bruta"] - df["cmv"]
    df["mes"] = df["data"].dt.to_period("M")
    df["ano"] = df["data"].dt.year
    return df


def _gerar_contas_pagar_demo(n=30):
    """Despesas demo calibradas para ~R$26k de receita (escala Hanella Jan-Abr 2025).
    CMV não incluído aqui — já consta direto na base de vendas."""
    random.seed(10)
    np.random.seed(10)
    datas_lanc = pd.date_range("2025-01-01", "2025-04-30", periods=n)
    # Remove CMV da lista — ele vem da base de vendas
    tipos_op = ["Marketing", "Pessoal", "Logística", "Aluguel",
                "Administrativo", "Tecnologia", "Impostos", "Outros"]
    tipos = np.random.choice(tipos_op, n,
                             p=[0.15, 0.25, 0.12, 0.18, 0.10, 0.07, 0.08, 0.05])
    # Valores mensais realistas para ~R$6,5k/mês de receita
    valores_base = {
        "Marketing": 380, "Pessoal": 700, "Logística": 260,
        "Aluguel": 480, "Administrativo": 180, "Tecnologia": 120,
        "Impostos": 290, "Outros": 90
    }
    valores = [valores_base[t] * np.random.uniform(0.75, 1.25) for t in tipos]
    status = np.random.choice(["Pago", "Em aberto", "Vencido"], n, p=[0.70, 0.20, 0.10])
    responsaveis = ["Financeiro", "Gestão", "Administrativo"]
    df = pd.DataFrame({
        "data_lancamento": datas_lanc,
        "tipo_despesa": tipos,
        "descricao": [f"Ref. {t} - {i+1:03d}" for i, t in enumerate(tipos)],
        "valor": np.round(valores, 2),
        "responsavel": np.random.choice(responsaveis, n),
        "data_vencimento": datas_lanc + pd.to_timedelta(np.random.randint(5, 45, n), unit="D"),
        "data_pagamento": [
            (datas_lanc[i] + timedelta(days=int(np.random.randint(5, 40))))
            if status[i] == "Pago" else pd.NaT
            for i in range(n)
        ],
        "status": status,
        "comentarios": ["" if np.random.random() > 0.3 else "Verificar" for _ in range(n)]
    })
    return df


def _gerar_contas_receber_demo(n=30):
    random.seed(20)
    np.random.seed(20)
    datas_lanc = pd.date_range("2025-01-01", "2025-04-30", periods=n)
    tipos = np.random.choice(["Venda Varejo", "Venda Atacado", "Marketplace", "E-commerce", "Outros"], n,
                             p=[0.35, 0.25, 0.15, 0.20, 0.05])
    valores = np.random.uniform(500, 8000, n)
    status = np.random.choice(["Recebido", "A receber", "Atrasado"], n, p=[0.72, 0.20, 0.08])
    df = pd.DataFrame({
        "data_lancamento": datas_lanc,
        "tipo_receita": tipos,
        "descricao": [f"NF {1000+i} - {t}" for i, t in enumerate(tipos)],
        "valor": np.round(valores, 2),
        "responsavel": np.random.choice(["Vendas", "Key Account", "E-commerce"], n),
        "data_prevista": datas_lanc + pd.to_timedelta(np.random.randint(7, 60, n), unit="D"),
        "data_recebimento": [
            (datas_lanc[i] + timedelta(days=int(np.random.randint(7, 55))))
            if status[i] == "Recebido" else pd.NaT
            for i in range(n)
        ],
        "status": status,
        "comentarios": ["" if np.random.random() > 0.25 else "Confirmar" for _ in range(n)]
    })
    return df


@st.cache_data(ttl=300)
def carregar_dados_google_sheets():
    try:
        import gspread
        from google.oauth2 import service_account
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = service_account.Credentials.from_service_account_info(
            creds_dict,
            scopes=["https://spreadsheets.google.com/feeds",
                    "https://www.googleapis.com/auth/drive"]
        )
        gc = gspread.authorize(creds)
        sheet_id = st.secrets["sheets"]["spreadsheet_id"]
        sh = gc.open_by_key(sheet_id)

        def aba_para_df(nome_aba):
            try:
                ws = sh.worksheet(nome_aba)
                dados = ws.get_all_records()
                return pd.DataFrame(dados) if dados else pd.DataFrame()
            except Exception:
                return pd.DataFrame()

        return {
            "vendas": aba_para_df("Vendas"),
            "contas_pagar": aba_para_df("Contas_a_Pagar"),
            "contas_receber": aba_para_df("Contas_a_Receber"),
            "fonte": "google_sheets"
        }
    except Exception:
        return None


def carregar_todos_dados(arquivo_vendas=None):
    sheets_data = carregar_dados_google_sheets()
    usando_demo = False

    if sheets_data and not sheets_data["vendas"].empty:
        vendas = sheets_data["vendas"]
        cp = sheets_data["contas_pagar"]
        cr = sheets_data["contas_receber"]
    else:
        vendas = _gerar_vendas_demo()
        cp = _gerar_contas_pagar_demo()
        cr = _gerar_contas_receber_demo()
        usando_demo = True

    if arquivo_vendas is not None:
        try:
            vendas = carregar_base_hanella(arquivo_vendas, ano=2025)
            usando_demo = False
        except Exception as e:
            st.warning(f"Erro ao carregar arquivo: {e}. Usando dados demo.")

    # Normalizar datas em CP/CR
    for col in ["data_lancamento"]:
        for df in [cp, cr]:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce")

    if "mes" not in vendas.columns and "data" in vendas.columns:
        vendas["mes"] = vendas["data"].dt.to_period("M")
    if "ano" not in vendas.columns and "data" in vendas.columns:
        vendas["ano"] = vendas["data"].dt.year

    return vendas, cp, cr, usando_demo
