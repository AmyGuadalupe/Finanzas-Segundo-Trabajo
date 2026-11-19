# Autora: Amy Pamela Guadalupe Cordova
# Código de matrícula: 2024200501G
# Tema 79: Fondos mutuos en el Perú: rentabilidad y riesgo por tipo de fondo
# Fecha de extracción: 2026-11-19
"""Por defecto verifica la entrega y la reproduce en una copia temporal sin internet.
--en-vivo: además llama a los modos demo de 01 y 02, sin sobrescribir originales.
"""
from pathlib import Path
import argparse, hashlib, shutil, subprocess, sys, tempfile
import numpy as np
import pandas as pd

RAIZ=Path(__file__).resolve().parents[1]

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def equivalencia(a,b):
    if sha(a)==sha(b):return 1.0
    x=pd.read_csv(a,keep_default_na=False,dtype=str);y=pd.read_csv(b,keep_default_na=False,dtype=str)
    if x.shape!=y.shape or list(x.columns)!=list(y.columns):return 0.0
    if x.empty:return 1.0
    # Las claves y fechas deben coincidir exactamente; para números, tolerancia de redondeo.
    for k in ['id_fondo_serie','mes','fecha','codigo','denominacion_original','moneda','tipo','variable','archivo']:
        if k in x and not x[k].equals(y[k]):return 0.0
    eq=x.eq(y)
    for col in x:
        n=pd.to_numeric(x[col],errors='coerce');m=pd.to_numeric(y[col],errors='coerce')
        eq[col]=eq[col] | (n.notna()&m.notna()&np.isclose(n,m,rtol=1e-9,atol=1e-11))
    return float(eq.to_numpy().mean())

def main(vivo=False):
    registro=[]
    rutas=[]
    for linea in (RAIZ/'hash_sha256.txt').read_text(encoding='utf-8').splitlines():
        esperado,rel=linea.split('  ',1);p=RAIZ/rel
        if not p.is_file() or sha(p)!=esperado:raise RuntimeError('Hash no coincide con archivo entregado: '+rel)
        rutas.append(rel)
    if not rutas or 'datos_procesados/datos_procesados_2024200501G.csv' not in rutas:raise RuntimeError('Manifiesto incompleto')
    registro.append(f'Integridad original: {len(rutas)} archivos verificados antes de regenerar.')
    with tempfile.TemporaryDirectory(prefix='repro_finanzas_') as tmp:
        t=Path(tmp)
        for carpeta in ['codigo','datos_crudos']:shutil.copytree(RAIZ/carpeta,t/carpeta)
        for carpeta in ['datos_procesados','salidas']: (t/carpeta).mkdir()
        for rel in ['datos_crudos/datos_crudos_2024200501G_bcrp.csv','datos_crudos/datos_crudos_2024200501G_aaf.csv','datos_crudos/scraping/control_parseo_2024200501G.csv','datos_crudos/scraping/filas_no_reconocidas_2024200501G.csv']:
            (t/rel).unlink(missing_ok=True)
        orden=[('01_extraccion_api.py','--local'),('02_scraping_web.py','--local'),('03_limpieza_datos.py',),('04_analisis.py',)]
        for args in orden:subprocess.run([sys.executable,str(t/'codigo'/args[0]),*args[1:]],cwd=t,check=True)
        # Reparseo de originales y regeneración de tablas: no se reescribe la entrega.
        for rel in rutas:
            if not rel.endswith('.csv'):continue
            if not (t/rel).is_file():raise RuntimeError('Archivo CSV no reproducido: '+rel)
            q=equivalencia(RAIZ/rel,t/rel)
            registro.append(f'{rel}: equivalencia {q:.2%}')
            if q<.95:raise RuntimeError(f'{rel}: equivalencia inferior al 95 %')
        originales={p.name for p in (RAIZ/'salidas').glob('figura*.png')};nuevos={p.name for p in (t/'salidas').glob('figura*.png')}
        if not originales or originales!=nuevos:raise RuntimeError('No se regeneraron todas las figuras.')
        registro.append(f'{len(originales)} figuras regeneradas; se contrastaron las tablas (PNG puede variar por plataforma).')
    d=pd.read_csv(RAIZ/'datos_procesados/datos_procesados_2024200501G.csv')
    d.sample(10,random_state=501).to_csv(RAIZ/'salidas/muestra_cotejo_2024200501G.csv',index=False)
    registro.append('APROBADO: reproducción computacional local. Esto no equivale a un cotejo nuevo contra la fuente viva.')
    (RAIZ/'salidas/verificacion_local.md').write_text('\n\n'.join(registro)+'\n',encoding='utf-8');print('\n'.join(registro))
    if vivo:
        for s in ['01_extraccion_api.py','02_scraping_web.py']:
            subprocess.run([sys.executable,str(RAIZ/'codigo'/s),'--demo'],cwd=RAIZ,check=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--en-vivo',action='store_true');p.add_argument('--sin-internet',action='store_true');a=p.parse_args()
    if a.en_vivo and a.sin_internet:p.error('Elige una modalidad')
    main(a.en_vivo)
