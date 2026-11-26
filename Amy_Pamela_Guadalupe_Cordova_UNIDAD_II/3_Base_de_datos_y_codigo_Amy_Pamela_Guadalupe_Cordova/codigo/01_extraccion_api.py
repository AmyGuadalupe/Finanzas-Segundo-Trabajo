# Autora: Amy Pamela Guadalupe Cordova
# Código de matrícula: 2024200501G
# Tema 79: Fondos mutuos en el Perú: rentabilidad y riesgo por tipo de fondo
# Fecha de extracción: 2026-11-20
"""Vía API BCRPData. Una consulta por serie; guarda JSON original y CSV.
--local: reconstruye exclusivamente desde los JSON incluidos. --demo: consulta
el tramo de cierre y coteja diez valores disponibles, sin sobrescribir crudos.
"""
import argparse, hashlib, json, time, re
from datetime import datetime, timezone, timedelta
from pathlib import Path
import pandas as pd
import requests

RAIZ = Path(__file__).resolve().parents[1]
DIR = RAIZ / 'datos_crudos' / 'api'
DIR.mkdir(parents=True, exist_ok=True)
FECHA_INICIO = '2018-12-01'  # mes previo para variación de enero de 2019
FECHA_CORTE = '2025-12-31'
BASE = 'https://estadisticas.bcrp.gob.pe/estadisticas/series/api'
UA = 'UNCP-FinanzasI/1.0 (investigacion academica; contacto: e_2024200501g@uncp.edu.pe)'
SERIES = {
    'PN01216PM': ('tc_fin', 'mensual', 'interbancario', 'S/ por USD'),
    'PD04692MD': ('tasa_pen', 'diaria', 'interbancaria', '% anual'),
    'PD04693MD': ('tasa_usd', 'diaria', 'interbancaria', '% anual'),
}
MESES = {m:i for i,m in enumerate('ene feb mar abr may jun jul ago set oct nov dic'.split(),1)}
MESES['sep'] = 9

def anotar(s):
    linea = f'{datetime.now(timezone(timedelta(hours=-5))):%Y-%m-%d %H:%M:%S} | 01_api | {s}'
    print(linea)
    with (RAIZ/'log_ejecucion.txt').open('a',encoding='utf-8') as f: f.write(linea+'\n')

def url(codigo, inicio=FECHA_INICIO, fin=FECHA_CORTE):
    """Construye el endpoint con fecha fija y formato compatible con la frecuencia."""
    if SERIES[codigo][1]=='mensual': inicio,fin=inicio[:7],fin[:7]
    return f'{BASE}/{codigo}/json/{inicio}/{fin}/esp'

def consultar(direccion):
    """Respeta la pausa entre solicitudes y registra el código HTTP antes de guardar."""
    time.sleep(1.5)
    r=requests.get(direccion,headers={'User-Agent':UA},timeout=90)
    anotar(f'HTTP {r.status_code} | {direccion}')
    r.raise_for_status()
    return r.content

def fecha(texto):
    # Formatos BCRP: Ene.2019, Ene19 y 02.Ene.2019.
    s=str(texto).strip().lower()
    m=re.fullmatch(r'(?:(\d{1,2})[. /-]*)?([a-záéíóú]{3})[. /-]*(\d{2,4})',s)
    if m:
        d,mes,a=m.groups(); a=int(a); a=a+2000 if a<100 else a
        return pd.Timestamp(a,MESES[mes],int(d or 1))
    return pd.to_datetime(s,format='%Y-%m-%d',errors='raise')

def leer(codigo,contenido):
    """Interpreta JSON conservando el valor original y valida nombre y fechas de la serie."""
    j=json.loads(contenido.decode('utf-8-sig'))
    nombre=j['config']['series'][0]['name']
    clave,frec,esperado,unidad=SERIES[codigo]
    if esperado not in nombre.lower(): raise ValueError(f'{codigo}: nombre inesperado {nombre}')
    if codigo=='PD04692MD' and 'S/' not in nombre: raise ValueError(nombre)
    if codigo=='PD04693MD' and 'US$' not in nombre: raise ValueError(nombre)
    filas=[{'codigo':codigo,'variable':clave,'fecha':fecha(p['name']), 'periodo_original':p['name'],
            'valor_original':p['values'][0], 'nombre_serie':nombre,'unidad':unidad,'frecuencia':frec}
           for p in j['periods']]
    d=pd.DataFrame(filas).sort_values('fecha')
    if d.empty or d.fecha.duplicated().any(): raise ValueError(f'{codigo}: sin datos o fechas duplicadas')
    return d

def main(local=False,demo=False):
    bloques=[]
    for codigo in SERIES:
        archivo=DIR/f'{codigo}.json'
        if demo:
            nuevo=leer(codigo,consultar(url(codigo,'2025-12-01','2025-12-31')))
            viejo=leer(codigo,archivo.read_bytes())
            cotejo=nuevo.merge(viejo,on=['codigo','fecha'],suffixes=('_vivo','_crudo'),validate='one_to_one')
            if cotejo.empty: raise ValueError('Sin fechas comunes para cotejo')
            igual=cotejo.valor_original_vivo.astype(str)==cotejo.valor_original_crudo.astype(str)
            print(cotejo[['fecha','valor_original_vivo','valor_original_crudo']].head(10).to_string(index=False))
            anotar(f'DEMO {codigo}: {igual.sum()}/{len(igual)} coincidencias exactas; revisiones se documentan')
            continue
        contenido=archivo.read_bytes() if local else consultar(url(codigo))
        d=leer(codigo,contenido)
        if not d.fecha.between(FECHA_INICIO,FECHA_CORTE).all(): raise ValueError(f'{codigo}: periodo fuera de corte')
        if d.fecha.dt.to_period('M').nunique()<85: raise ValueError(f'{codigo}: cobertura temporal insuficiente')
        if not local:
            archivo.write_bytes(contenido)
            anotar(f'GUARDADO {archivo.relative_to(RAIZ)} | {len(d)} filas | SHA256 {hashlib.sha256(contenido).hexdigest()}')
        bloques.append(d)
    if not demo:
        pd.concat(bloques,ignore_index=True).to_csv(RAIZ/'datos_crudos/datos_crudos_2024200501G_bcrp.csv',index=False,date_format='%Y-%m-%d')
        anotar(f'CSV BCRP: {sum(map(len,bloques))} filas originales')

if __name__=='__main__':
    p=argparse.ArgumentParser(); g=p.add_mutually_exclusive_group(); g.add_argument('--local',action='store_true');g.add_argument('--demo',action='store_true'); a=p.parse_args(); main(a.local,a.demo)
