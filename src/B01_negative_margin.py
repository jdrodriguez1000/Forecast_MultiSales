import pandas as pd
import numpy as np
import json
import os
from datetime import datetime

class MarginCorrector:
    def __init__(self, config):
        """
        Inicializa el corrector con la configuración del proyecto y
        prepara el diccionario de evidencia para el reporte JSON.
        """
        self.config = config
        self.reporte_evidencia = {
            "proceso": "Saneamiento e Imputación de Datos (A25)",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "cambios_estructurales": [],
            "detalles_correccion": []
        }

    def registrar_cambio_formato(self, tabla, columna, tipo_orig, tipo_nuevo):
        """
        Registra en la evidencia técnica los cambios de tipo de dato 
        (ej. de texto a datetime).
        """
        self.reporte_evidencia["cambios_estructurales"].append({
            "tabla": tabla,
            "columna": columna,
            "accion": "Conversion de Formato",
            "de": str(tipo_orig),
            "a": str(tipo_nuevo),
            "nota": "Estandarización para análisis temporal"
        })

    def corregir_margenes_inteligente(self, df_precios):
        """
        Detecta registros con margen negativo y decide si corregir 
        el precio o el costo basándose en la mediana del MISMO AÑO.
        """
        df = df_precios.copy()
        
        # 1. Identificar los registros con problemas (Precio < Costo)
        indices_problema = df[df['precio_venta_unitario'] < df['costo_unitario']].index
        
        if len(indices_problema) == 0:
            return df

        for idx in indices_problema:
            prod_id = df.loc[idx, 'producto_id']
            anio_error = df.loc[idx, 'año']
            precio_orig = float(df.loc[idx, 'precio_venta_unitario'])
            costo_orig = float(df.loc[idx, 'costo_unitario'])
            margen_orig = float(df.loc[idx, 'margen_unitario'])

            # 2. Obtener historial del mismo producto en el mismo año para comparar
            historial_anio = df[
                (df['producto_id'] == prod_id) & 
                (df['año'] == anio_error) & 
                (df['precio_venta_unitario'] >= df['costo_unitario'])
            ]
            
            # Si no hay historial sano ese año, usamos todo el historial del producto
            if historial_anio.empty:
                historial_ref = df[df['producto_id'] == prod_id]
            else:
                historial_ref = historial_anio

            # 3. Calcular medianas de referencia
            mediana_p = historial_ref['precio_venta_unitario'].median()
            mediana_c = historial_ref['costo_unitario'].median()

            # 4. Diagnóstico: ¿Quién se desvió más de su normalidad anual?
            desv_p = abs((precio_orig - mediana_p) / mediana_p) if mediana_p != 0 else 0
            desv_c = abs((costo_orig - mediana_c) / mediana_c) if mediana_c != 0 else 0

            # 5. Aplicar la corrección quirúrgica
            if desv_p > desv_c:
                df.loc[idx, 'precio_venta_unitario'] = mediana_p
                tipo_ajuste = f"Precio corregido (Mediana Anual {anio_error})"
            else:
                df.loc[idx, 'costo_unitario'] = mediana_c
                tipo_ajuste = f"Costo corregido (Mediana Anual {anio_error})"

            # 6. Guardar evidencia para el JSON
            self.reporte_evidencia["detalles_correccion"].append({
                "producto_id": int(prod_id),
                "fecha": str(df.loc[idx, 'fecha']),
                "año": int(anio_error),
                "diagnostico": tipo_ajuste,
                "antes": {"precio": precio_orig, "costo": costo_orig, "margen": margen_orig},
                "despues": {
                    "precio": float(df.loc[idx, 'precio_venta_unitario']),
                    "costo": float(df.loc[idx, 'costo_unitario']),
                    "margen": float(df.loc[idx, 'precio_venta_unitario'] - df.loc[idx, 'costo_unitario'])
                }
            })

        # 7. Recalcular campos derivados para mantener consistencia
        df['margen_unitario'] = df['precio_venta_unitario'] - df['costo_unitario']
        df['margen_porcentaje'] = df['margen_unitario'] / df['precio_venta_unitario'].replace(0, np.nan)
        
        return df

    def generar_reporte_evidencia(self):
        """Guarda la bitácora de cambios en un archivo JSON."""
        ruta_rep = self.config['paths'].get('outputs_reports', 'outputs/reports/')
        path_final = os.path.abspath(os.path.join(os.getcwd(), "..", ruta_rep, "b01_evidencia_margenes.json"))
        os.makedirs(os.path.dirname(path_final), exist_ok=True)
        
        with open(path_final, 'w', encoding='utf-8') as f:
            json.dump(self.reporte_evidencia, f, indent=4, ensure_ascii=False)
        return path_final