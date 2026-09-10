# Proyecto 3: Segmentación de Clientes (RFM) y Análisis de Churn

## Contexto

El departamento de Marketing necesita identificar a sus clientes más valiosos, detectar quiénes están en riesgo de abandono (churn) y diseñar estrategias de retención personalizadas. 
Este proyecto construye un modelo de segmentación RFM (Recencia, Frecuencia, Monetario) sobre el histórico de transacciones, aplica agrupamiento no supervisado con K-Means, y visualiza los segmentos resultantes de forma interactiva con Plotly.

## Preguntas clave
- ¿Cómo se distribuyen los clientes según los criterios RFM?
- ¿Cuántos segmentos de clientes existen según el modelo K-Means?
- ¿Cuáles son las características principales de cada grupo?
- ¿Qué acciones de marjeting se recomiendad para cada segmento?

## Metodología
1. **Cálculo de RFM (Pandas):** por cada cliente se calculó Recencia (días desde su última compra), Frecuencia (número de pedidos —`Invoice`— distintos) y Monetario (suma total gastada).
2. **Escalamiento (Scikit-Learn `StandardScaler`):** las tres métricas viven en escalas muy distintas entre sí, por lo que se estandarizaron antes de aplicar clustering.
3. **Clustering (`KMeans`):** el número óptimo de clusters se determinó con el método del codo (curvatura máxima en k=4)
4. **Visualización (Plotly):** un scatter 3D interactivo (Recencia × Frecuencia × Monetario) y gráficos de barras comparando el gasto promedio y la frecuencia promedio de cada grupo.

## Requisitos

```bash
pip install pandas numpy scikit-learn plotly matplotlib 
```

## Resultados: perfiles de clientes encontrados

| Cluster | Perfil | Recencia (días) | Frecuencia (pedidos) | Monetario promedio | N° clientes |
|---|---|---|---|---|---|
| 3 | VIP / Champions* | 3.5 | 212.75 | $436,835.79 | 4 |
| 2 | Leales | 25.9 | 103.7 | $83,086.08 | 35 |
| 0 | En Riesgo | 67.0 | 7.3 | $3,008.62 | 3,842 |
| 1 | Perdidos | 463.2 | 2.2 | $764.48 | 2,000 |

## Ejecución

1. Clonar este repositorio y ubicarse en `proyecto_3_segmentacion_entrega/`.
2. Instalar las dependencias listadas arriba como **Requisitos**.
3. Abrir `notebook_rfm_clustering.ipynb` en VSCode o Jupyter y correr todas las
   celdas en orden (Run All).
4. El archivo `data/clientes_segmentados.csv` se genera automáticamente al final
   del notebook.