# Autora: Amy Pamela Guadalupe Cordova
# Código de matrícula: 2024200501G
# Tema 79: Fondos mutuos en el Perú: rentabilidad y riesgo por tipo de fondo
# Fecha de extracción: 2026-11-26
"""Construcción de panel mensual balanceado. Los originales nunca se alteran.
El criterio de selección es cobertura, no significancia ni R².
"""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import re, unicodedata
import numpy as np
import pandas as pd

RAIZ=Path(__file__).resolve().parents[1]; CR=RAIZ/'datos_crudos'; PR=RAIZ/'datos_procesados'; S=RAIZ/'salidas'; PR.mkdir(exist_ok=True); S.mkdir(exist_ok=True)
FECHA_INICIO='2019-01'; FECHA_CORTE='2025-12'; MINIMO=1000; META=4000
VARIABLES=['rent_mes','vol12','var_tc','rent_lag1']
MAX_HUECO=3; MAX_PROP=.15; HISTORIA=12; MIN_MESES=60

def anotar(s):
    linea=f'{datetime.now(timezone(timedelta(hours=-5))):%Y-%m-%d %H:%M:%S} | 03_limpieza | {s}'; print(linea)
    with (RAIZ/'log_ejecucion.txt').open('a',encoding='utf-8') as f:f.write(linea+'\n')

def normalizar(s):
    return ' '.join(''.join(c for c in unicodedata.normalize('NFKD',str(s)) if not unicodedata.combining(c)).upper().split())

# Alias de ADMINISTRADORAS, no de fondos distintos. Se conservan clases A/B/C y moneda.
ALIAS={'BBVA ASSET MANAGEMENT':'BBVA','BBVA SAF':'BBVA','CREDICORP CAPITAL':'CREDICORP','CREDICORP CAPITAL SAF':'CREDICORP','CREDICORP SAF':'CREDICORP','FONDOS SURA':'SURA','SURA':'SURA','SURA SAF':'SURA','FONDOS SURA SAF':'SURA','SCOTIA FONDOS':'SCOTIA','SCOTIA SAF':'SCOTIA','INTERFONDOS':'INTERFONDOS','INTERFONDO':'INTERFONDOS','FARO CAPITAL':'FARO CAPITAL','FARO CAPITAL SAFI':'FARO CAPITAL','ANDEAN CROWN':'ANDEAN CROWN','AC SAF':'ANDEAN CROWN','ANDEAN CROWN SAF S A C':'ANDEAN CROWN','BLUM SAF':'BLUM','BLUM':'BLUM','EL DORADO SAF':'EL DORADO','EL DORADO':'EL DORADO','DIVISO FONDOS':'DIVISO','DIVISO':'DIVISO','FLIP SAF':'FLIP','FLIP':'FLIP'}
def palabras(s):
    return ' '.join(re.sub(r'[^A-Z0-9$]+',' ',normalizar(s).replace('S/.',' SOLES ').replace('S/',' SOLES ')).split())

def identidad(fondo,admin,moneda):
    a=palabras(admin); a=ALIAS.get(a,a)
    if not a or a=='NAN':return None
    n=palabras(fondo)
    # Retirar únicamente etiquetas institucionales en los extremos, no palabras del nombre interno.
    opciones=sorted([k for k,v in ALIAS.items() if v==a],key=len,reverse=True)
    # Los prefijos con separador explícito aparecen en los boletines de 2025.
    f=normalizar(fondo)
    partes=re.split(r'\s*[-–—]\s*',f,maxsplit=1)
    if len(partes)==2 and ALIAS.get(palabras(partes[0]),palabras(partes[0]))==a:n=palabras(partes[1])
    for suf in opciones:
        if n.endswith(' '+suf):n=n[:-len(suf)].strip();break
    n=re.sub(r'\bFMIV\b','',n); n=re.sub(r'\bFM\b','',n)
    n=' '.join(n.split())
    # Etiqueta genérica de categoría repetida por la publicación, no distingue una clase.
    n=re.sub(r'^FONDOS? DE FONDOS?\s+', '',n)
    # Quitar únicamente el nombre completo de la misma administradora cuando
    # está repetido como marca inicial; se mantiene el identificador del gestor.
    for pref in opciones:
        if n.startswith(pref+' ') and len(n[len(pref):].strip())>=4:
            n=n[len(pref):].strip();break
    if not n or n==a or n in opciones or len(n)<3:return None
    # Continuidad documentada de la clase A: la clase B se creó el 16/05/2025.
    # Fuente: https://www.fondossura.pe/productos (consulta 20/11/2026).
    # Solo los cuatro nombres exactos, sin fusionar la clase B.
    if a=='SURA' and n in {'CORTO PLAZO SOLES','CORTO PLAZO DOLARES','ULTRA CASH SOLES','ULTRA CASH DOLARES'}:
        n+=' SERIE A'
    return a+' | '+n+' | '+moneda

def completar(g,cal):
    """Vacíos internos <=3 meses y <=15% del historial. No extrapola.
    Retorno faltante: tasa geométrica residual de cuotas que respeta el retorno
    publicado del mes posterior. No usar si el salto implícito es desmesurado.
    El retorno publicado del mes siguiente se conserva. La cuota es estimada.
    """
    g=g.set_index('mes').reindex(cal).copy(); g.index.name='mes'
    g['imputado']=0
    presentes=g.rent_mes.notna()&g.valor_cuota.notna()
    if not presentes.any():return g.iloc[:0]
    pos=np.flatnonzero(presentes);g=g.iloc[pos[0]:pos[-1]+1].copy()
    missing=~(g.rent_mes.notna()&g.valor_cuota.notna())
    # Solo faltas de fila completa o de una cuota; no sustituir rentabilidad observada.
    for _,bloque in g[missing].groupby((missing!=missing.shift()).cumsum()):
        indices=list(bloque.index);k=len(indices);i=g.index.get_loc(indices[0]);j=i+k
        if k>MAX_HUECO or i==0 or j>=len(g):continue
        a,b=g.iloc[i-1],g.iloc[j]
        if pd.isna(a.valor_cuota) or pd.isna(b.valor_cuota) or not (-1<b.rent_mes):continue
        if bloque.rent_mes.notna().any() or bloque.valor_cuota.notna().any():continue
        factor=b.valor_cuota/a.valor_cuota/(1+b.rent_mes)
        if not np.isfinite(factor) or factor<=0:continue
        r=factor**(1/k)-1
        if abs(r)>=.50:continue
        for q,m in enumerate(indices,1):
            g.loc[m,'rent_mes']=r;g.loc[m,'valor_cuota']=a.valor_cuota*(1+r)**q;g.loc[m,'imputado']=1
            g.loc[m,['tipo','moneda','fondo','administradora','id_fondo_serie']]=a[['tipo','moneda','fondo','administradora','id_fondo_serie']].values
            g.loc[m,'denominacion_original']='ESTIMADO: '+str(a.denominacion_original);g.loc[m,'archivo']='INTERPOLACION';g.loc[m,'pagina']=0;g.loc[m,'fila_original']=f'Estimación geométrica entre {a.name} y {b.name}; cuota final y retorno posterior observados';g.loc[m,'estado']='estimado'
    return g

def main():
    a=pd.read_csv(CR/'datos_crudos_2024200501G_aaf.csv',dtype={'mes':str}); b=pd.read_csv(CR/'datos_crudos_2024200501G_bcrp.csv',dtype={'valor_original':str});b['fecha']=pd.to_datetime(b.fecha);b['mes']=b.fecha.dt.to_period('M').astype(str);b['valor']=pd.to_numeric(b.valor_original,errors='coerce')
    cal=pd.period_range(FECHA_INICIO,FECHA_CORTE,freq='M').astype(str)
    m=b.groupby(['mes','variable']).valor.mean().unstack().sort_index().reindex(pd.period_range('2018-12',FECHA_CORTE,freq='M').astype(str));m.index.name='mes';m['var_tc']=np.log(m.tc_fin.where(m.tc_fin>0)).diff()
    for mon in ['pen','usd']:m['rf_'+mon]=(1+m['tasa_'+mon]/100).where(m['tasa_'+mon]>-100)**(1/12)-1
    m.reset_index().to_csv(S/'tabla_contexto_bcrp.csv',index=False,float_format='%.12g')
    for col in ['rent_mes','valor_cuota']:a[col]=pd.to_numeric(a[col],errors='coerce')
    a['id_fondo_serie']=[identidad(f,z,c) for f,z,c in zip(a.fondo,a.administradora,a.moneda)]
    valido=a.id_fondo_serie.notna()&a.valor_cuota.gt(0)&a.rent_mes.ge(-1)&a.moneda.isin(['PEN','USD'])&a.mes.isin(cal)
    a.loc[~valido].to_csv(S/'filas_excluidas.csv',index=False);a=a[valido].copy()
    a[['mes','denominacion_original','id_fondo_serie','tipo','moneda']].drop_duplicates().sort_values(['id_fondo_serie','mes']).to_csv(S/'tabla_homologacion.csv',index=False)
    llave=['id_fondo_serie','mes'];a=a.drop_duplicates(llave+['tipo','valor_cuota','rent_mes']);conf=a.duplicated(llave,keep=False);a[conf].to_csv(S/'duplicados_conflictivos.csv',index=False);a=a[~conf].copy()
    # No mezclar una serie reclasificada: la clase y moneda deben ser estables.
    a=a[a.groupby('id_fondo_serie').tipo.transform('nunique').eq(1)].copy()
    a.to_csv(PR/'base_integrada_observada.csv',index=False,float_format='%.12g')
    grupos=[]
    for id_,g in a.groupby('id_fondo_serie',sort=True):
        h=completar(g,cal).reindex(cal);h.index.name='mes';h['id_fondo_serie']=id_;grupos.append(h.reset_index())
    d=pd.concat(grupos,ignore_index=True);d=d.merge(m.reset_index(),on='mes',how='left',validate='many_to_one');d['rf_mensual']=np.where(d.moneda.eq('PEN'),d.rf_pen,d.rf_usd)
    # Winsorizar rentabilidades, no cuotas. Límites por tipo/moneda calculados SOLO con observaciones originales.
    d['rent_original']=d.rent_mes
    referencia=d[d.imputado.eq(0)&d.rent_mes.notna()].groupby(['tipo','moneda']).rent_mes.quantile([.25,.75]).unstack();referencia.columns=['q1','q3'];referencia['lim_inf']=(referencia.q1-3*(referencia.q3-referencia.q1)).clip(lower=-1);referencia['lim_sup']=referencia.q3+3*(referencia.q3-referencia.q1)
    # Si RIC=0, no recortar sin dispersión identificada.
    referencia.loc[referencia.q1.eq(referencia.q3),['lim_inf','lim_sup']]=[-1,np.inf]
    referencia.reset_index().to_csv(S/'tabla_limites_tukey.csv',index=False,float_format='%.12g')
    d=d.merge(referencia.reset_index(),on=['tipo','moneda'],how='left',validate='many_to_one');d['rent_mes']=d.rent_original.clip(d.lim_inf,d.lim_sup);d['atipico']=(d.rent_original.notna()&d.rent_mes.ne(d.rent_original)).astype(int);d['exceso']=d.rent_mes-d.rf_mensual
    d=d.sort_values(['id_fondo_serie','mes']);g=d.groupby('id_fondo_serie',sort=False)
    d['vol12']=g.rent_mes.transform(lambda z:z.shift().rolling(HISTORIA,min_periods=6).std());d['rent_lag1']=g.rent_mes.shift();d['vol12_original']=g.rent_original.transform(lambda z:z.shift().rolling(HISTORIA,min_periods=6).std());d['rent_lag1_original']=g.rent_original.shift();d['historia_n']=g.rent_original.transform(lambda z:z.shift().rolling(HISTORIA,min_periods=1).count());d['historia_imputada']=g.imputado.transform(lambda z:z.shift().rolling(HISTORIA,min_periods=6).sum());d['historia_atipica']=g.atipico.transform(lambda z:z.shift().rolling(HISTORIA,min_periods=6).sum())
    # Selección por disponibilidad; se evalúan ventanas de >=60 meses; meta mínima de 4000 filas.
    requeridas=VARIABLES+['valor_cuota','rf_mensual','rent_original','vol12_original','rent_lag1_original','historia_imputada','historia_atipica','historia_n','tipo','moneda','fondo','administradora','archivo','pagina','fila_original','denominacion_original','estado','tc_fin','tasa_pen','tasa_usd','rf_pen','rf_usd','exceso','atipico','imputado']
    d['completo']=d[requeridas].notna().all(axis=1)&np.isfinite(d[VARIABLES]).all(axis=1)
    ids=d.id_fondo_serie.unique();c=d.pivot(index='id_fondo_serie',columns='mes',values='completo').reindex(index=ids,columns=cal).to_numpy(dtype=bool);imp=d.pivot(index='id_fondo_serie',columns='mes',values='imputado').reindex(index=ids,columns=cal).fillna(0).to_numpy();hist=d.pivot(index='id_fondo_serie',columns='mes',values='historia_imputada').reindex(index=ids,columns=cal).fillna(999).to_numpy();nh=d.pivot(index='id_fondo_serie',columns='mes',values='historia_n').reindex(index=ids,columns=cal).fillna(0).to_numpy();tip=d.dropna(subset=['tipo']).drop_duplicates('id_fondo_serie').set_index('id_fondo_serie').tipo.reindex(ids).to_numpy()
    candidatos=[];mejor=None
    for i in range(len(cal)):
        for j in range(i+MIN_MESES,len(cal)+1):
            t=j-i; ok=c[:,i:j].all(axis=1)&((imp[:,i:j].sum(axis=1)+hist[:,i])/(t+nh[:,i])<=MAX_PROP);n=int(ok.sum());nfil=n*t;nt=len(set(tip[ok]));
            if nfil<=MINIMO or nt<4:continue
            candidatos.append(dict(inicio=cal[i],fin=cal[j-1],meses=t,series=n,filas=nfil,tipos=nt))
            # Prioridad: cumplir 60 meses y 4000 filas; después maximizar cobertura por tipos y filas.
            prioridad=(int(t>=60 and nfil>=META),int(nfil>=META),nt,nfil,t)
            if mejor is None or prioridad>mejor[0]:mejor=(prioridad,i,j,ok)
    pd.DataFrame(candidatos).to_csv(S/'tabla_ventanas_candidatas.csv',index=False)
    if mejor is None:raise RuntimeError('No hay panel balanceado con cobertura suficiente. No se rellena artificialmente.')
    _,i,j,ok=mejor;final=d[d.id_fondo_serie.isin(ids[ok])&d.mes.isin(cal[i:j])].copy();final['muestra_modelo']=1
    cols=['mes','tipo','fondo','administradora','denominacion_original','moneda','estado','valor_cuota','rent_mes','archivo','pagina','fila_original','id_fondo_serie','tasa_pen','tasa_usd','tc_fin','var_tc','rf_pen','rf_usd','rf_mensual','exceso','vol12','rent_lag1','atipico','imputado','muestra_modelo','rent_original','vol12_original','rent_lag1_original','historia_imputada','historia_atipica','historia_n']
    final=final[cols].sort_values(llave).reset_index(drop=True)
    assert not final.isna().any().any() and not final.duplicated(llave).any() and final.groupby('id_fondo_serie').mes.nunique().eq(j-i).all() and len(final)==ok.sum()*(j-i)
    pd.DataFrame({'id_fondo_serie':ids,'tipo':tip,'seleccionado':ok.astype(int)}).to_csv(S/'tabla_seleccion_series.csv',index=False)
    final.to_csv(PR/'datos_procesados_2024200501G.csv',index=False,float_format='%.12g');d[d.atipico.eq(1)|d.imputado.eq(1)][['mes','id_fondo_serie','tipo','moneda','rent_original','rent_mes','valor_cuota','atipico','imputado','archivo','pagina','fila_original']].to_csv(S/'tabla_tratamientos.csv',index=False,float_format='%.12g')
    pd.DataFrame([{'variable':v,'observaciones_validas':len(final),'meses_distintos':j-i,'observaciones_modelo':len(final)} for v in VARIABLES]).to_csv(S/'tabla_cobertura_variables.csv',index=False)
    final.groupby('mes').agg(filas=('id_fondo_serie','size'),unidades=('id_fondo_serie','nunique'),imputadas=('imputado','sum'),winsorizadas=('atipico','sum')).reset_index().to_csv(S/'tabla_cobertura_mensual.csv',index=False)
    anotar(f'Panel balanceado {cal[i]} a {cal[j-1]}: {len(final)} filas, {ok.sum()} series, {j-i} meses; {int(final.imputado.sum())} interpoladas; {int(final.atipico.sum())} winsorizadas; 0 faltantes.')
    if len(final)<META:raise RuntimeError('El panel no alcanza la meta de 4000 filas; no publicar una muestra inferior sin revisión.')
    print(final.groupby('tipo').id_fondo_serie.nunique().to_string())
if __name__=='__main__':main()
