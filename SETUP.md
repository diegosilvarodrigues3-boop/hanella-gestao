# 🚀 Guia de Configuração — Gestão Marca de Sapatos

## Visão geral da arquitetura

```
Google Forms (entrada de dados)
       ↓ (resposta automática)
Google Sheets (banco de dados)
       ↓ (API via gspread)
Streamlit App (dashboard)
       ↓ (deploy gratuito)
Streamlit Cloud (acesso remoto)
```

---

## PASSO 1 — Criar a Planilha Google Sheets

1. Acesse [sheets.google.com](https://sheets.google.com) e crie uma nova planilha.
2. Renomeie a planilha para **"Gestão Sapatos"**.
3. Crie as seguintes abas (clique em "+" no canto inferior):
   - `Contas_a_Pagar`
   - `Contas_a_Receber`
   - `Vendas`

4. Na aba **Contas_a_Pagar**, crie estas colunas na linha 1:
   ```
   Carimbo de data/hora | Data de Lançamento | Tipo de Despesa | Subcategoria |
   Valor (R$) | Nome do Responsável | Data de Vencimento | Data de Pagamento |
   Status | Comentários
   ```

5. Na aba **Contas_a_Receber**, crie estas colunas:
   ```
   Carimbo de data/hora | Data de Lançamento | Tipo de Receita | Descrição |
   Valor (R$) | Nome do Responsável | Data Prevista de Recebimento |
   Data de Recebimento | Status | Comentários
   ```

6. Anote o **ID da planilha** — é a parte da URL entre `/d/` e `/edit`:
   ```
   https://docs.google.com/spreadsheets/d/ESTE_É_O_ID/edit
   ```

---

## PASSO 2 — Criar os Google Forms

### Form 1: Contas a Pagar

1. Acesse [forms.google.com](https://forms.google.com) → Novo formulário.
2. Título: **"Contas a Pagar — [Nome da Marca]"**
3. Adicione as perguntas:

| Pergunta | Tipo |
|---|---|
| Data de Lançamento | Data |
| Tipo de Despesa | Múltipla escolha: CMV, Marketing, Pessoal, Logística, Aluguel, Administrativo, Tecnologia, Impostos, Outros |
| Subcategoria / Descrição | Resposta curta |
| Valor (R$) | Resposta curta (validação: número) |
| Nome do Responsável | Resposta curta |
| Data de Vencimento | Data |
| Data de Pagamento (deixar em branco se não pago) | Data (não obrigatório) |
| Status | Múltipla escolha: Pago, Em aberto, Vencido |
| Comentários | Parágrafo (não obrigatório) |

4. Clique em **"Respostas"** → ícone de planilha verde → **"Selecionar planilha existente"** → escolha "Gestão Sapatos" → aba **Contas_a_Pagar**.

### Form 2: Contas a Receber

1. Novo formulário. Título: **"Contas a Receber — [Nome da Marca]"**
2. Perguntas:

| Pergunta | Tipo |
|---|---|
| Data de Lançamento | Data |
| Tipo de Receita | Múltipla escolha: Venda Varejo, Venda Atacado, Marketplace, E-commerce, Consignado, Outros |
| Descrição / Nº NF | Resposta curta |
| Valor (R$) | Resposta curta (validação: número) |
| Nome do Responsável | Resposta curta |
| Data Prevista de Recebimento | Data |
| Data de Recebimento (deixar em branco se não recebido) | Data (não obrigatório) |
| Status | Múltipla escolha: Recebido, A receber, Atrasado |
| Comentários | Parágrafo (não obrigatório) |

3. Conecte à aba **Contas_a_Receber** da mesma planilha.

> **Dica:** Copie o link de cada formulário e cole no `app.py` e `pages/3_Financeiro.py`
> nos trechos marcados com `[Abrir Formulário](#)`.

---

## PASSO 3 — Configurar a API do Google (Service Account)

1. Acesse [console.cloud.google.com](https://console.cloud.google.com).
2. Crie um novo projeto ou selecione um existente.
3. No menu lateral: **APIs e Serviços → Biblioteca**.
4. Ative as APIs:
   - **Google Sheets API**
   - **Google Drive API**
5. Vá em **APIs e Serviços → Credenciais → Criar credencial → Conta de serviço**.
6. Dê um nome (ex: "streamlit-gestao") e clique em **Criar e continuar**.
7. Função: **Editor** → Continuar → Concluir.
8. Clique na conta de serviço criada → **Chaves → Adicionar chave → Criar nova chave → JSON**.
9. Salve o arquivo JSON baixado.

10. **Compartilhe a planilha com a conta de serviço:**
    - Abra a planilha Google Sheets.
    - Clique em **Compartilhar**.
    - Cole o email da conta de serviço (algo como `nome@projeto.iam.gserviceaccount.com`).
    - Dê permissão de **Editor**.

---

## PASSO 4 — Configurar credenciais no Streamlit

1. Na pasta do projeto, copie o exemplo:
   ```
   cp .streamlit/secrets.toml.example .streamlit/secrets.toml
   ```

2. Abra o arquivo JSON da conta de serviço e copie os valores para `secrets.toml`:
   ```toml
   [gcp_service_account]
   type = "service_account"
   project_id = "seu-projeto"
   private_key_id = "abc123..."
   private_key = "-----BEGIN RSA PRIVATE KEY-----\n..."
   client_email = "nome@projeto.iam.gserviceaccount.com"
   client_id = "123456789"
   auth_uri = "https://accounts.google.com/o/oauth2/auth"
   token_uri = "https://oauth2.googleapis.com/token"

   [sheets]
   spreadsheet_id = "ID_DA_SUA_PLANILHA"
   ```

---

## PASSO 5 — Fazer deploy no Streamlit Cloud (acesso remoto gratuito)

1. Crie uma conta em [streamlit.io](https://streamlit.io).
2. Faça o push do projeto para um repositório **privado** no GitHub:
   ```bash
   git init
   git add .
   git commit -m "first commit"
   git remote add origin https://github.com/SEU_USUARIO/gestao-sapatos.git
   git push -u origin main
   ```
   > ⚠️ NUNCA commite o `secrets.toml`! O `.gitignore` já o exclui.

3. No Streamlit Cloud: **New app → selecione o repositório → Branch: main → Main file: app.py**.

4. Vá em **Advanced settings → Secrets** e cole o conteúdo do seu `secrets.toml`.

5. Clique em **Deploy**. Em 2-3 minutos o app estará online com URL pública.

---

## PASSO 6 — Importar base de vendas

O app aceita upload de Excel/CSV na sidebar com as seguintes colunas esperadas:

| Coluna | Descrição |
|---|---|
| `data` | Data da venda (formato: DD/MM/YYYY ou YYYY-MM-DD) |
| `categoria` | Categoria do produto (ex: Feminino Casual) |
| `canal` | Canal de venda (ex: E-commerce, Loja Própria) |
| `quantidade` | Número de pares vendidos |
| `preco_unitario` | Preço unitário (R$) |
| `receita_bruta` | Receita bruta total da linha |
| `cmv` | Custo da mercadoria vendida |
| `desconto` | Valor do desconto concedido |
| `vendedor` | Nome do vendedor (opcional) |
| `uf` | Estado (opcional) |

---

## Estrutura de pastas

```
sapatos-gestao/
├── app.py                    ← Página principal (dashboard KPIs)
├── pages/
│   ├── 1_DRE.py             ← DRE detalhada + waterfall
│   ├── 2_Vendas.py          ← Análise volume e mix
│   ├── 3_Financeiro.py      ← CP/CR + fluxo de caixa
│   └── 4_Indicadores.py     ← Indicadores operacionais
├── utils/
│   ├── data_loader.py       ← Carga de dados (Sheets + demo)
│   ├── metricas.py          ← Cálculos DRE e KPIs
│   └── charts.py            ← Gráficos Plotly
├── .streamlit/
│   ├── config.toml          ← Tema (vermelho/escuro)
│   └── secrets.toml.example ← Modelo das credenciais
├── requirements.txt
└── .gitignore
```

---

## Testar localmente

```bash
cd sapatos-gestao
pip install -r requirements.txt
streamlit run app.py
```

Acesse: http://localhost:8501
