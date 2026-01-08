# Plan de Proyecto: Forecasting de Unidades Vendidas (Multi-Producto)

## 1. Introducción
Este proyecto tiene como objetivo predecir las unidades vendidas para 100 productos distribuidos en 10 categorías de negocio. El horizonte de predicción es de 6 meses, considerando que en el momento de la ejecución (mes X) no se dispone de los datos de ventas del mes en curso.

## 2. Objetivos y Alcance
* **Horizonte:** 6 meses ($X+1, X+2, X+3, X+4, X+5, X+6$).
* **Granularidad:** Mensual (agregada desde datos diarios).
* **Unidades:** Cantidad física de productos vendidos.
* **Restricción:** El último dato histórico disponible es del mes $X-1$.

## 3. Metodología de Modelado (Híbrida)
Basado en el "Sistema de Forecasting Multiple", utilizaremos:
1.  **Categoría A (Alta Prioridad):** Modelos individuales (Enfoque Directo para manejar la latencia).
2.  **Categoría B (Media Prioridad):** Modelos Multi-series por categoría de negocio.
3.  **Categoría C (Baja Prioridad/Cola Larga):** Modelo Global Único con variables categóricas.

## 4. Definición de Métricas (KPIs)
Para evaluar la precisión del modelo, se utilizarán las siguientes métricas:
* **WAPE (Global):** Métrica principal de desempeño del negocio.
* **MAE (Por Producto):** Error absoluto medio en unidades.
* **Bias (Sesgo):** $\frac{\sum(Forecast - Actual)}{\sum Actual}$. Un bias positivo indica sobre-stock; negativo indica quiebre de stock.

## 5. Estrategia de Validación (Backtesting)
Se utilizará **Time Series Cross-Validation** con una ventana deslizante de 6 meses.
* **Gap de Seguridad:** Se dejará un mes de "vacío" entre el conjunto de entrenamiento y el de prueba para simular la falta del mes $X$.
* **Folds:** Al menos 5 ventanas históricas para asegurar estabilidad estadística.

## 6. Variables Exógenas Identificadas
* Precios de venta y costos unitarios (Históricos).
* Eventos de Promoción (Binario).
* Campañas de Marketing (Categórico).
* Variables de Calendario (Mes, Trimestre, Festivos).

## 7. Cronograma de Fases
1.  **Fase 1: Planeación** (Estado: En curso)
2.  **Fase 2: Pipeline de Datos** (Transformación diaria -> mensual)
3.  **Fase 3: Segmentación ABC**
4.  **Fase 4: EDA**
5.  **Fase 5: Engineering** (Creación de Lags >= 2)
6.  **Fase 6: Modelado y Reconciliación**
7.  **Fase 7: Inferencia y Reporte**