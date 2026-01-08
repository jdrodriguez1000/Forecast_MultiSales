# ==============================================================================
# Archivo: C10_transformation.py
# Propósito: Transformación de granularidad y cálculo de métricas ponderadas
# ==============================================================================
import pandas as pd
import numpy as np

class TimeSeriesTransformer:
    def __init__(self, config):
        """Inicializa el transformador con la configuración del proyecto."""
        self.config = config

    def aggregate_to_monthly(self, df):
        """Convierte datos diarios a mensuales con rigor financiero."""
        conf = self.config['column_mapping']
        trans = self.config['transformation_params']
        
        # Extraer nombres de columnas del config
        date_col = conf['date_col']
        id_col = conf['id_col']
        target_col = conf['target_col']
        fin_cols = conf['financial_cols']
        
        df = df.copy()
        
        # 1. Crear el índice mensual (Month Start)
        df['month_index'] = df[date_col].dt.to_period('M').dt.to_timestamp()
        
        # 2. Preparar los numeradores para promedios ponderados (Precio * Unidades)
        # Esto nos permite calcular el valor total vendido antes de agrupar
        for col in fin_cols:
            df[f'_total_{col}'] = df[target_col] * df[col]
            
        # 3. Definir el diccionario de agregación
        # Unidades se suman, los totales financieros también (para luego promediar)
        agg_dict = {target_col: 'sum'}
        for col in fin_cols:
            agg_dict[f'_total_{col}'] = 'sum'
            
        # 4. Agregación principal por Producto y Mes
        df_monthly = df.groupby([id_col, 'month_index']).agg(agg_dict).reset_index()
        
        # 5. Calcular los promedios ponderados finales
        # Precio Mensual = Suma(Ventas * Precio) / Total Ventas Mensuales
        for col in fin_cols:
            # Evitar división por cero si un mes no tuvo ventas
            df_monthly[col] = np.where(
                df_monthly[target_col] > 0,
                df_monthly[f'_total_{col}'] / df_monthly[target_col],
                0
            )
            df_monthly.drop(columns=[f'_total_{col}'], inplace=True)
            
        # 6. Cálculo de la columna solicitada: dias_con_venta
        # Contamos cuántas fechas únicas tienen ventas > 0 por producto/mes
        df_activity = (
            df[df[target_col] > 0]
            .groupby([id_col, 'month_index'])
            .size()
            .reset_index(name=trans['new_col_activity'])
        )
        
        # 7. Unir actividad con el dataframe mensual
        df_monthly = pd.merge(
            df_monthly, 
            df_activity, 
            on=[id_col, 'month_index'], 
            how='left'
        ).fillna({trans['new_col_activity']: 0})
        
        # Renombrar columna de fecha a su nombre original
        df_monthly.rename(columns={'month_index': date_col}, inplace=True)
        
        return df_monthly