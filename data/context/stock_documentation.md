# Tabela de Estoque: `maga-bigdata.nets_gestao_info.tgi_estoque_hist`

## Objetivo
Tabela histórica com métricas de estoque por SKU, usada em análises internas. Os dados são particionados por data e clusterizados por SKU pai.

---

## Esquema Técnico

- **Partitioned by**: `sid_tempo`
- **Clustered by**: `cod_sku_pai`

| Coluna                       | Tipo    | Descrição                                                                                                  |
|-----------------------------|---------|------------------------------------------------------------------------------------------------------------|
| `sid_tempo`                 | DATE    | Data da informação. Usada para particionar a tabela.                                                       |
| `cod_sku_pai`               | STRING  | Código do SKU Pai. Contém os 8 primeiros caracteres do SKU avô e representa o grupo de SKUs filhos.       |
| `qtd_estoque_saldo_central`| INT     | Quantidade disponível no centro de distribuição central (estoque vendável).                                |
| `qtd_estoque_saldo`        | INT     | Estoque total incluindo localizações não vendáveis (fotografia, transferência, etc).                      |
| `vlr_custo_estoque`        | FLOAT   | Valor total de custo do estoque disponível.                                                                |
| `qtd_dias_com_estoque_56`  | INT     | Quantidade de dias com estoque disponível nos últimos 56 dias.                                            |
| `qtd_vmd`                  | FLOAT   | Venda Média Diária (total vendido ÷ número de dias).                                                      |
| `qtd_aging_01` a `08`      | INT     | Faixas de tempo de armazenagem. Aging 01 = mais novo; Aging 08 = obsoleto.                                |
| `qtd_skus_com_estoque`     | INT     | Quantidade de SKUs filhos com estoque disponível.                                                          |
| `qtd_skus_com_estoque_base`| INT     | Quantidade de SKUs com estoque na base de comparação.                                                     |
| `qtd_skus`                 | INT     | Total de SKUs filhos monitorados para o SKU pai.                                                           |
| `dt_ultim_compra`          | DATE    | Data da última compra registrada para o SKU.                                                               |
| `dt_prim_compra`           | DATE    | Data da primeira compra registrada para o SKU.                                                             |
| `data_base`                | DATE    | Data de referência do relatório/snapshot.                                                                  |

---

## Hierarquia de SKU

O código de SKU possui estrutura hierárquica embutida:

- **SKU Avô**: 8 caracteres  
- **SKU Pai**: 12 caracteres (prefixo do avô + 4 caracteres)  
- **SKU Filho**: 15 caracteres (prefixo do pai + 3 caracteres)  

**Exemplo prático:**

- SKU Avô: `757-7789`  
- SKU Pai: `757-7789-565`  
- SKU Filho: `757-7789-565-63`  

Essa estrutura permite inferência hierárquica via funções como `LEFT(cod_sku_filho, N)` para agrupar, filtrar ou consolidar níveis superiores.

---

## Glossário de Negócio

| Termo     | Definição                                                                                     |
|-----------|-----------------------------------------------------------------------------------------------|
| `SKU`     | Identificador hierárquico do produto (avô → pai → filho). A estrutura está embutida na string. |
| `VMD`     | Venda Média Diária = total vendido ÷ número de dias.                                          |
| `Ruptura` | Estado em que o SKU está sem estoque disponível (rupturado).                                  |
| `Aging`   | Faixas de tempo de armazenagem (01 = novo; 08 = obsoleto).                                   |

---

## Recomendações para Modelos LLM

- Sempre inclua `sid_tempo` em filtros para reduzir leitura de dados.
- Use `cod_sku_pai` em `GROUP BY` ou `WHERE` para beneficiar do cluster.
- Para agrupamentos hierárquicos, aplique `LEFT(cod_sku_filho, 8|12|15)` conforme o nível desejado.
- Utilize `qtd_vmd` para calcular cobertura ou prever rupturas.
- Métricas de obsolescência podem ser inferidas com somas das colunas `qtd_aging_06` a `qtd_aging_08`.
