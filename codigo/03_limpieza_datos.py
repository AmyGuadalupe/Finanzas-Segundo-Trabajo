# Autora: Amy Pamela Guadalupe Cordova
# Código de matrícula: 2024200501G
# Tema 79: Fondos mutuos en el Perú: rentabilidad y riesgo por tipo de fondo
# Fecha de extracción: 2026-11-19
"""Integra AAF (fondo/serie-mes) y BCRP (mes). No modifica crudos ni imputa.
Y: rent_mes. X1: vol12 rezagada. X2: var_tc. X3: retorno del mes anterior.
La rentabilidad rezagada solo usa el mes calendario inmediatamente anterior.
"""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import pandas as pd
import numpy as np
import unicodedata

RAIZ=Path(__file__).resolve().parents[1]; CR=RAIZ/'datos_crudos'; PR=RAIZ/'datos_procesados'; S=RAIZ/'salidas'; PR.mkdir(exist_ok=True);S.mkdir(exist_ok=True)
FECHA_INICIO='2019-01'; FECHA_CORTE='2025-12'; MINIMO=1000
VARIABLES=['rent_mes','vol12','var_tc','rent_lag1']

def anotar(s):
    linea=f'{datetime.now(timezone(timedelta(hours=-5))):%Y-%m-%d %H:%M:%S} | 03_limpieza | {s}'
    print(linea)
    with (RAIZ/'log_ejecucion.txt').open('a',encoding='utf-8') as f:f.write(linea+'\n')

def normalizar(s):
    return ' '.join(''.join(c for c in unicodedata.normalize('NFD',str(s)) if unicodedata.category(c)!='Mn').upper().split())

def main():
    a=pd.read_csv(CR/'datos_crudos_2024200501G_aaf.csv',dtype={'mes':str}).sort_values(['mes','denominacion_original','pagina'])
    b=pd.read_csv(CR/'datos_crudos_2024200501G_bcrp.csv',dtype={'valor_original':str})
    b['fecha']=pd.to_datetime(b.fecha);b['mes']=b.fecha.dt.to_period('M').astype(str)
    b['valor']=pd.to_numeric(b.valor_original,errors='coerce')
    # TC de fin de mes; interbancaria promedio de días observados, en cada moneda.
    m=b.groupby(['mes','variable']).valor.mean().unstack().sort_index().reindex(pd.period_range('2018-12',FECHA_CORTE,freq='M').astype(str))
    m.index.name='mes'
    m['var_tc']=np.log(m.tc_fin.where(m.tc_fin>0)).diff()
    for moneda in ['pen','usd']:
        m['rf_'+moneda]=(1+m['tasa_'+moneda]/100).where(m['tasa_'+moneda]>-100)**(1/12)-1
    m.reset_index().to_csv(S/'tabla_contexto_bcrp.csv',index=False,float_format='%.10g')
    for col in ['valor_cuota','rent_mes']:a[col]=pd.to_numeric(a[col],errors='coerce')
    a.loc[a.valor_cuota.le(0),'valor_cuota']=np.nan
    a['id_fondo_serie']=a.denominacion_original.map(normalizar)+' | '+a.moneda
    filtro=a.mes.between(FECHA_INICIO,FECHA_CORTE)&a.moneda.isin(['PEN','USD'])&a.rent_mes.ge(-1)&a.rent_mes.notna()
    a.loc[~filtro].to_csv(S/'filas_excluidas.csv',index=False)
    a=a.loc[filtro].copy()
    llave=['id_fondo_serie','mes']; valores=['tipo','valor_cuota','rent_mes']
    # Duplicados idénticos, no se suman. Duplicados conflictivos: se registran y excluyen.
    a=a.drop_duplicates(llave+valores)
    conflicto=a.duplicated(llave,keep=False)
    a.loc[conflicto].to_csv(S/'duplicados_conflictivos.csv',index=False)
    a=a.loc[~conflicto].copy()
    a=a.merge(m.reset_index(),on='mes',how='left',validate='many_to_one')
    a['rf_mensual']=np.where(a.moneda.eq('PEN'),a.rf_pen,a.rf_usd)
    a['exceso']=a.rent_mes-a.rf_mensual
    a['vol12']=np.nan
    a['rent_lag1']=np.nan
    # Ventana de 12 meses calendario previos, >=6 retornos observados; no usa el retorno actual.
    for _,g in a.groupby('id_fondo_serie',sort=False):
        s=g.set_index('mes').rent_mes.copy(); s.index=pd.PeriodIndex(s.index,freq='M')
        s=s.reindex(pd.period_range(s.index.min(),s.index.max(),freq='M'))
        v=s.shift(1).rolling(12,min_periods=6).std(ddof=1)
        a.loc[g.index,'vol12']=v.reindex(pd.PeriodIndex(g.mes,freq='M')).to_numpy()
        a.loc[g.index,'rent_lag1']=s.shift(1).reindex(pd.PeriodIndex(g.mes,freq='M')).to_numpy()
    # Atípicos: marca según tipo y moneda; no recorta pérdidas auténticas.
    grupo=a.groupby(['tipo','moneda']).rent_mes
    q1=grupo.transform(lambda s:s.quantile(.25));q3=grupo.transform(lambda s:s.quantile(.75));iqr=q3-q1
    a['atipico']=((iqr>0)&((a.rent_mes<q1-3*iqr)|(a.rent_mes>q3+3*iqr))).astype(int)
    a['imputado']=0
    a['muestra_modelo']=a[VARIABLES].notna().all(axis=1).astype(int)
    a=a.sort_values(llave).reset_index(drop=True)
    muestra=a[a.muestra_modelo.eq(1)]
    cobertura=pd.DataFrame([{'variable':v,'observaciones_validas':int(a[v].notna().sum()),'meses_distintos':int(a.loc[a[v].notna(),'mes'].nunique()),'observaciones_modelo':len(muestra)} for v in VARIABLES])
    cobertura.to_csv(S/'tabla_cobertura_variables.csv',index=False)
    a.groupby('mes').agg(filas=('id_fondo_serie','size'),unidades=('id_fondo_serie','nunique')).reset_index().to_csv(S/'tabla_cobertura_mensual.csv',index=False)
    print(cobertura.to_string(index=False))
    anotar(f'{len(a)} filas | {a.id_fondo_serie.nunique()} fondos/series identificados | {a.mes.nunique()} meses | {len(muestra)} filas completas')
    if (cobertura.observaciones_validas<=MINIMO).any() or len(muestra)<=MINIMO:
        raise RuntimeError('No se supera el mínimo de 1000 filas válidas por variable y completas en el modelo.')
    if muestra.mes.nunique()<24 or muestra.id_fondo_serie.nunique()<10:
        raise RuntimeError('Panel insuficiente para inferencia agrupada: menos de 24 meses o 10 unidades.')
    if a.exceso.notna().sum()<=MINIMO:raise RuntimeError('Cobertura insuficiente de tasas de referencia por moneda.')
    a.to_csv(PR/'datos_procesados_2024200501G.csv',index=False,float_format='%.12g')
    anotar('Base procesada guardada; datos crudos intactos.')

if __name__=='__main__':main()
