import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# ==============================================================================
# 1. CONFIGURAÇÃO DA PÁGINA
# ==============================================================================
# Define as configurações globais da aplicação Streamlit (título na aba, ícone e layout wide/ampliado).
st.set_page_config(
    page_title="Sistema de Análise de Crédito Executiva",
    page_icon="🏦",
    layout="wide"
)

# ==============================================================================
# 2. CARREGAMENTO DE DADOS (COM CACHE)
# ==============================================================================
# O decorator @st.cache_data armazena o DataFrame em memória após a primeira leitura,
# evitando que o Streamlit leia o arquivo do disco a cada interação do usuário com os filtros.
@st.cache_data
def carregar_dados(caminho_csv: str) -> pd.DataFrame:
    """
    Lê o arquivo CSV informado e retorna diretamente o DataFrame pandas.
    """
    return pd.read_csv(caminho_csv)

# Tenta carregar o dataset
try:
    df_raw = carregar_dados('data/clean/datasetClean.csv')
except Exception as e:
    st.error(f"Erro ao carregar o arquivo 'datasetClean.csv': {e}")
    st.stop()

# Garantia de conversão numérica para colunas monetárias formatadas no padrão PT-BR (ex: '12.691,51'), se necessário.
df = df_raw.copy()
#Retirando conversão desnecessária.
# for col in ['limite_credito', 'valor_transacoes_12m']:
#     if col in df.columns and df[col].dtype == 'object':
#         df[col] = df[col].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
#         df[col] = pd.to_numeric(df[col], errors='coerce')

# Dicionário de mapeamento para rótulos executivos amigáveis
#As linhas limite_credito e valor_transacoes_12m foram retiradas pois não são variáveis númericas e sim categóricas.
MAPA_COLUNAS = {
    'idade': 'Idade (anos)',
    'dependentes': 'Nº de Dependentes',
    'meses_de_relacionamento': 'Meses de Relacionamento',
    'qtd_produtos': 'Qtd. de Produtos',
    'iteracoes_12m': 'Contatos (12m)',
    'meses_inativo_12m': 'Meses Inativo (12m)',
    # 'limite_credito': 'Limite de Crédito (R$)',
    # 'valor_transacoes_12m': 'Valor Transações (12m - R$)',
    'qtd_transacoes_12m': 'Qtd. Transações (12m)'
}

# Lista com as chaves numéricas disponíveis para análise
colunas_numericas = [c for c in MAPA_COLUNAS.keys() if c in df.columns]

# ==============================================================================
# 3. NAVEGAÇÃO NA SIDEBAR
# ==============================================================================
st.sidebar.title("📌 Navegação")
opcao_dashboard = st.sidebar.radio(
    label="Selecione o Dashboard desejado:",
    options=["Dashboard 1: Análise Correlacional", "Dashboard 2: Perfil Socioeconômico e Transações"],
    index=0
)

st.sidebar.markdown("---")

# ==============================================================================
# 4. DASHBOARD 1: MATRIZ DE CORRELAÇÃO E HISTOGRAMAS DINÂMICOS
# ==============================================================================
if opcao_dashboard == "Dashboard 1: Análise Correlacional":
    st.title("📊 Dashboard 1: Análise Correlacional e Distribuição de Variáveis")
    st.markdown(
        "Visualização executiva focada na correlação linear de Pearson e na distribuição das "
        "variáveis quantitativas filtradas."
    )
    
    st.sidebar.header("⚙️ Filtros - Dashboard 1")
    
    # Seletor de variáveis (multiselect) para definir quais colunas entram na matriz e nos histogramas
    variaveis_selecionadas_chaves = st.sidebar.multiselect(
        label="Selecione as variáveis para análise:",
        options=colunas_numericas,
        default=['idade', 'limite_credito','qtd_transacoes_12m'],
        format_func=lambda x: MAPA_COLUNAS.get(x, x),
        key="ms_dash1"
    )

    st.sidebar.markdown("---")
    st.sidebar.subheader("🎯 Filtro de Intervalo por Variável")

    df_filtrado_d1 = df.copy()

    # Aplicação de sliders duplos de intervalo para cada variável selecionada
    if variaveis_selecionadas_chaves:
        for var in variaveis_selecionadas_chaves:
            val_min = float(df[var].min())
            val_max = float(df[var].max())
            rotulo = MAPA_COLUNAS.get(var, var)
            
            intervalo = st.sidebar.slider(
                label=f"Intervalo: {rotulo}",
                min_value=val_min,
                max_value=val_max,
                value=(val_min, val_max),
                key=f"slider_d1_{var}"
            )
            
            # Filtra dinamicamente as linhas dentro do intervalo selecionado
            df_filtrado_d1 = df_filtrado_d1[
                (df_filtrado_d1[var] >= intervalo[0]) & (df_filtrado_d1[var] <= intervalo[1])
            ]

    #Trecho de código retirado pois essas métricas só devem aparecer no segundo dashboard
    # # Indicadores principais de resumo de dados
    # col_m1, col_m2, col_m3 = st.columns(3)
    # with col_m1:
    #     st.metric("Total de Clientes Filtrados", f"{len(df_filtrado_d1):,}".replace(",", "."))
    # with col_m2:
    #     adimplentes = (df_filtrado_d1['status_financeiro'].str.lower() == 'adimplente').sum()
    #     st.metric("Clientes Adimplentes", f"{adimplentes:,}".replace(",", "."))
    # with col_m3:
    #     inadimplentes = (df_filtrado_d1['status_financeiro'].str.lower() == 'inadimplente').sum()
    #     st.metric("Clientes Inadimplentes", f"{inadimplentes:,}".replace(",", "."))

    st.markdown("---")

    # Renderização dos gráficos caso os filtros sejam válidos
    if len(variaveis_selecionadas_chaves) >= 2 and len(df_filtrado_d1) > 0:
        
        # --- MAPA DE CALOR (CORRELAÇÃO DE PEARSON) ---
        with st.container(border=True):
            st.subheader("🔥 Mapa de Calor (Correlação de Pearson)")
            st.caption("Exibe a força da relação linear entre as variáveis selecionadas (escala de -1 a +1).")
            
            # Cálculo da matriz de correlação de Pearson
            matriz_corr = df_filtrado_d1[variaveis_selecionadas_chaves].corr(method='pearson')
            nomes_formatados = [MAPA_COLUNAS.get(c, c) for c in matriz_corr.columns]
            matriz_corr.index = nomes_formatados
            matriz_corr.columns = nomes_formatados

            # Gráfico de calor do Plotly com escala divergente centro-zero (RdBu_r)
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
                            "Adimplente": "#1f77b4",
                            "Inadimplente": "#d62728",
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
        st.warning("⚠️ Selecione pelo menos **2 variáveis** na barra lateral para visualizar o mapa de calor e histogramas.")
    else:
        st.error("❌ Nenhum dado encontrado para os intervalos selecionados.")

# ==============================================================================
# 5. DASHBOARD 2: PERFIL SOCIOECONÔMICO E TRANSAÇÕES
# ==============================================================================
else:
    st.title("💳 Dashboard 2: Perfil Socioeconômico e Comportamento de Transações")
    st.markdown("Análise quantitativa focada nas métricas operacionais, perfil socioeconômico e engajamento com cartões.")
    
    st.sidebar.header("⚙️ Filtros - Dashboard 2")
    st.sidebar.markdown("Ajuste os intervalos para filtrar os indicadores e os 3 gráficos do dashboard.")

    df_filtrado_d2 = df.copy()

    # Sliders para todas as variáveis numéricas do dataset
    for var in colunas_numericas:
        val_min = float(df[var].min())
        val_max = float(df[var].max())
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
        # Cálculo das 3 métricas do Dashboard 2
        qtd_adimplentes = (df_filtrado_d2['status_financeiro'].str.lower() == 'adimplente').sum()
        qtd_inadimplentes = (df_filtrado_d2['status_financeiro'].str.lower() == 'inadimplente').sum()
        
        taxa_adimplentes = (qtd_adimplentes / total_clientes_d2) * 100
        taxa_inadimplentes = (qtd_inadimplentes / total_clientes_d2) * 100
        qtd_platinum = (df_filtrado_d2['tipo_cartao'].str.lower() == 'platinum').sum()

        # Exibição das 3 métricas em cards ordenados
        col_k1, col_k2, col_k3 = st.columns(3)
        with col_k1:
            with st.container(border=True):
                st.metric("Taxa de Clientes Adimplentes", f"{taxa_adimplentes:.1f}%", delta=f"{qtd_adimplentes} clientes")
        with col_k2:
            with st.container(border=True):
                st.metric("Taxa de Clientes Inadimplentes", f"{taxa_inadimplentes:.1f}%", delta=f"-{qtd_inadimplentes} clientes", delta_color="inverse")
        with col_k3:
            with st.container(border=True):
                st.metric("Nº de Clientes Cartão Platinum", f"{qtd_platinum:,}".replace(",", "."), delta="Cartão Premium")

        st.markdown("---")

        # Ordem categórica das variáveis qualitativas para exibição limpa no Plotly
        ordem_cartao = ['blue', 'silver', 'gold', 'platinum']
        ordem_escolaridade = ['sem educacao formal', 'ensino medio', 'graduacao', 'mestrado', 'doutorado']

        # Disposição dos 3 gráficos em colunas
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
                    labels={"tipo_cartao": "Tipo de Cartão", "status_financeiro": "Status", "count": "Quantidade"},
                    color_discrete_map={
                        "Adimplente": "#1f77b4", "Inadimplente": "#d62728",
                        "adimplente": "#1f77b4", "inadimplente": "#d62728"
                    }
                )
                fig_cartao.update_layout(
                    xaxis_title="Tipo de Cartão",
                    yaxis_title="Nº de Clientes",
                    margin=dict(l=10, r=10, t=30, b=10),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                st.plotly_chart(fig_cartao, width="stretch")

        # --- GRÁFICO 2: GRÁFICO DE DISPERSÃO (VALOR DAS TRANSAÇÕES VS. QTD DE TRANSAÇÕES) ---
        with col_g2:
            with st.container(border=True):
                st.subheader("↗️ Dispersão: Transações")
                st.caption("Eixo X: Valor total das transações | Eixo Y: Quantidade de transações no ano")
                
                # Gráfico de dispersão entre as duas variáveis numéricas contínuas de transação
                fig_scatter = px.scatter(
                    df_filtrado_d2,
                    x="valor_transacoes_12m",
                    y="qtd_transacoes_12m",
                    color="status_financeiro",
                    opacity=0.7,
                    labels={
                        "valor_transacoes_12m": "Valor Transações (12m - R$)",
                        "qtd_transacoes_12m": "Qtd. Transações (12m)",
                        "status_financeiro": "Status"
                    },
                    color_discrete_map={
                        "Adimplente": "#1f77b4", "Inadimplente": "#d62728",
                        "adimplente": "#1f77b4", "inadimplente": "#d62728"
                    }
                )
                fig_scatter.update_layout(
                    xaxis_title="Valor de Transações (R$)",
                    yaxis_title="Quantidade de Transações",
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
                    labels={"escolaridade": "Escolaridade", "status_financeiro": "Status", "count": "Quantidade"},
                    color_discrete_map={
                        "Adimplente": "#1f77b4", "Inadimplente": "#d62728",
                        "adimplente": "#1f77b4", "inadimplente": "#d62728"
                    }
                )
                fig_escolaridade.update_layout(
                    xaxis_title="Escolaridade",
                    yaxis_title="Nº de Clientes",
                    margin=dict(l=10, r=10, t=30, b=10),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                st.plotly_chart(fig_escolaridade, width="stretch")

    else:
        st.error("❌ Nenhum dado encontrado para os filtros selecionados. Redefina os sliders na barra lateral.")