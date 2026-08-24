# Brasil Com Censo — Benchmark de Candidatos

Aplicação Streamlit para explorar candidaturas, fontes públicas e um benchmark editorial de soberania e autonomia estratégica. O primeiro recorte é **Presidência — 2026**.

## O que o app separa

- **Fatos oficiais:** cadastro, bens, redes e prestação de contas publicados pelo TSE.
- **Contexto biográfico:** resumo e links da Wikipédia, como fonte suplementar.
- **Avaliação editorial:** notas de 0 a 10 apoiadas em critérios públicos, com pesos auditáveis e simuláveis.

Uma nota não é um fato nem uma previsão. É a aplicação documentada da régua metodológica às evidências disponíveis. A média ponderada é sempre calculada por `soma(nota × peso) / soma(pesos)`.

## Navegação e leitura

- **Eleição:** visão geral, escolha direta e alternância entre radar-chave, radar por blocos e ranking.
- **Ficha do candidato:** conteúdo e tabelas à esquerda, gráfico alternável à direita; no celular, os blocos são empilhados sem sair da página.
- **Comparar:** seleção de 2 a 4 nomes, simulação de pesos e cinco visualizações comparativas.
- **Tabela-base auditável:** em cada ficha, exibe fator, peso, prós, contras, notas positiva e negativa, saldo e fonte. A última linha traz a média ponderada.

A planilha original enviada ao projeto não continha fontes por linha. Essa ausência é mostrada como tal; a revisão atual oferece a fonte principal oficial e seu link, sem atribuí-la retroativamente à redação original.

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
