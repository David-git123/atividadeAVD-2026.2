import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# ==============================================================================
# 1. CONFIGURAÇÃO DA PÁGINA
# ==============================================================================
# Define as configurações globais da aplicação Streamlit (título, ícone e layout fluido).
st.set_page_config(
    page_title="Sistema de Análise de Crédito Executiva",
    page_icon="🏦",
    layout="wide"
)

# ==============================================================================
# 2. CARREGAMENTO E TRATAMENTO DE DADOS (COM CACHE)
# ==============================================================================
# O decorator @st.cache_data guarda em memória o resultado da leitura e limpeza do CSV,
# evitando o reprocessamento pesado do ficheiro a cada alteração de filtro pelo utilizador.
@st.cache_data
def carregar_dados(caminho_csv: str) -> pd.DataFrame:
    """
    Realiza a leitura do CSV de crédito e procede à conversão/normalização dos dados.
    """
    df = pd.read_csv(caminho_csv)
    
    # Tratamento de valores ausentes e padronização das colunas categóricas para minúsculas
    colunas_categoricas = ['escolaridade', 'salario_anual', 'tipo_cartao', 'status_financeiro']
    for col in colunas_categoricas:
        if col in df.columns:
            df[col] = df[col].fillna('não informado')
            df[col] = df[col].astype(str).str.strip().str.lower()

    # Função interna para conversão de números no formato brasileiro (ex: '12.691,51' -> 12691.51)
    def converter_valor_br(val):
        if pd.isna(val) or val is None:
            return np.nan
        if isinstance(val, (int, float)):
            return float(val)
        s_val = str(val).replace('.', '').replace(',', '.')
        try:
            return float(s_val)
        except ValueError:
            return np.nan

    # Limpeza de colunas monetárias formatadas como texto
    colunas_monetarias = ['limite_credito', 'valor_transacoes_12m']
    for col in colunas_monetarias:
        if col in df.columns and df[col].dtype == 'object':
            df[col] = df[col].apply(converter_valor_br)
            
    return df

# Tenta carregar o dataset principal
try:
    df_raw = carregar_dados('datasetClean.csv')
except Exception as e:
    st.error(f"Erro ao carregar o ficheiro 'datasetClean.csv': {e}")
    st.stop()

# Mapeamento para exibição executiva dos nomes das colunas
MAPA_COLUNAS = {
    'idade': 'Idade (anos)',
    'dependentes': 'Nº de Dependentes',
    'meses_de_relacionamento': 'Meses de Relacionamento',
    'qtd_produtos': 'Qtd. de Produtos',
    'iteracoes_12m': 'Contatos (12m)',
    'meses_inativo_12m': 'Meses Inativo (12m)',
    'limite_credito': 'Limite de Crédito (R$)',
    'valor_transacoes_12m': 'Valor Transações (12m - R$)',
    'qtd_transacoes_12m': 'Qtd. Transações (12m)'
}

colunas_numericas = [c for c in MAPA_COLUNAS.keys() if c in df_raw.columns]

# ==============================================================================
# 3. SELEÇÃO DE DASHBOARD NA SIDEBAR
# ==============================================================================
st.sidebar.title("📌 Navegação")
opcao_dashboard = st.sidebar.radio(
    label="Selecione o Dashboard desejado:",
    options=["Dashboard 1: Análise Correlacional", "Dashboard 2: Perfil Socioeconômico"],
    index=0
)

st.sidebar.markdown("---")

# ==============================================================================
# 4. DASHBOARD 1: MATRIZ DE CORRELAÇÃO E HISTOGRAMAS DINÂMICOS
# ==============================================================================
if opcao_dashboard == "Dashboard 1: Análise Correlacional":
    st.title("📊 Dashboard 1: Análise Correlacional e Distribuição de Variáveis")
    st.markdown(
        "Visualização executiva focada no estudo de correlação linear de Pearson e distribuição "
        "das métricas operacionais filtradas."
    )
    
    st.sidebar.header("⚙️ Filtros - Dashboard 1")
    
    # Seletor de variáveis para visualização nos gráficos
    variaveis_selecionadas_chaves = st.sidebar.multiselect(
        label="Selecione as variáveis para análise:",
        options=colunas_numericas,
        default=['idade', 'limite_credito', 'valor_transacoes_12m', 'qtd_transacoes_12m'],
        format_func=lambda x: MAPA_COLUNAS.get(x, x),
        key="ms_dash1"
    )

    st.sidebar.markdown("---")
    st.sidebar.subheader("🎯 Filtro de Intervalo por Variável")

    df_filtrado_d1 = df_raw.copy()

    # Aplicação de sliders de intervalo para cada variável selecionada
    if variaveis_selecionadas_chaves:
        for var in variaveis_selecionadas_chaves:
            val_min = float(df_raw[var].min())
            val_max = float(df_raw[var].max())
            rotulo = MAPA_COLUNAS.get(var, var)
            
            intervalo = st.sidebar.slider(
                label=f"Intervalo: {rotulo}",
                min_value=val_min,
                max_value=val_max,
                value=(val_min, val_max),
                key=f"slider_d1_{var}"
            )
            
            df_filtrado_d1 = df_filtrado_d1[
                (df_filtrado_d1[var] >= intervalo[0]) & (df_filtrado_d1[var] <= intervalo[1])
            ]

    # KPIs de resumo de dados filtrados
    col_m1, col_m2, col_m3 = st.columns(3)
    with col_m1:
        st.metric("Total de Clientes Filtrados", f"{len(df_filtrado_d1):,}".replace(",", "."))
    with col_m2:
        adimplentes = (df_filtrado_d1['status_financeiro'] == 'adimplente').sum()
        st.metric("Clientes Adimplentes", f"{adimplentes:,}".replace(",", "."))
    with col_m3:
        inadimplentes = (df_filtrado_d1['status_financeiro'] == 'inadimplente').sum()
        st.metric("Clientes Inadimplentes", f"{inadimplentes:,}".replace(",", "."))

    st.markdown("---")

    # Construção das visualizações caso existam variáveis e dados suficientes
    if len(variaveis_selecionadas_chaves) >= 2 and len(df_filtrado_d1) > 0:
        
        # --- MAPA DE CALOR (CORRELAÇÃO DE PEARSON) ---
        with st.container(border=True):
            st.subheader("🔥 Mapa de Calor (Correlação de Pearson)")
            st.caption("Exibe a correlação linear entre as variáveis selecionadas (escala de -1 a +1).")
            
            matriz_corr = df_filtrado_d1[variaveis_selecionadas_chaves].corr(method='pearson')
            nomes_formatados = [MAPA_COLUNAS.get(c, c) for c in matriz_corr.columns]
            matriz_corr.index = nomes_formatados
            matriz_corr.columns = nomes_formatados

            fig_heatmap = px.imshow(
                matriz_corr,
                text_auto=".2f",
                aspect="auto",
                color_continuous_scale="RdBu_r",
                range_color=[-1, 1],
                labels=dict(color="Correlação")
            )
            fig_heatmap.update_layout(
                margin=dict(l=20, r=20, t=30, b=20),
                coloraxis_colorbar=dict(title="Pearson (r)")
            )
            st.plotly_chart(fig_heatmap, width="stretch")

        # --- HISTOGRAMAS DAS VARIÁVEIS SELECIONADAS ---
        st.markdown("### 📈 Histogramas por Variável")
        cols_hist = st.columns(2)
        
        for idx, var in enumerate(variaveis_selecionadas_chaves):
            col_atual = cols_hist[idx % 2]
            with col_atual:
                with st.container(border=True):
                    rotulo = MAPA_COLUNAS.get(var, var)
                    st.subheader(f"Histograma: {rotulo}")
                    
                    fig_hist = px.histogram(
                        df_filtrado_d1,
                        x=var,
                        color="status_financeiro",
                        barmode="overlay",
                        opacity=0.7,
                        labels={
                            var: rotulo,
                            "status_financeiro": "Status Financeiro",
                            "count": "Frequência"
                        },
                        color_discrete_map={
                            "adimplente": "#1f77b4",
                            "inadimplente": "#d62728"
                        }
                    )
                    fig_hist.update_layout(
                        xaxis_title=rotulo,
                        yaxis_title="Nº de Clientes",
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                        margin=dict(l=20, r=20, t=40, b=20)
                    )
                    st.plotly_chart(fig_hist, width="stretch")

    elif len(variaveis_selecionadas_chaves) < 2:
        st.warning("⚠️ Selecione pelo menos **2 variáveis** no menu lateral para visualizar o mapa de calor e histogramas.")
    else:
        st.error("❌ Nenhum dado encontrado para os intervalos definidos.")

# ==============================================================================
# 5. DASHBOARD 2: PERFIL SOCIOECONÔMICO E CARTÕES DE CRÉDITO
# ==============================================================================
else:
    st.title("💳 Dashboard 2: Perfil Socioeconômico e Tipo de Cartão")
    st.markdown("Análise comparativa focada em escolaridade, faixa salarial e representatividade dos cartões Platinum.")
    
    st.sidebar.header("⚙️ Filtros - Dashboard 2")
    st.sidebar.markdown("Ajuste os intervalos abaixo para filtrar dinamicamente os 3 gráficos e indicadores.")

    df_filtrado_d2 = df_raw.copy()

    # Sliders automáticos para todas as variáveis numéricas
    for var in colunas_numericas:
        val_min = float(df_raw[var].min())
        val_max = float(df_raw[var].max())
        rotulo = MAPA_COLUNAS.get(var, var)
        
        intervalo = st.sidebar.slider(
            label=f"Intervalo: {rotulo}",
            min_value=val_min,
            max_value=val_max,
            value=(val_min, val_max),
            key=f"slider_d2_{var}"
        )
        
        df_filtrado_d2 = df_filtrado_d2[
            (df_filtrado_d2[var] >= intervalo[0]) & (df_filtrado_d2[var] <= intervalo[1])
        ]

    total_clientes_d2 = len(df_filtrado_d2)

    if total_clientes_d2 > 0:
        # Cálculo das métricas solicitadas no Dashboard 2
        qtd_adimplentes = (df_filtrado_d2['status_financeiro'] == 'adimplente').sum()
        qtd_inadimplentes = (df_filtrado_d2['status_financeiro'] == 'inadimplente').sum()
        
        taxa_adimplentes = (qtd_adimplentes / total_clientes_d2) * 100
        taxa_inadimplentes = (qtd_inadimplentes / total_clientes_d2) * 100
        qtd_platinum = (df_filtrado_d2['tipo_cartao'] == 'platinum').sum()

        # Exibição dos KPIs em 3 colunas
        col_k1, col_k2, col_k3 = st.columns(3)
        with col_k1:
            with st.container(border=True):
                st.metric("Taxa de Adimplentes", f"{taxa_adimplentes:.1f}%", delta=f"{qtd_adimplentes} clientes")
        with col_k2:
            with st.container(border=True):
                st.metric("Taxa de Inadimplentes", f"{taxa_inadimplentes:.1f}%", delta=f"-{qtd_inadimplentes} clientes", delta_color="inverse")
        with col_k3:
            with st.container(border=True):
                st.metric("Clientes Cartão Platinum", f"{qtd_platinum:,}".replace(",", "."), delta="Cartão Premium")

        st.markdown("---")

        # Configuração da ordem categórica dos eixos
        ordem_cartao = ['blue', 'silver', 'gold', 'platinum']
        ordem_salario = ['menos que $40k', '$40k - $60k', '$60k - $80k', '$80k - $120k', '$120k +', 'não informado']
        ordem_escolaridade = ['sem educacao formal', 'ensino medio', 'graduacao', 'mestrado', 'doutorado', 'não informado']

        # Estrutura em 3 colunas conforme a disposição do rascunho wireframe
        col_g1, col_g2, col_g3 = st.columns([1, 1.2, 1])

        # --- GRÁFICO 1: HISTOGRAMA DO TIPO DE CARTÃO ---
        with col_g1:
            with st.container(border=True):
                st.subheader("💳 Tipos de Cartão")
                fig_cartao = px.histogram(
                    df_filtrado_d2,
                    x="tipo_cartao",
                    color="status_financeiro",
                    barmode="group",
                    category_orders={"tipo_cartao": ordem_cartao},
                    labels={"tipo_cartao": "Cartão", "status_financeiro": "Status", "count": "Qtd"},
                    color_discrete_map={"adimplente": "#1f77b4", "inadimplente": "#d62728"}
                )
                fig_cartao.update_layout(
                    xaxis_title="Tipo de Cartão",
                    yaxis_title="Nº de Clientes",
                    margin=dict(l=10, r=10, t=30, b=10),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                st.plotly_chart(fig_cartao, width="stretch")

        # --- GRÁFICO 2: DISPERSÃO (SALÁRIO ANUAL VS. TRANSAÇÕES) ---
        with col_g2:
            with st.container(border=True):
                st.subheader("↗️ Salário vs. Transações")
                fig_scatter = px.strip(
                    df_filtrado_d2,
                    x="valor_transacoes_12m",
                    y="salario_anual",
                    color="status_financeiro",
                    category_orders={"salario_anual": ordem_salario},
                    labels={
                        "valor_transacoes_12m": "Valor Transações (R$)",
                        "salario_anual": "Salário Anual",
                        "status_financeiro": "Status"
                    },
                    color_discrete_map={"adimplente": "#1f77b4", "inadimplente": "#d62728"}
                )
                fig_scatter.update_layout(
                    xaxis_title="Valor Transações (R$)",
                    yaxis_title="Salário Anual",
                    margin=dict(l=10, r=10, t=30, b=10),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                st.plotly_chart(fig_scatter, width="stretch")

        # --- GRÁFICO 3: HISTOGRAMA DE ESCOLARIDADE ---
        with col_g3:
            with st.container(border=True):
                st.subheader("🎓 Nível de Escolaridade")
                fig_escolaridade = px.histogram(
                    df_filtrado_d2,
                    x="escolaridade",
                    color="status_financeiro",
                    barmode="group",
                    category_orders={"escolaridade": ordem_escolaridade},
                    labels={"escolaridade": "Escolaridade", "status_financeiro": "Status", "count": "Qtd"},
                    color_discrete_map={"adimplente": "#1f77b4", "inadimplente": "#d62728"}
                )
                fig_escolaridade.update_layout(
                    xaxis_title="Escolaridade",
                    yaxis_title="Nº de Clientes",
                    margin=dict(l=10, r=10, t=30, b=10),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                st.plotly_chart(fig_escolaridade, width="stretch")

    else:
        st.error("❌ Nenhum dado encontrado para os filtros selecionados.")