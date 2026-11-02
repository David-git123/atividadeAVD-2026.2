## Contexto

Sou um estudante do quinto período de Ciência da computação. Estou realizando um projeto para a disciplina da análise e visualização de dados. O projeto consiste na criação de dois dashboards com métricas obtidas a partir de um dataset da escolha do estudante atráves da ferramenta streamlit. Meu dataset contém informações relacionados à análise de crédito, que separa os clientes em 2 grupos: Adimplentes e Inandimplentes. Os dois dashboards serão direcionados à executivos de empresas de setores variados que possuem interesse em análise de crédito e em informações bancárias de seus clientes. 
 
## Entrada

Como entrada, será disponibilizado um arquivo ".csv" que contém as colunas e linhas do dataset, um arquivo ".png" contendo um rascunho da tela e esta descrição do que deve ser feito: "Gerar código correspondente ao rascunho contido no ".png". O código deverá contemplar uma sidebar lateral que possua um filtro de quais váriáveis do dataset os gráficos irão possuir e um seletor de valor para cada variável que deverá refletir quais dados serão utilizados para realização da visualização. Os gráficos gerados deverão ser: Um mapa de calor, com escala de cor divergente, comtemplando as variáveis selecionadas através do seletor de variáveis e mostrando o valor da correlação de pearson entre as variáveis escolhidas, utilizando os dados que se encaixam do intervalo definido através do seletor de intervalos de cada variável. Além desse gráfico, o dashboard deve conter um histograma para cada variável selecionada e deve mostrar as informações de acordo com o intervalo definido no seletor de intervalo." 

## Restrições

Deve respeitar o que foi definido no skills. Deve utilizar apenas informações de dados contidos no dataset.

## Formato de saída

Código completo do app.py para o primeiro dashboard, com um #TODO indicando onde deve ser colocado o segundo dashboard. Também deve possuir comentários explicando o que cada parte do código estpa efetivamente realizando. As explicações devem comtemplar também o que funções não convencionais ou pouco intuitivas realizam.