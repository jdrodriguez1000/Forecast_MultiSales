import pandas as pd
import json
import os
from datetime import datetime

class ConsistencyValidator:
    def __init__(self, config):
        self.config = config
        self.reporte = {
            "proceso": "Auditoría de Consistencia Inter-Tablas",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "resultados": {}
        }

    def validar_integridad_referencial(self, df_hijo, df_padre, llave, nombre_relacion):
        """Verifica que todos los IDs en la tabla de ventas existan en la tabla maestra."""
        ids_hijo = set(df_hijo[llave].unique())
        ids_padre = set(df_padre[llave].unique())
        
        huerfanos = ids_hijo - ids_padre
        exito = len(huerfanos) == 0
        
        resultado = {
            "estado": "Consistente" if exito else "Inconsistente",
            "ids_huerfanos_detectados": list(huerfanos) if not exito else "Ninguno"
        }
        self.reporte["resultados"][nombre_relacion] = resultado
        return exito

    def validar_continuidad_temporal(self, df, nombre_tabla):
        """Verifica si faltan días en el rango de fechas para la serie de tiempo."""
        df['fecha'] = pd.to_datetime(df['fecha'])
        min_date = df['fecha'].min()
        max_date = df['fecha'].max()
        
        # Crear el rango teórico completo
        rango_teorico = pd.date_range(start=min_date, end=max_date)
        dias_reales = df['fecha'].unique()
        
        faltantes = len(rango_teorico) - len(dias_reales)
        
        resultado = {
            "rango_detectado": f"{min_date.date()} a {max_date.date()}",
            "dias_calendario_faltantes": int(faltantes) if faltantes > 0 else "Serie completa"
        }
        self.reporte["resultados"][f"Continuidad_{nombre_tabla}"] = resultado
        return faltantes == 0

    def generar_reporte_json(self):
        ruta_rep = self.config['paths'].get('outputs_reports', 'outputs/reports/')
        path_final = os.path.abspath(os.path.join(os.getcwd(), "..", ruta_rep, "a15_status_consistency.json"))
        
        os.makedirs(os.path.dirname(path_final), exist_ok=True)
        with open(path_final, 'w', encoding='utf-8') as f:
            json.dump(self.reporte, f, indent=4, ensure_ascii=False)
        return path_final