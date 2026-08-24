# Brasil Com Censo — Benchmark de Candidatos

## Estado do projeto

Documento inicial de requisitos. O desenvolvimento, a criação do repositório GitHub e a publicação no Streamlit Community Cloud somente começarão após a definição conjunta da arquitetura de navegação e de conteúdo.

## Marca e apresentação

- Marca: **Brasil Com Censo**.
- Título do aplicativo: **Benchmark de Candidatos**.
- Criar logo e slogan provisórios, com identidade simples, elegante e institucional.
- Eleição inicial: **Presidência da República — 2026**.
- A interface deve ser simples, intuitiva, responsiva e adequada a apresentação pública.

## Objetivo

Criar um aplicativo Streamlit online, publicado no Streamlit Community Cloud, para consultar, filtrar, visualizar, comparar e baixar informações sobre candidatos e eleições brasileiras.

O primeiro recorte será a eleição presidencial de 2026. A arquitetura deverá permitir expansão posterior para governadores, senadores, deputados, prefeitos, vereadores, partidos, anos eleitorais e espectros políticos.

## Funcionalidades principais

### Página inicial — Eleição

- Primeira página do aplicativo.
- Seleção inicial da eleição: Presidência, 2026.
- Visão geral da eleição selecionada.
- Exibição dos candidatos em cartões e gráficos.
- Filtros rápidos e apropriados ao pequeno número inicial de opções.
- Seleção direta de candidato, evitando widgets que exijam dois cliques quando houver poucas alternativas.
- Ao selecionar um candidato, habilitar botão para abrir a ficha do candidato.
- Permitir seleção de dois ou mais candidatos e habilitar botão de comparação.
- O corpo da página deve mudar para o conteúdo correspondente quando a pessoa abrir uma ficha ou comparação.

### Ficha do candidato

- Organizada em abas conforme o tipo de informação.
- Dados biográficos e políticos.
- Partido, coligação, candidatura e situação eleitoral.
- Propostas e avaliação de soberania nacional.
- Histórico político e cargos.
- Doações, receitas, despesas e outros dados eleitorais acessíveis por API ou fonte pública.
- Patrimônio declarado, quando disponível.
- Links para fontes primárias, páginas oficiais e referências complementares.
- Dados complementares da Wikipédia, claramente identificados como fonte secundária.
- Gráficos e tabelas específicos do candidato.
- Exportação dos dados em JSON.
- Exportação de gráficos como imagem.

### Comparação

- Seleção direta de candidatos.
- Comparação lado a lado.
- Múltiplos gráficos interativos de alta qualidade.
- Tabelas comparativas baixáveis.
- Comparação das notas, pesos, fatores e médias ponderadas do benchmark.
- Comparação de financiamento, patrimônio, experiência, propostas e outros indicadores disponíveis.
- Links e fontes por item.

## Dados e fontes

- Planos oficiais protocolados no TSE.
- APIs, arquivos e sistemas públicos eleitorais, preferencialmente do TSE.
- Dados de candidaturas, partidos, receitas, despesas, doadores e fornecedores quando legal e tecnicamente disponíveis.
- Dados institucionais de Câmara, Senado, governos e demais fontes oficiais.
- Wikipédia como fonte secundária complementar, nunca como única base de alegações sensíveis.
- Links explícitos para as fontes.
- Sínteses redigidas de maneira factual, distinguindo fato, proposta, declaração, inferência e avaliação técnica.
- Camada de cache e registro da data de atualização.

## Visualizações

- Múltiplos gráficos interativos e de padrão de apresentação.
- Investigar biblioteca declarativa compatível com Streamlit que permita especificações avançadas inspiradas ou originadas em outras linguagens, como Vega-Lite/Altair, além de Plotly e componentes especializados quando justificáveis.
- Preferir gráficos acessíveis, responsivos, com tooltips, filtros, seleção cruzada e boa exportação.
- Permitir baixar dados em JSON e gráficos como imagem, observadas as limitações de cada biblioteca.

## Experiência do usuário

- Evitar navegabilidade de iniciante e interações desnecessárias.
- Quando existirem poucas opções, usar botões segmentados, cartões clicáveis ou controles de seleção direta.
- Mostrar progresso de modo discreto e elegante.
- Informar o que está sendo processado em segundo plano.
- Usar cache para reduzir recarregamentos e chamadas repetidas.
- Evitar dependência excessiva de `st.session_state` para navegação principal.
- Preferir navegação multipágina nativa, baseada em `st.Page`, `st.navigation` e execução da página selecionada.

## Navegação solicitada

- Sidebar como principal forma de navegação.
- Página inicial denominada **Eleição**, em primeiro lugar.
- Acesso direto também a perfis e comparações.
- Prever expansão por:
  - ano eleitoral;
  - cargo: presidente, governador, senador, deputado, prefeito e vereador;
  - partido;
  - espectro político, a ser definido posteriormente;
  - comparações de candidatos.
- Evitar listar todos os candidatos nominalmente na sidebar, pois isso não escala.
- Investigar categorias e subcategorias do `st.navigation`, expansão e retração de grupos e alternativas para tornar categorias selecionáveis sem inflar o menu.

## Infraestrutura e publicação

- Código-fonte em `D:\PROGRAMACAO\__ed_eleicoes`.
- Inicialização de repositório Git local.
- Criação de repositório no GitHub.
- Atualização do repositório remoto.
- Publicação no Streamlit Community Cloud (`share.streamlit.io`).
- Segredos e tokens em mecanismos próprios do Streamlit/GitHub, nunca versionados.
- Arquivos mínimos esperados futuramente: aplicação, páginas, módulos de dados, modelos, assets, testes, `requirements.txt` ou equivalente, configuração do Streamlit, documentação e licença a definir.

## Decisões pendentes antes do desenvolvimento

1. Arquitetura exata da sidebar e da navegação contextual.
2. Separação entre navegação global e filtros locais.
3. Biblioteca principal de gráficos.
4. Modelo de dados e estratégia de atualização/cache.
5. Fontes e disponibilidade técnica de dados de doações e candidaturas de 2026.
6. Regra definitiva do índice de soberania e tratamento de evidências.
7. Critério futuro de espectro político.
8. Nome e visibilidade do repositório GitHub.
9. Conta/organização GitHub e autorização para criar e publicar o repositório.
10. Conta Streamlit Community Cloud e autorização para realizar o deploy.
