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

Sempre que uma dada tabela tiver apenas SKU_FILHO, e for necessário cruzar com outra tabela que tenha SKU_PAI, utilize LEFT(cod_sku_filho,12) para efetuar corretamente o JOIN.
---

## Glossário de Negócio

| Termo     | Definição                                                                                      |
|-----------|----------------------------------------------------------------------------------------------- |
| `SKU`     | Identificador hierárquico do produto (avô → pai → filho). A estrutura está embutida na string. |
| `VMD`     | Venda Média Diária = total vendido ÷ número de dias.                                           |
| `Ruptura` | Estado em que o SKU está sem estoque disponível (rupturado).                                   |
| `Aging`   | Faixas de tempo de armazenagem (01 = novo; 08 = obsoleto).                                     |

---