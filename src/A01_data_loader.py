import pandas as pd
import os
import json
from datetime import datetime

class DataLoader:
    def __init__(self, config):
        self.config = config
        self.report = {
            "proceso": "Carga de Datos Inicial",
            "timestamp_inicio": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "estado_global": "Iniciado",
            "archivos_procesados": {}
        }

    def cargar_csv(self, llave_config, nombre_amigable, nombre_df):
        """Lee el CSV y registra el nombre del DataFrame creado."""
        rel_path = self.config['paths'].get(llave_config)
        abs_path = os.path.abspath(os.path.join(os.getcwd(), "..", rel_path))

        try:
            if not os.path.exists(abs_path):
                raise FileNotFoundError(f"Archivo no encontrado: {abs_path}")

            # Creación del DataFrame
            df = pd.read_csv(abs_path)
            
            if df.empty:
                raise ValueError(f"El archivo está vacío: {abs_path}")

            # Registro detallado para el JSON incluyendo el nombre del DataFrame
            self.report["archivos_procesados"][nombre_amigable] = {
                "estado": "Exitoso",
                "dataframe_asignado": nombre_df,
                "filas": len(df),
                "columnas": list(df.columns),
                "ruta_origen": abs_path
            }
            return df

        except Exception as e:
            error_msg = f"ERROR en {nombre_amigable}: {str(e)}"
            self.report["archivos_procesados"][nombre_amigable] = {
                "estado": "Fallido", 
                "dataframe_intento": nombre_df,
                "error": error_msg
            }
            self.report["estado_global"] = "Error"
            raise Exception(error_msg)

    def generar_reporte_json(self):
        """Genera el reporte en outputs/reports/ indicando los nombres de los DataFrames."""
        try:
            # Recuperar ruta desde config.yaml: outputs_reports
            rel_report_path = self.config['paths'].get('outputs_reports', 'outputs/reports/')
            abs_output_path = os.path.abspath(os.path.join(os.getcwd(), "..", rel_report_path, 'a01_status_loader.json'))
            
            os.makedirs(os.path.dirname(abs_output_path), exist_ok=True)

            self.report["timestamp_fin"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if self.report["estado_global"] != "Error":
                self.report["estado_global"] = "Completado con Éxito"

            with open(abs_output_path, 'w', encoding='utf-8') as f:
                json.dump(self.report, f, indent=4, ensure_ascii=False)
            
            return abs_output_path
        except Exception as e:
            return f"Error al generar JSON: {str(e)}"