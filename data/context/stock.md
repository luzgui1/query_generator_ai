# Métrica:
Estoque

## Tabela: `maga-bigdata.nets_gestao_info.tgi_estoque_hist`

## Descrição
Tabela histórica com métricas de estoque por SKU, usada em análises internas. Os dados são particionados por data e clusterizados por SKU pai.

## Schema

- **Partitioned by**: `sid_tempo`
- **Clustered by**: `cod_sku_pai`
- **Primary Key**: [`sid_tempo`,`cod_sku_pai`]

| Coluna                      | Tipo    | Descrição                                                                                                  |
|-----------------------------|---------|------------------------------------------------------------------------------------------------------------|
| `sid_tempo`                 | DATE    | Data da informação. Usada para particionar a tabela.                                                       |
| `cod_sku_pai`               | STRING  | Código do SKU Pai. Contém os 8 primeiros caracteres do SKU avô e representa o grupo de SKUs filhos.        |
| `qtd_estoque_saldo_central` | INT     | Quantidade disponível no centro de distribuição central (estoque vendável).                                |
| `qtd_estoque_saldo`         | INT     | Estoque total incluindo localizações não vendáveis (fotografia, transferência, etc).                       |
| `vlr_custo_estoque`         | FLOAT   | Valor total de custo do estoque disponível.                                                                |
| `qtd_dias_com_estoque_56`   | INT     | Quantidade de dias com estoque disponível nos últimos 56 dias.                                             |
| `qtd_vmd`                   | FLOAT   | Venda Média Diária (total vendido ÷ número de dias).                                                       |
| `qtd_aging_01` a `08`       | INT     | Faixas de tempo de armazenagem. Aging 01 = mais novo; Aging 08 = obsoleto.                                 |
| `qtd_skus_com_estoque`      | INT     | Quantidade de SKUs filhos com estoque disponível.                                                          |
| `qtd_skus_com_estoque_base` | INT     | Quantidade de SKUs com estoque na base de comparação.                                                      |
| `qtd_skus`                  | INT     | Total de SKUs filhos monitorados para o SKU pai.                                                           |
| `dt_ultim_compra`           | DATE    | Data da última compra registrada para o SKU.                                                               |
| `dt_prim_compra`            | DATE    | Data da primeira compra registrada para o SKU.                                                             |
| `data_base`                 | DATE    | Data de referência do relatório/snapshot.                                                                  |

---

## Exemplos:

...

## Recomendações:

- Sempre inclua `sid_tempo` em filtros para reduzir leitura de dados.
- Use `cod_sku_pai` em `GROUP BY` ou `WHERE` para beneficiar do cluster.
- Para agrupamentos hierárquicos, aplique `LEFT(cod_sku_filho, 8|12|15)` conforme o nível desejado.
- Utilize `qtd_vmd` para calcular cobertura ou prever rupturas.
- Métricas de obsolescência podem ser inferidas com somas das colunas `qtd_aging_06` a `qtd_aging_08`.
