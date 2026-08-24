# Brasil Com Censo — Benchmark de Candidatos

Aplicação Streamlit para explorar candidaturas, fontes públicas e um benchmark editorial de soberania e autonomia estratégica. O primeiro recorte é **Presidência — 2026**.

## O que o app separa

- **Fatos oficiais:** cadastro, bens, redes e prestação de contas publicados pelo TSE.
- **Contexto biográfico:** resumo e links da Wikipédia, como fonte suplementar.
- **Avaliação editorial:** notas de 0 a 10 apoiadas em critérios públicos, com pesos auditáveis e simuláveis.

Uma nota não é um fato nem uma previsão. É a aplicação documentada da régua metodológica às evidências disponíveis. A média ponderada é sempre calculada por `soma(nota × peso) / soma(pesos)`.

## Navegação e leitura

- **Presidência:** visão geral e os 13 pedidos de candidatura do snapshot do TSE como itens diretos do menu; cada nome abre sua ficha completa em um clique.
- **Ficha do candidato:** conteúdo em abas à esquerda, gráfico alternável à direita; dados oficiais do TSE e seções da Wikipédia são identificados separadamente.
- **Comparar:** páginas diretas para visão geral, radar por fatores, mapa de notas e pesos/tabela. Os 13 nomes começam selecionados.
- **Tabela-base auditável:** em cada ficha, exibe fator, peso, prós, contras, notas positiva e negativa, saldo e fonte. A última linha traz a média ponderada.

A planilha original enviada ao projeto não continha fontes por linha. Essa ausência é mostrada como tal; a revisão atual oferece a fonte principal oficial e seu link, sem atribuí-la retroativamente à redação original.

O radar geral, renderizado com Apache ECharts, incorpora os 40 fatores em nove dimensões temáticas para evitar quarenta rótulos sobrepostos. O mapa mantém os 40 fatores individualizados, e o radar seletivo permite escolher de 3 a 12 fatores brutos. “Indústria nacional”, “Transição energética”, “Terras raras e minerais críticos” e “Ferrovias” são linhas exclusivas da metodologia — não um gráfico privilegiado.

O cadastro contém os 13 pedidos encontrados no arquivo oficial de 24/08/2026. Até agora, quatro nomes possuem avaliação documental completa. Os demais aparecem com dados oficiais e Wikipédia, mas sem notas presumidas; pedido registrado também não é apresentado como registro judicialmente deferido.

## Executar localmente

```powershell
python -m pip install -r requirements.txt
python -m streamlit run streamlit_app.py
```

## Atualizar dados oficiais

```powershell
python scripts/refresh_tse.py
```

O atualizador usa os arquivos ZIP oficiais do Portal de Dados Abertos do TSE. Se o portal estiver indisponível ou bloquear a rede de execução, o app preserva o último snapshot validado e informa a falha; não substitui dados ausentes por estimativas.

## Publicação

No Streamlit Community Cloud, selecione este repositório, a branch principal e `streamlit_app.py`. Não há segredos obrigatórios para o MVP.
