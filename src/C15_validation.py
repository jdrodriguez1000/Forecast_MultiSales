# ==============================================================================
# Archivo: C15_validation.py (Versión Corregida para JSON)
# Propósito: Suite de validación con tipos compatibles para serialización
# ==============================================================================
import pandas as pd
import numpy as np
from datetime import datetime
import json
import os 

class DataValidator:
    def __init__(self, config):
        self.config = config
        self.report = {}

    def validate_structure(self, df):
        conf = self.config['column_mapping']
        expected_cols = [conf['date_col'], conf['id_col'], conf['target_col']] + conf['financial_cols']
        
        missing_cols = [col for col in expected_cols if col not in df.columns]
        is_date_correct = pd.api.types.is_datetime64_any_dtype(df[conf['date_col']])
        
        # Convertimos a bool nativo de Python
        self.report['estructura'] = {
            "columnas_faltantes": missing_cols,
            "formato_fecha_ok": bool(is_date_correct),
            "dimensiones": list(df.shape)
        }
        return len(missing_cols) == 0 and bool(is_date_correct)

    def validate_consistency(self, df_daily, df_monthly):
        conf = self.config['column_mapping']
        target_col = conf['target_col']
        id_col = conf['id_col']
        date_col = conf['date_col']
        
        sum_daily = float(df_daily[target_col].sum())
        sum_monthly = float(df_monthly[target_col].sum())
        diff_units = abs(sum_daily - sum_monthly)
        
        # Detección de gaps
        gaps = []
        for pid, group in df_monthly.groupby(id_col):
            expected_range = pd.date_range(start=group[date_col].min(), 
                                          end=group[date_col].max(), 
                                          freq='MS')
            if len(group) != len(expected_range):
                gaps.append(int(pid)) # Asegurar que el ID sea int nativo

        self.report['consistencia'] = {
            "diferencia_unidades": round(diff_units, 4),
            "productos_con_gaps": len(gaps),
            "balance_ok": bool(diff_units < 1e-4)
        }
        return self.report['consistencia']['balance_ok'] and len(gaps) == 0

    def validate_quality(self, df):
        activity_col = self.config['transformation_params']['new_col_activity']
        
        # Forzamos int() para evitar tipos de numpy
        nulls = int(df.isnull().sum().sum())
        dups = int(df.duplicated().sum())
        
        out_of_range = df[(df[activity_col] < 0) | (df[activity_col] > 31)]
        
        self.report['calidad'] = {
            "total_nulos": nulls,
            "total_duplicados": dups,
            "errores_rango_actividad": int(len(out_of_range))
        }
        return nulls == 0 and dups == 0 and len(out_of_range) == 0

    def validate_business(self, df):
        precio_col = self.config['column_mapping']['financial_cols'][0]
        costo_col = self.config['column_mapping']['financial_cols'][1]
        
        neg_margin = df[df[precio_col] < df[costo_col]]
        
        self.report['negocio'] = {
            "margenes_negativos": int(len(neg_margin)),
            "max_perdida_unitaria": float( (df[precio_col] - df[costo_col]).min() ) if not neg_margin.empty else 0.0
        }
        return len(neg_margin) == 0
    
    def save_report(self, df_name, base_path):
        """Genera el archivo C15_status_validation.json con los resultados."""
        report_dir = os.path.join(base_path, "outputs", "reports")
        report_path = os.path.join(report_dir, "c15_status_validation.json")
        os.makedirs(report_dir, exist_ok=True)
        
        # Lógica de estado final
        all_ok = (
            self.report['estructura']['formato_fecha_ok'] and 
            not self.report['estructura']['columnas_faltantes'] and
            self.report['consistencia']['balance_ok'] and
            self.report['consistencia']['productos_con_gaps'] == 0 and
            self.report['calidad']['total_nulos'] == 0 and
            self.report['negocio']['margenes_negativos'] == 0
        )

        final_report = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "target_dataframe": df_name,
            "validacion_detallada": self.report,
            "estado_final": "VALIDADO" if all_ok else "REVISIÓN REQUERIDA"
        }

        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(final_report, f, indent=4, ensure_ascii=False)
        
        print(f"📝 Reporte de validación C15 generado en: {report_path}")