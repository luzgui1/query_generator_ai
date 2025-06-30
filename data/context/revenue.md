# Métrica:  
Receita 1P  

## Tabela: `maga-bigdata.nets_gestao_info.tgi_receita`

## Descrição  
Tabela com informações de receita detalhadas por pedido e SKU filho. Utilizada para análises financeiras e operacionais, considerando devoluções, impostos, bonificações e custos. Os dados são particionados por data de processamento.

---

## Schema  

- **Primary Key**: [`sid_tempo`, `cod_pedido`, `cod_sku_filho`]  

| Coluna                      | Tipo    | Descrição                                                                                              |
|-----------------------------|---------|--------------------------------------------------------------------------------------------------------|
| `sid_tempo`                 | DATE    | Data de processamento da informação.                                                                   |
| `cod_pedido`                | STRING  | Código identificador do pedido.                                                                        |
| `cod_sku_filho`             | STRING  | Código do SKU filho associado ao pedido.                                                               |
| `flg_dev`                   | STRING  | Flag indicadora de devolução ('0': 'Venda', '1': 'Devolução').                                         |
| `qtd_rec`                   | INT     | Quantidade de itens.                                                                                   |
| `vlr_rec_bruta`             | FLOAT   | Valor bruto recebido pela venda do SKU.                                                                |
| `vlr_icms`                  | FLOAT   | Valor correspondente ao ICMS (Imposto sobre Circulação de Mercadorias e Serviços).                     |
| `vlr_pis`                   | FLOAT   | Valor correspondente ao PIS (Programa de Integração Social).                                           |
| `vlr_cofins`                | FLOAT   | Valor correspondente à COFINS (Contribuição para o Financiamento da Seguridade Social).                |
| `vlr_ipi`                   | FLOAT   | Valor correspondente ao IPI (Imposto sobre Produtos Industrializados).                                 |
| `vlr_iss`                   | FLOAT   | Valor correspondente ao ISS (Imposto Sobre Serviços).                                                  |
| `vlr_bonif`                 | FLOAT   | Valor de bonificação concedida.                                                                        |
| `vlr_icms_bonif`            | FLOAT   | Valor do ICMS sobre a bonificação.                                                                     |
| `vlr_icms_parte_dest`       | FLOAT   | Valor do ICMS destinado à unidade de destino (parte do diferencial de alíquota).                       |
| `vlr_icms_partil_ori`       | FLOAT   | Valor do ICMS partilhado com a unidade de origem.                                                      |
| `vlr_fundo_probrez`         | FLOAT   | Valor destinado ao Fundo de Combate à Pobreza.                                                         |
| `vlr_custo`                 | FLOAT   | Custo associado ao SKU no pedido.                                                                      |
| `vlr_desc`                  | FLOAT   | Valor total de descontos concedidos.                                                                   |
| `vlr_desc_ncard`            | FLOAT   | Valor de descontos relacionados a cartão Netshoes (NCard).                                             |
| `vlr_frete_cli`             | FLOAT   | Valor do frete cobrado do cliente.                                                                     |
| `cod_uni_neg`               | INT     | Código da unidade de negócio associada ao pedido.                                                      |
| `vlr_custo_frete`           | FLOAT   | Custo do frete para a empresa.                                                                         |
| `data_base`                 | DATE    | Data de referência do relatório/snapshot.                                                              |

---

## Exemplos (Utilize esse padrão de desenvolvimento de queries para te orientar em análises com outras métricas):

### Quantidade de pedidos devolvidos no dia de ontem:
			SELECT
			  sid_tempo
			  ,COUNT(cod_pedido) qtd_pedidos
			FROM `maga-bigdata.nets_gestao_info.tgi_receita`
			WHERE 1=1
			  AND sid_tempo = DATE_SUB(sid_tempo,INTERVAL 1 DAY)
			  AND flg_dev = '1'
			GROUP BY 1

### 5 produtos com maior incidência de imposto do mês atual:

			SELECT
			  cod_sku_filho
			  ,(
			      SUM(vlr_pis)
			      + SUM(vlr_cofins)
			      + SUM(vlr_iss)
			      + SUM(vlr_bonif)
			      + SUM(vlr_icms)
			      + SUM(vlr_icms_bonif)
			      + SUM(vlr_icms_parte_dest)
			      + SUM(vlr_icms_partil_ori)
			      + SUM(vlr_fundo_probrez)
			  ) vlr_impostos
			FROM `maga-bigdata.nets_gestao_info.tgi_receita`
			WHERE sid_tempo = CURRENT_DATE()-1
			GROUP BY 1
			ORDER BY 2 DESC
			LIMIT 5
			

## Recomendações  

- Sempre inclua `sid_tempo` em filtros para reduzir a leitura de dados.
- Utilize a combinação de `cod_pedido` e `cod_sku_filho` para identificar de forma única cada linha.
- Para análises financeiras, considere o impacto de `vlr_icms`, `vlr_pis`, `vlr_cofins` e `vlr_ipi` no valor líquido.
- Para análise de devoluções, filtre pela `flg_dev`.
- Cálculos de margem podem ser realizados a partir de `vlr_rec_bruta` menos `vlr_custo` e impostos.
- O `cod_uni_neg` pode ser usado para segmentações por unidade de negócio.
