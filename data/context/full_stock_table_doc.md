# Stock Table Documentation

This document describes the columns of the stock table used for internal analytics.

Dataset Name: maga-bigdata.nets_gestao_info.tgi_estoque_hist

| Column Name | Description |
|-------------|-------------|
| `sid_tempo` | Data da medição de estoque, geralmente usada como chave temporal. {Table Partition}|
| `cod_sku_pai` | Código identificador do SKU principal (produto pai). {Cluster Column}|
| `qtd_estoque_saldo_central` | Quantidade de estoque disponível no centro de distribuição central. |
| `qtd_estoque_saldo` | Quantidade total de estoque disponível, somando todas as localizações. |
| `vlr_custo_estoque` | Valor monetário do custo do estoque disponível. |
| `qtd_dias_com_estoque_56` | Número de dias que o estoque esteve disponível nos últimos 56 dias. |
| `qtd_vmd` | Venda média diária (VMD) do SKU no período analisado. |
| `qtd_aging_01` | Quantidade de estoque com menor tempo de armazenagem (faixa 1). |
| `qtd_aging_02` | Quantidade de estoque com tempo de armazenagem em faixa intermediária (faixa 2). |
| `qtd_aging_03` | Quantidade de estoque em faixa de armazenagem mais elevada (faixa 3). |
| `qtd_aging_04` | Quantidade de estoque com tempo de armazenagem longo (faixa 4). |
| `qtd_aging_05` | Quantidade de estoque com tempo de armazenagem muito longo (faixa 5). |
| `qtd_aging_06` | Quantidade de estoque com tempo de armazenagem crítico (faixa 6). |
| `qtd_aging_07` | Quantidade de estoque com tempo de armazenagem obsoleto (faixa 7). |
| `qtd_aging_08` | Quantidade de estoque extremamente obsoleto (faixa 8). |
| `qtd_skus_com_estoque` | Quantidade de SKUs com estoque disponível. |
| `qtd_skus_com_estoque_base` | Quantidade de SKUs com estoque na base comparativa. |
| `qtd_skus` | Quantidade total de SKUs monitorados. |
| `dt_ultim_compra` | Data da última compra registrada para o SKU. |
| `dt_prim_compra` | Data da primeira compra registrada para o SKU. |
| `data_base` | Data base de referência para o relatório. |