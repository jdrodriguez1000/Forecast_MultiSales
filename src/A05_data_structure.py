import pandas as pd
import json
import os
from datetime import datetime

class StructureValidator:
    def __init__(self, config):
        self.config = config
        self.report = {
            "proceso": "Validación de Estructura",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "estado_global": "Pendiente",
            "detalles": {}
        }

    def validar_columnas(self, df, nombre_tabla, columnas_esperadas):
        """Comprueba que los nombres de las columnas coincidan exactamente."""
        columnas_actuales = set(df.columns)
        esperadas = set(columnas_esperadas)
        
        faltantes = list(esperadas - columnas_actuales)
        extras = list(columnas_actuales - esperadas)
        
        exito = len(faltantes) == 0
        
        self.report["detalles"][nombre_tabla] = {
            "test_columnas": "Exitoso" if exito else "Fallido",
            "columnas_faltantes": faltantes,
            "columnas_extras": extras,
            "dtypes": df.dtypes.apply(lambda x: str(x)).to_dict()
        }
        
        if not exito:
            self.report["estado_global"] = "Error"
            raise ValueError(f"Faltan columnas en {nombre_tabla}: {faltantes}")
        
        return exito

    def generar_reporte_json(self):
        """Guarda el resultado en la ruta de reportes."""
        rel_path = self.config['paths'].get('outputs_reports', 'outputs/reports/')
        abs_path = os.path.abspath(os.path.join(os.getcwd(), "..", rel_path, "a05_status_structure.json"))
        
        if self.report["estado_global"] != "Error":
            self.report["estado_global"] = "Exitoso"
            
        with open(abs_path, 'w', encoding='utf-8') as f:
            json.dump(self.report, f, indent=4, ensure_ascii=False)
        return abs_path