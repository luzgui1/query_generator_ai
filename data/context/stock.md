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

## Exemplos (Utilize esse padrão de desenvolvimento de queries para te orientar em análises com outras métricas):

### Análise de SKUs obsoletos na última semana:
				SELECT 
				  sid_tempo
				  ,(SUM(qtd_aging_06) + SUM(qtd_aging_07) + SUM(qtd_aging_08)) qtd_skus_obsoletos
				FROM `maga-bigdata.nets_gestao_info.tgi_estoque_hist` 
				WHERE sid_tempo >= DATE_SUB(CURRENT_DATE('America/Sao_Paulo'), INTERVAL 7 DAY)
				GROUP BY 1

### Cruzamento de Estoque com Receita para extração de informações:
#### Exemplo: Receita Bruta e Custo estoque total do dia de ontem.
				SELECT
				    SUM(t1.vlr_custo_estoque) AS total_custo_estoque_ontem,
				    SUM(t2.vlr_rec_bruta) AS faturamento_total_ontem
			  FROM
			    `maga-bigdata.nets_gestao_info.tgi_estoque_hist` AS t1
			  LEFT JOIN `maga-bigdata.nets_gestao_info.tgi_receita` AS t2 
				    ON t1.sid_tempo = t2.sid_tempo 
				    AND t1.cod_sku_pai = LEFT(t2.cod_sku_filho, 12) -- sempre utilizar o SKU para cruzar
			  WHERE t1.sid_tempo = DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)
							
## Recomendações:

- Sempre inclua `sid_tempo` em filtros para reduzir leitura de dados.
- Use `cod_sku_pai` em `GROUP BY` ou `WHERE` para beneficiar do cluster.
- Para agrupamentos hierárquicos, aplique `LEFT(cod_sku_filho, 8|12|15)` conforme o nível desejado.
- Utilize `qtd_vmd` para calcular cobertura ou prever rupturas.
- Métricas de obsolescência podem ser inferidas com somas das colunas `qtd_aging_06` a `qtd_aging_08`.