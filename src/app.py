import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# ==============================================================================
# 1. CONFIGURAÇÃO DA PÁGINA
# ==============================================================================
# Define o título da página no navegador e a disposição do layout como "wide" (amplo),
# permitindo aproveitar melhor o espaço horizontal para os gráficos em tela.
st.set_page_config(
    page_title="Dashboard de Análise de Crédito",
    page_icon="📊",
    layout="wide"
)

# ==============================================================================
# 2. CARREGAMENTO E TRATAMENTO DE DADOS (COM CACHE)
# ==============================================================================
# A anotação @st.cache_data evita re-executar a leitura e limpeza pesada do CSV a cada
# interação do usuário com os filtros na tela, otimizando o desempenho do app.
@st.cache_data
def carregar_dados(caminho_csv: str) -> pd.DataFrame:
    """
    Lê o CSV contendo os dados bancários/crédito e realiza o tratamento das
    colunas numéricas formatadas no padrão brasileiro (ex: '12.691,51').
    """
    df = pd.read_csv(caminho_csv)
    
    # Função interna auxiliar para conversão de valores monetários/formatados
    def converter_valor_br(val):
        if pd.isna(val) or val is None:
            return np.nan
        if isinstance(val, (int, float)):
            return float(val)
        # Remove ponto de milhar e substitui vírgula por ponto decimal
        s_val = str(val).replace('.', '').replace(',', '.')
        try:
            return float(s_val)
        except ValueError:
            return np.nan

    # Tratamento específico das colunas numéricas que contêm caracteres de texto
    colunas_monetarias = ['limite_credito', 'valor_transacoes_12m']
    for col in colunas_monetarias:
        if col in df.columns and df[col].dtype == 'object':
            df[col] = df[col].apply(converter_valor_br)
            
    return df

# Tenta carregar o dataset principal
try:
    df_raw = carregar_dados('datasetClean.csv')
except Exception as e:
    st.error(f"Erro ao carregar o arquivo 'datasetClean.csv': {e}")
    st.stop()

# Dicionário de mapeamento para renomear colunas técnicas para rótulos amigáveis a executivos.
MAPA_COLUNAS = {
    'idade': 'Idade (anos)',
    'dependentes': 'Nº de Dependentes',
    'meses_de_relacionamento': 'Meses de Relacionamento',
    'qtd_produtos': 'Qtd. de Produtos',
    'iteracoes_12m': 'Contatos (12m)',
    'meses_inativo_12m': 'Meses Inativo (12m)',
    'limite_credito': 'Limite de Crédito (R$)',
    'valor_transacoes_12m': 'Valor Transações (12m - R$)',
    'qtd_transacoes_12m': 'Qtd. Transações (12m)',
    'qtd_transacoes_12m_log': 'Log Qtd. Transações (12m)'
}

# Identifica apenas colunas estritamente numéricas e relevantes para a análise
colunas_numericas = [c for c in MAPA_COLUNAS.keys() if c in df_raw.columns]

# ==============================================================================
# 3. SIDEBAR (PAINEL LATERAL DE FILTROS E INTERVALOS)
# ==============================================================================
st.sidebar.header("⚙️ Filtros do Dashboard")

# --- SELETOR DE VARIÁVEIS ---
# Permite ao usuário escolher quais variáveis serão incluídas no Heatmap e nos Histogramas.
variaveis_selecionadas_chaves = st.sidebar.multiselect(
    label="Selecione as variáveis para análise:",
    options=colunas_numericas,
    default=['idade', 'limite_credito', 'valor_transacoes_12m', 'qtd_transacoes_12m'],
    format_func=lambda x: MAPA_COLUNAS.get(x, x)
)

st.sidebar.markdown("---")
st.sidebar.subheader("🎯 Filtro de Intervalo por Variável")

# Copiamos o dataframe original para aplicar os filtros de intervalo de forma acumulativa
df_filtrado = df_raw.copy()

# Guardará os limites atuais aplicados para exibição nos títulos
intervalos_aplicados = {}

# --- SELETORES DE INTERVALO DINÂMICOS ---
# Para cada variável selecionada na barra lateral, cria um slider de intervalo (min, max).
if variaveis_selecionadas_chaves:
    for var in variaveis_selecionadas_chaves:
        val_min = float(df_raw[var].min())
        val_max = float(df_raw[var].max())
        rotulo = MAPA_COLUNAS.get(var, var)
        
        # Cria um slider duplo (range slider) no sidebar
        intervalo = st.sidebar.slider(
            label=f"Intervalo: {rotulo}",
            min_value=val_min,
            max_value=val_max,
            value=(val_min, val_max),
            key=f"slider_{var}"
        )
        
        intervalos_aplicados[var] = intervalo
        
        # Aplica o filtro de intervalo no DataFrame acumulativo
        df_filtrado = df_filtrado[
            (df_filtrado[var] >= intervalo[0]) & (df_filtrado[var] <= intervalo[1])
        ]
else:
    st.sidebar.info("Selecione pelo menos uma variável no filtro acima.")

# ==============================================================================
# 4. ÁREA PRINCIPAL: DASHBOARD 1
# ==============================================================================
st.title("📊 Dashboard 1: Análise Correlacional e Distribuções de Crédito")
st.markdown(
    "Visualização executiva para análise de perfil de clientes adimplentes vs. inadimplentes "
    "baseada em métricas bancárias e operacionais."
)

# Métricas resumo sobre o volume de dados filtrados
col_m1, col_m2, col_m3 = st.columns(3)
with col_m1:
    st.metric("Total de Clientes Filtrados", f"{len(df_filtrado):,}".replace(",", "."))
with col_m2:
    if 'status_financeiro' in df_filtrado.columns:
        adimplentes = (df_filtrado['status_financeiro'] == 'Adimplente').sum()
        st.metric("Clientes Adimplentes", f"{adimplentes:,}".replace(",", "."))
with col_m3:
    if 'status_financeiro' in df_filtrado.columns:
        inadimplentes = (df_filtrado['status_financeiro'] == 'Inadimplente').sum()
        st.metric("Clientes Inadimplentes", f"{inadimplentes:,}".replace(",", "."))

st.markdown("---")

# Verificação se existem variáveis e dados suficientes após os filtros
if len(variaveis_selecionadas_chaves) >= 2 and len(df_filtrado) > 0:
    
    # Layout em colunas: Heatmap à esquerda, Histogramas organizados à direita/abaixo
    col_heatmap, col_espaco = st.columns([1.2, 0.05])
    
    with col_heatmap:
        with st.container(border=True):
            st.subheader("🔥 Mapa de Calor (Correlação de Pearson)")
            st.caption("Mede a força da relação linear entre as variáveis selecionadas (de -1 a +1).")
            
            # Cálculo da Matriz de Correlação de Pearson
            matriz_corr = df_filtrado[variaveis_selecionadas_chaves].corr(method='pearson')
            
            # Subtitui os nomes das colunas pelos rótulos executivos formatados
            nomes_formatados = [MAPA_COLUNAS.get(c, c) for c in matriz_corr.columns]
            matriz_corr.index = nomes_formatados
            matriz_corr.columns = nomes_formatados

            # Construção do Mapa de Calor interativo com Plotly Express
            # Escala de cor divergente 'RdBu_r' (Red-Blue invertido: azul positivo, vermelho negativo)
            # zmin=-1 e zmax=1 garantem a centralização neutra no zero.
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
            
            # Renderização no Streamlit usando a propriedade width="stretch" (recomendação moderna)
            st.plotly_chart(fig_heatmap, width="stretch")

    # --- SEÇÃO DOS HISTOGRAMAS ---
    st.markdown("### 📈 Histogramas das Variáveis Selecionadas")
    st.caption("Distribuição individual dos dados considerando os limites definidos no filtro.")

    # Exibe os histogramas em uma grade de até 2 colunas para melhor organização visual
    cols_hist = st.columns(2)
    
    for idx, var in enumerate(variaveis_selecionadas_chaves):
        col_atual = cols_hist[idx % 2]
        
        with col_atual:
            with st.container(border=True):
                rotulo = MAPA_COLUNAS.get(var, var)
                st.subheader(f"Histograma: {rotulo}")
                
                # Criação do histograma com separação por status financeiro
                fig_hist = px.histogram(
                    df_filtrado,
                    x=var,
                    color="status_financeiro" if "status_financeiro" in df_filtrado.columns else None,
                    barmode="overlay",
                    opacity=0.7,
                    labels={
                        var: rotulo,
                        "status_financeiro": "Status Financeiro",
                        "count": "Frequência"
                    },
                    color_discrete_map={
                        "Adimplente": "#1f77b4",
                        "Inadimplente": "#d62728"
                    }
                )
                
                fig_hist.update_layout(
                    xaxis_title=rotulo,
                    yaxis_title="Frequência (Nº de Clientes)",
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    margin=dict(l=20, r=20, t=40, b=20)
                )
                
                st.plotly_chart(fig_hist, width="stretch")

elif len(variaveis_selecionadas_chaves) < 2:
    st.warning("⚠️ Selecione pelo menos **2 variáveis** na barra lateral para calcular o mapa de calor e visualizar os histogramas.")

elif len(df_filtrado) == 0:
    st.error("❌ Nenhum dado encontrado para os intervalos selecionados. Redefina os sliders na barra lateral.")

# ==============================================================================
# 5. RESERVA PARA O SEGUNDO DASHBOARD
# ==============================================================================

# TODO: Implementar Dashboard 2 aqui