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

#### Tabela obrigatória da ficha

Cada ficha de candidato deverá apresentar uma tabela central com, no mínimo, as seguintes colunas, nesta ordem:

| Coluna | Conteúdo |
|---|---|
| Fator | Nome do aspecto de soberania avaliado. |
| Peso | Importância estratégica do fator segundo a metodologia oficial. |
| Prós | Evidências específicas que favorecem autonomia, capacidade nacional ou resistência à dependência externa. |
| Contras | Evidências específicas que indicam dependência, vulnerabilidade, perda de controle ou subordinação externa. |
| Nota prós | Intensidade total dos efeitos favoráveis, em escala definida e uniforme. |
| Nota contras | Intensidade total dos efeitos desfavoráveis, na mesma escala. |
| Saldo do fator | Resultado líquido do fator antes da aplicação do peso. |
| Fonte(s) | Uma ou mais fontes individualizadas para os prós, contras e notas. |

Regras de cálculo:

- `saldo do fator = nota prós − nota contras`;
- as notas de prós e contras usarão a mesma escala, inicialmente de 0 a 10;
- o saldo ficará inicialmente entre −10 e +10;
- `resultado ponderado do fator = saldo do fator × peso`, usado apenas no cálculo e nos detalhes, sem necessidade de ocupar uma coluna principal;
- `média ponderada normalizada = soma(saldo × peso) / soma(pesos aplicáveis)`;
- quando a interface exigir apresentação de 0 a 10, a normalização deverá ser exibida e documentada separadamente, sem substituir ou esconder o saldo original;
- ausência de evidência não será registrada como pró nem contra;
- prós e contras poderão coexistir no mesmo fator;
- cada nota deverá ser explicada pelas evidências listadas, evitando números arbitrários.

Comportamento da tabela:

- permanecer visível na ficha, e não escondida apenas em área metodológica;
- permitir pesquisa, ordenação e filtros por bloco, peso, saldo e confiança;
- permitir expansão da linha para mostrar evidências completas, ressalvas e trechos relevantes;
- exibir múltiplas fontes como links identificados, não como uma URL extensa e ilegível;
- diferenciar visualmente fonte primária, fonte oficial, imprensa, Wikipédia e inferência;
- disponibilizar download da tabela completa ou filtrada em JSON e CSV;
- alimentar diretamente os gráficos da ficha, garantindo que tabela e visualizações utilizem os mesmos dados.

### Comparação

- Seleção direta de candidatos.
- Comparação lado a lado.
- Múltiplos gráficos interativos de alta qualidade.
- Tabelas comparativas baixáveis.
- Comparação das notas, pesos, fatores e médias ponderadas do benchmark.
- Comparação de financiamento, patrimônio, experiência, propostas e outros indicadores disponíveis.
- Links e fontes por item.

### Matriz que fundamenta as notas

O aplicativo deverá apresentar, e não apenas calcular internamente, a tabela completa utilizada como base do benchmark.

Para cada combinação de candidato e fator, exibir:

- fator avaliado;
- definição operacional do fator;
- peso e critérios que determinaram o peso;
- nota atribuída;
- **prós**: fatos, propostas, atos ou declarações que aumentem a autonomia nacional;
- **contras**: fatos, propostas, atos ou declarações que aumentem dependência, vulnerabilidade ou subordinação externa;
- ressalvas e ambiguidades;
- justificativa sintética da nota, explicando como os prós e contras foram convertidos no valor final;
- fonte individual de cada alegação;
- tipo de fonte e de evidência;
- data da fonte e data da última verificação;
- grau de confiança da avaliação;
- indicação clara quando não houver posição ou evidência suficiente.

Os comentários não poderão ser genéricos nem apenas repetir uma descrição global do candidato. Cada nota deverá possuir fundamentação específica para o fator correspondente.

#### Tipos de evidência

Manter separadas, com sinalização visual:

1. ato executado e resultado comprovado;
2. política em execução;
3. proposta registrada em plano oficial;
4. projeto legislativo ou compromisso formal;
5. declaração pública inequívoca;
6. informação secundária confirmada;
7. inferência analítica, que deverá ser explicitamente identificada e nunca apresentada como fato.

#### Apresentação no aplicativo

- Tabela pesquisável, filtrável e ordenável.
- Alternância entre visão resumida e visão detalhada.
- Expansão de cada linha para mostrar prós, contras, ressalvas e fontes.
- Tooltips nos gráficos com resumo da justificativa.
- Clique em uma nota ou ponto do gráfico abre o respectivo fundamento.
- Filtros por candidato, fator, bloco temático, peso, nota, tipo de evidência, confiança e fonte.
- Download integral ou filtrado em JSON e CSV.
- Possibilidade de baixar uma ficha gráfica da comparação como imagem.
- Linha final de média ponderada, sem criar colunas intermediárias de “ponderada”.

#### Auditabilidade do cálculo

- Fórmula geral: `soma(nota × peso) / soma(pesos aplicáveis)`.
- Notas e pesos devem permanecer disponíveis no conjunto de dados baixável.
- Alterações metodológicas devem possuir versão e histórico.
- A interface deve informar qual versão da metodologia e dos dados produziu cada gráfico.
- O usuário poderá visualizar o efeito dos pesos e, em modo de simulação, alterar pesos sem modificar a versão oficial do benchmark.

### Fatores obrigatórios do benchmark

Os fatores abaixo devem existir como linhas independentes da matriz, com notas, pesos, prós, contras, comentários e fontes próprios. Não poderão ser ocultados dentro de categorias excessivamente amplas:

#### Terras raras e minerais críticos

- controle brasileiro das reservas e dos ativos;
- regras para capital e controle estrangeiro;
- processamento, refino e separação realizados no Brasil;
- transferência e domínio tecnológico;
- agregação de valor antes da exportação;
- destino da produção e concentração em um único país comprador;
- efeitos sobre defesa, semicondutores, baterias e indústria;
- salvaguardas ambientais e territoriais.

#### Transição energética

- segurança e continuidade do abastecimento;
- diversidade da matriz energética;
- domínio nacional de equipamentos, tecnologias e cadeias produtivas;
- biocombustíveis, energia solar, eólica, nuclear, hidrelétrica, petróleo e gás;
- baterias, armazenamento, redes elétricas e minerais necessários;
- dependência de fornecedores estrangeiros;
- compatibilidade entre descarbonização, industrialização e autonomia regulatória;
- financiamento e efeitos distributivos.

#### Indústria nacional

- densidade e diversidade das cadeias produtivas brasileiras;
- produção de máquinas, equipamentos e insumos críticos;
- engenharia, pesquisa, patentes e propriedade intelectual;
- conteúdo nacional eficiente e compras públicas;
- capacidade de substituir importações críticas;
- integração competitiva ao comércio exterior sem desindustrialização;
- participação de capital estrangeiro e respectivas salvaguardas;
- empregos qualificados, produtividade e agregação de valor.

#### Ferrovias

- expansão, integração e interoperabilidade da malha;
- transporte de cargas e passageiros;
- ligação entre regiões produtoras, cidades, portos e fronteiras;
- controle dos corredores e gargalos logísticos;
- modelo de concessão, propriedade e regulação;
- origem do financiamento, equipamentos, sinalização e tecnologia;
- produção nacional de trilhos, material rodante e sistemas ferroviários;
- tarifas, direito de passagem, capacidade e continuidade do serviço;
- risco de a infraestrutura servir apenas à exportação primária sem integração territorial e industrial.

Esses fatores poderão pertencer a blocos temáticos para organização visual, mas cada um conservará nota e peso próprios no cálculo.

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
