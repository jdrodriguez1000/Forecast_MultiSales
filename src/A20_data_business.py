import pandas as pd
import json
import os
from datetime import datetime

class BusinessValidator:
    def __init__(self, config):
        self.config = config
        self.reporte = {
            "proceso": "Auditoría de Lógica de Negocio",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "resultados": {}
        }

    def validar_margenes(self, df_precios, nombre_df):
        """Detecta márgenes negativos y extrae un ejemplo real del error."""
        # Regla de negocio: Precio de venta debe ser estrictamente mayor al costo
        anomalias = df_precios[df_precios['precio_venta_unitario'] <= df_precios['costo_unitario']]
        
        conteo = len(anomalias)
        # Extraemos la primera fila como ejemplo (convertida a diccionario)
        ejemplo = anomalias.head(1).to_dict(orient='records')[0] if conteo > 0 else "Sin anomalías"
        
        self.reporte["resultados"]["Margenes_Negativos"] = {
            "estado": "Alerta" if conteo > 0 else "OK",
            "dataframe_origen": nombre_df,
            "registros_afectados": conteo,
            "registro_ejemplo": ejemplo
        }
        return conteo == 0

    def validar_inactividad(self, df_ventas, nombre_df):
        """Detecta productos sin ventas basándose en el límite del config.yaml."""
        # Extraer el límite del archivo YAML
        reglas = self.config.get('business_rules', {})
        dias_limite = reglas.get('inactivity_limit_days', 90) # 90 es el valor por defecto
        
        ultima_fecha_global = pd.to_datetime(df_ventas['fecha']).max()
        
        # Agrupamos para ver la última venta de cada producto
        ultimas_ventas = df_ventas[df_ventas['ventas_diarias'] > 0].groupby('producto_id')['fecha'].max()
        ultimas_ventas = pd.to_datetime(ultimas_ventas)
        
        # Calculamos días desde la última venta
        inactividad = (ultima_fecha_global - ultimas_ventas).dt.days
        productos_afectados_serie = inactividad[inactividad > dias_limite]
        
        conteo = len(productos_afectados_serie)
        
        ejemplo = "Sin anomalías"
        if conteo > 0:
            id_ejemplo = productos_afectados_serie.index[0]
            ejemplo = df_ventas[df_ventas['producto_id'] == id_ejemplo].tail(1).to_dict(orient='records')[0]
            ejemplo['dias_inactivo_calculados'] = int(productos_afectados_serie.iloc[0])

        self.reporte["resultados"]["Inactividad_Prolongada"] = {
            "estado": "Informativo" if conteo > 0 else "OK",
            "dataframe_origen": nombre_df,
            "limite_dias_usado": dias_limite,
            "productos_afectados": conteo,
            "registro_ejemplo": ejemplo
        }
        return conteo == 0

    def generar_reporte_json(self):
        ruta_rep = self.config['paths'].get('outputs_reports', 'outputs/reports/')
        path_final = os.path.abspath(os.path.join(os.getcwd(), "..", ruta_rep, "a20_status_business.json"))
        os.makedirs(os.path.dirname(path_final), exist_ok=True)
        with open(path_final, 'w', encoding='utf-8') as f:
            json.dump(self.reporte, f, indent=4, ensure_ascii=False)
        return path_final