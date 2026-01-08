import pandas as pd
import yaml
import os
import json
from datetime import datetime

class DataManager:
    def __init__(self, config_path, base_path="../"):
        self.base_path = base_path
        with open(config_path, 'r', encoding='utf-8') as file:
            self.config = yaml.safe_load(file)
            
    def load_interim_data(self):
        path = os.path.join(self.base_path, self.config['paths']['interim_data'])
        df_ventas = pd.read_csv(os.path.join(path, self.config['paths']['files']['ventas']))
        df_precios = pd.read_csv(os.path.join(path, self.config['paths']['files']['precios']))
        
        date_col = self.config['column_mapping']['date_col']
        df_ventas[date_col] = pd.to_datetime(df_ventas[date_col])
        df_precios[date_col] = pd.to_datetime(df_precios[date_col])
        
        return df_ventas, df_precios

    def merge_data(self, df_ventas, df_precios):
        """Une ventas diarias con precios mensuales mediante broadcast."""
        id_col = self.config['column_mapping']['id_col']
        date_col = self.config['column_mapping']['date_col']
        
        # 1. Crear la llave temporal al inicio de mes usando el doble accesor .dt
        # Esto asegura que la fecha '2018-07-15' se convierta en '2018-07-01'
        df_ventas['temp_month'] = df_ventas[date_col].dt.to_period('M').dt.to_timestamp()
        
        # 2. Realizar el merge usando la llave del mes
        # Usamos left_on y right_on porque las columnas de unión tienen nombres distintos temporalmente
        df_merged = pd.merge(
            df_ventas, 
            df_precios, 
            left_on=[id_col, 'temp_month'],
            right_on=[id_col, date_col],
            how='left',
            suffixes=('', '_price_source')
        )
        
        # 3. Limpieza: eliminamos columnas auxiliares para mantener el dataset limpio
        cols_to_drop = ['temp_month']
        if date_col + '_price_source' in df_merged.columns:
            cols_to_drop.append(date_col + '_price_source')
            
        df_merged = df_merged.drop(columns=cols_to_drop)
        
        return df_merged

    def save_processed_data(self, df, filename=None):
        """Guarda en parquet usando la ruta base."""
        path = os.path.join(self.base_path, self.config['paths']['processed_data'])
        os.makedirs(path, exist_ok=True)
            
        out_name = filename or self.config['paths']['output_file']
        out_path = os.path.join(path, out_name)
        
        df.to_parquet(
            out_path, 
            engine=self.config['storage_options']['engine'], 
            compression=self.config['storage_options']['compression']
        )
        print(f"✅ Archivo guardado exitosamente en: {out_path}")
        

    def save_merge_log(self, df_ventas, df_precios, df_final, df_name="df_daily"):
        """Genera un log de auditoría detallado incluyendo el nombre del dataframe."""
        log_data = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "dataframe_name": df_name,  # <--- Nuevo campo solicitado
            "fuentes": {
                "ventas_diarias": {
                    "archivo": self.config['paths']['files']['ventas'],
                    "registros_iniciales": int(len(df_ventas))
                },
                "precios_mensuales": {
                    "archivo": self.config['paths']['files']['precios'],
                    "registros_iniciales": int(len(df_precios))
                }
            },
            "configuracion_union": {
                "tipo_join": "left",
                "llaves": [
                    self.config['column_mapping']['id_col'],
                    self.config['column_mapping']['date_col']
                ],
                "broadcast_temporal": "diario_hacia_inicio_mes"
            },
            "resultado": {
                "registros_finales": int(len(df_final)),
                "columnas_financieras": self.config['column_mapping']['financial_cols'],
                "nulos_detectados": df_final[self.config['column_mapping']['financial_cols']].isnull().sum().to_dict()
            }
        }

        # Rutas de salida para reportes
        report_dir = os.path.join(self.base_path, "outputs", "reports")
        report_name = "c05_status_transformation.json"
        report_path = os.path.join(report_dir, report_name)
        
        os.makedirs(report_dir, exist_ok=True)

        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=4, ensure_ascii=False)
        
        print(f"📝 Reporte de estado generado: {report_path}")