import pandas as pd
import json
import os
import numpy as np
from datetime import datetime

class QualityValidator:
    def __init__(self, config):
        self.config = config
        self.listas_centinela = config.get('centinelas', {})
        self.umbral_iqr = config.get('umbral_outliers', 1.5)
        self.reporte = {
            "proceso": "Auditoría Integral y Perfilamiento de Datos",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "inventario_categorico": {},
            "inventario_temporal": {}, 
            "resultados_criticos": {}
        }

    def ejecutar_auditoria(self, df, nombre_tabla):
        analisis_col = {}
        total_filas = len(df)
        
        # 1. IDENTIFICACIÓN DE COLUMNAS (Filtrando fechas de las categorías)
        cols_num = df.select_dtypes(include=[np.number]).columns
        cols_bool = df.select_dtypes(include=['bool']).columns
        
        # Filtro clave: Solo es categoría si es 'object' Y NO tiene la palabra 'fecha'
        cols_cat = [c for c in df.select_dtypes(include=['object', 'category']).columns 
                    if 'fecha' not in c.lower()]
        
        # Columnas de fecha
        cols_date = [c for c in df.columns if 'fecha' in c.lower()]

        # --- 2. INVENTARIO CATEGÓRICO (Solo Texto Real: Categoría, Producto, etc.) ---
        for col in cols_cat:
            counts = df[col].value_counts(dropna=False)
            dist = {str(k): {"conteo": int(v), "participacion": f"{round((v/total_filas)*100, 2)}%"} 
                    for k, v in counts.items()}
            self.reporte["inventario_categorico"].setdefault(nombre_tabla, {})[col] = dist

        # --- 3. INVENTARIO TEMPORAL (Agrupado por Año) ---
        for col in cols_date:
            # Forzamos conversión a fecha para que el reporte sea limpio
            temp_date = pd.to_datetime(df[col], errors='coerce')
            if temp_date.notnull().any():
                min_d = temp_date.min()
                max_d = temp_date.max()
                
                # Agrupamos por año para no tener mil filas
                year_counts = temp_date.dt.year.value_counts().sort_index()
                dist_anual = {str(int(y)): {"conteo": int(v), "participacion": f"{round((v/total_filas)*100, 2)}%"} 
                             for y, v in year_counts.items()}
                
                self.reporte["inventario_temporal"].setdefault(nombre_tabla, {})[col] = {
                    "fecha_inicio": str(min_d.date()),
                    "fecha_fin": str(max_d.date()),
                    "dias_de_cobertura_total": int((max_d - min_d).days),
                    "distribucion_anual": dist_anual
                }

        # --- 4. AUDITORÍA DE CALIDAD (Nulos, Centinelas, Outliers) ---
        for col in df.columns:
            resumen_col = {}
            # Nulos (Explícito)
            nulos = int(df[col].isnull().sum())
            resumen_col["nulos"] = f"{nulos}" if nulos > 0 else "No hay valores nulos"
            
            # Centinelas
            tipo_l = 'numeric' if col in cols_num else 'categorical'
            if col in cols_bool: tipo_l = 'boolean'
            if col in cols_date: tipo_l = 'date'
            l_check = self.listas_centinela.get(tipo_l, [])
            conteo_cent = {str(v): int((df[col] == v).sum()) for v in l_check if (df[col] == v).any()}
            resumen_col["centinelas_configurados"] = conteo_cent if conteo_cent else "No hay valores centinela"

            # Outliers (Direccionales)
            if col in cols_num and 'id' not in col.lower():
                q1, q3 = df[col].quantile(0.25), df[col].quantile(0.75)
                iqr = q3 - q1
                inf, sup = q1 - self.umbral_iqr * iqr, q3 + self.umbral_iqr * iqr
                c_inf, c_sup = int((df[col] < inf).sum()), int((df[col] > sup).sum())
                resumen_col["outliers_iqr"] = {
                    "total": c_inf + c_sup,
                    "fuera_inf": c_inf,
                    "fuera_sup": c_sup,
                    "lim_inf": round(float(inf), 2), 
                    "lim_sup": round(float(sup), 2)
                }
            else:
                resumen_col["outliers_iqr"] = "No aplica"
            
            analisis_col[col] = resumen_col

        self.reporte["resultados_criticos"][nombre_tabla] = {
            "duplicados": int(df.duplicated().sum()), 
            "detalle_columnas": analisis_col
        }
        return df

    def generar_reporte_json(self):
        # Aseguramos la ruta correcta según tu estructura
        ruta_rep = self.config['paths'].get('outputs_reports', 'outputs/reports/')
        path_final = os.path.abspath(os.path.join(os.getcwd(), "..", ruta_rep, "a10_status_quality.json"))
        os.makedirs(os.path.dirname(path_final), exist_ok=True)
        with open(path_final, 'w', encoding='utf-8') as f:
            json.dump(self.reporte, f, indent=4, ensure_ascii=False)
        return path_final