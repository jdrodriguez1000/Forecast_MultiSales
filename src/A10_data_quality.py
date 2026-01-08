import pandas as pd
import json
import os
import numpy as np
from datetime import datetime

class QualityValidator:
    def __init__(self, config):
        """
        Inicializa el validador con la configuración del proyecto.
        """
        self.config = config
        self.listas_centinela = config.get('centinelas', {})
        self.umbral_iqr = config.get('umbral_outliers', 1.5)
        self.reporte = {
            "proceso": "Auditoría Integral de Calidad con Direccionalidad de Outliers",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "resultados": {}
        }

    def ejecutar_auditoria(self, df, nombre_tabla):
        """
        Realiza un escaneo 360° incluyendo la dirección de los outliers.
        """
        analisis_col = {}
        
        # 1. Validación de Duplicados en la Tabla
        total_duplicados = int(df.duplicated().sum())
        msg_duplicados = f"{total_duplicados}" if total_duplicados > 0 else "No se encontraron duplicados"

        # Clasificación de columnas
        cols_num = df.select_dtypes(include=[np.number]).columns
        cols_cat = df.select_dtypes(include=['object']).columns
        cols_bool = df.select_dtypes(include=['bool']).columns
        cols_date = [c for c in df.columns if 'fecha' in c.lower()]

        for col in df.columns:
            resumen_col = {}
            
            # --- A. NULOS ---
            nulos = int(df[col].isnull().sum())
            resumen_col["nulos"] = f"{nulos}" if nulos > 0 else "No hay valores nulos"

            # --- B. CENTINELAS ---
            tipo_lista = 'numeric' if col in cols_num else 'categorical'
            if col in cols_bool: tipo_lista = 'boolean'
            if col in cols_date: tipo_lista = 'date'
            
            lista_check = self.listas_centinela.get(tipo_lista, [])
            conteo_cent = {str(v): int((df[col] == v).sum()) for v in lista_check if (df[col] == v).any()}
            resumen_col["centinelas"] = conteo_cent if conteo_cent else "No hay valores centinela"

            # --- C. OUTLIERS (IQR) CON DIRECCIONALIDAD ---
            if col in cols_num and 'id' not in col.lower():
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1
                
                l_inf = Q1 - self.umbral_iqr * IQR
                l_sup = Q3 + self.umbral_iqr * IQR
                
                # Conteo direccional
                out_inf = int((df[col] < l_inf).sum())
                out_sup = int((df[col] > l_sup).sum())
                total_out = out_inf + out_sup
                
                resumen_col["outliers_iqr"] = {
                    "estado": "Hallazgos detectados" if total_out > 0 else "No hay outliers",
                    "conteo_total": total_out,
                    "fuera_limite_inferior": out_inf if out_inf > 0 else "No se encontraron",
                    "fuera_limite_superior": out_sup if out_sup > 0 else "No se encontraron",
                    "limite_inferior_permitido": round(float(l_inf), 2),
                    "limite_superior_permitido": round(float(l_sup), 2)
                }
            else:
                resumen_col["outliers_iqr"] = "No aplica (Columna no numérica o identificador)"

            analisis_col[col] = resumen_col

        self.reporte["resultados"][nombre_tabla] = {
            "duplicados_en_tabla": msg_duplicados,
            "detalle_por_columna": analisis_col
        }
        return df

    def generar_reporte_json(self):
        try:
            ruta_rep = self.config['paths'].get('outputs_reports', 'outputs/reports/')
            path_final = os.path.abspath(os.path.join(os.getcwd(), "..", ruta_rep, "a10_status_quality.json"))
            os.makedirs(os.path.dirname(path_final), exist_ok=True)
            with open(path_final, 'w', encoding='utf-8') as f:
                json.dump(self.reporte, f, indent=4, ensure_ascii=False)
            return path_final
        except Exception as e:
            return f"Error crítico: {str(e)}"