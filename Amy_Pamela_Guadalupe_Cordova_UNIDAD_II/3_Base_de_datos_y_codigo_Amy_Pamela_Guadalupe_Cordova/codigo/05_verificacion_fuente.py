# Autora: Amy Pamela Guadalupe Cordova
# Código de matrícula: 2024200501G
# Tema 79: Fondos mutuos en el Perú: rentabilidad y riesgo por tipo de fondo
# Fecha de extracción: 2026-11-25
"""Auditoría independiente de integridad, reproducción y autenticidad.

La ejecución sin argumentos reproduce la entrega y realiza un cotejo acotado
contra ambas fuentes vivas. --en-vivo comprueba solo la muestra en la exposición;
--sin-internet verifica íntegramente la reproducción desde JSON y PDF entregados.
La comparación en vivo NO acredita todos los meses; una respuesta bloqueada no
es una discrepancia de datos. Nunca se regeneran los hashes de la entrega ni se
sobrescriben los crudos. Código de salida 0: pruebas solicitadas conformes;
2: cotejo vivo incompleto o discrepante; 1: error de integridad/reproducción.
"""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import argparse
import hashlib
import importlib.util
import shutil
import subprocess
import sys
import tempfile
import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
SALIDAS = RAIZ / 'salidas'
PROCESADO = 'datos_procesados/datos_procesados_2024200501G.csv'
CRUDO_AAF = 'datos_crudos/datos_crudos_2024200501G_aaf.csv'
CRUDO_BCRP = 'datos_crudos/datos_crudos_2024200501G_bcrp.csv'
INVENTARIO = 'datos_crudos/scraping/descargas_boletines_2024200501G.csv'
SEMILLA = 501  # 0501: últimos cuatro dígitos numéricos de la matrícula.
UMBRAL = .95
RTOL, ATOL = 1e-9, 1e-11
LLAVES = ['id_fondo_serie','mes','fecha','codigo','denominacion_original','moneda','tipo','variable','archivo']


def sha(p):
    """Calcula la huella de los bytes originales, sin abrir ni modificar datos."""
    return hashlib.sha256(p.read_bytes()).hexdigest()


def leer_csv(p):
    return pd.read_csv(p, dtype={'mes':str})


def fecha_peru():
    return datetime.now(timezone(timedelta(hours=-5))).isoformat(timespec='seconds')


def igual(a,b):
    """Compara números con tolerancia de serialización, no de revisión oficial."""
    if pd.isna(a) or pd.isna(b):
        return bool(pd.isna(a) and pd.isna(b))
    try:
        return bool(np.isclose(float(a),float(b),rtol=RTOL,atol=ATOL))
    except (ValueError,TypeError):
        return str(a)==str(b)


def integridad():
    """Prueba 1: el manifiesto se coteja antes de reejecutar, nunca después."""
    rutas=[]
    for num,linea in enumerate((RAIZ/'hash_sha256.txt').read_text(encoding='utf-8').splitlines(),1):
        esperado,rel=linea.split('  ',1)
        r=Path(rel)
        if r.is_absolute() or '..' in r.parts or rel in rutas:
            raise RuntimeError(f'Manifiesto inválido en línea {num}: {rel}')
        p=RAIZ/r
        if not p.is_file() or sha(p)!=esperado:
            raise RuntimeError('Hash no coincide con archivo entregado: '+rel)
        rutas.append(rel)
    if not {PROCESADO,CRUDO_AAF,CRUDO_BCRP,INVENTARIO}.issubset(rutas):
        raise RuntimeError('Manifiesto incompleto.')
    print(f'PRUEBA 1 | Integridad original: {len(rutas)} archivos conformes.')
    return rutas


def comparar_csv(a,b):
    """Prueba las dimensiones, columnas, tipos inferidos y claves antes de valores.
    Los números pueden diferir en el último decimal al ejecutar otro entorno.
    Los identificadores y fechas nunca admiten tolerancia numérica.
    """
    x,y=leer_csv(a),leer_csv(b)
    forma=x.shape==y.shape and list(x.columns)==list(y.columns)
    tipos=forma and x.dtypes.astype(str).equals(y.dtypes.astype(str))
    if not forma or not tipos:
        return dict(filas_original=len(x),filas_reproducidas=len(y),columnas_tipos=bool(tipos),claves=False,celdas=0,coinciden=0,equivalencia=0.)
    # Comparar texto exacto en identificadores y campos no numéricos.
    claves=all(x[k].equals(y[k]) for k in LLAVES if k in x)
    ok=x.eq(y)|(x.isna()&y.isna())
    for col in x:
        if col not in LLAVES and pd.api.types.is_numeric_dtype(x[col]):
            ok[col]=np.isclose(x[col].to_numpy(dtype=float),y[col].to_numpy(dtype=float),rtol=RTOL,atol=ATOL,equal_nan=True)
    total=ok.size; n=int(ok.to_numpy().sum())
    return dict(filas_original=len(x),filas_reproducidas=len(y),columnas_tipos=bool(tipos),claves=bool(claves),celdas=total,coinciden=n,equivalencia=n/total if total else 1.)


def copia_temporal(t):
    """Aísla toda actividad de red, logs y reejecución de los datos entregados."""
    for carpeta in ['codigo','datos_crudos']:
        shutil.copytree(RAIZ/carpeta,t/carpeta,ignore=shutil.ignore_patterns('__pycache__','*.ipynb'))
    for carpeta in ['datos_procesados','salidas']:
        (t/carpeta).mkdir()


def muestra_panel():
    """Muestra elegida antes de consultar, solo en registros originales observados.
    No se compara un retorno winsorizado/interpolado con un dato publicado.
    Se usa el identificador homologado para encontrar t y t-1.
    """
    d=leer_csv(RAIZ/PROCESADO)
    observado=leer_csv(RAIZ/'datos_procesados/base_integrada_observada.csv')
    llaves=set(zip(observado.id_fondo_serie,observado.mes))
    manifiesto=leer_csv(RAIZ/INVENTARIO)
    meses=set(manifiesto.mes)
    a=d[d.muestra_modelo.eq(1)&d.imputado.eq(0)]
    for mes,g in reversed(list(a.groupby('mes',sort=True))):
        previo=str(pd.Period(mes,freq='M')-1)
        if mes not in meses or previo not in meses:continue
        elegible=g[g.id_fondo_serie.map(lambda k:(k,mes) in llaves and (k,previo) in llaves)]
        if len(elegible)>=10:
            return elegible.sort_values('id_fondo_serie').sample(10,random_state=SEMILLA).reset_index(drop=True)
    raise RuntimeError('No existen diez casos con datos originales verificables de t y t-1.')


def informe_local(rutas):
    """Pruebas 2 a 4: reparsear originales, recalcular procesado y regenerar salidas.
    No necesita permisos de GitHub, Drive ni acceso a Internet.
    """
    registro=[f'# Verificación computacional local\n\nFecha de ejecución: {fecha_peru()}',
              f'Prueba 1. Integridad: {len(rutas)} hashes originales conformes.',
              'Prueba 2. Reparseo de JSON de BCRP y PDF AAF entregados.',
              'Prueba 3. Reestimación de limpieza, variables calculadas, tablas y modelos desde los crudos.']
    comparaciones=[]
    with tempfile.TemporaryDirectory(prefix='repro_finanzas_') as tmp:
        t=Path(tmp);copia_temporal(t)
        # Si estos productos ya existían, borrarlos solo en la copia para asegurar
        # que realmente se generen con el código y no se reutilicen archivos viejos.
        for rel in [CRUDO_BCRP,CRUDO_AAF,'datos_crudos/scraping/control_parseo_2024200501G.csv','datos_crudos/scraping/filas_no_reconocidas_2024200501G.csv']:
            (t/rel).unlink(missing_ok=True)
        orden=[('01_extraccion_api.py','--local'),('02_scraping_web.py','--local'),('03_limpieza_datos.py',),('04_analisis.py',)]
        for args in orden:
            subprocess.run([sys.executable,str(t/'codigo'/args[0]),*args[1:]],cwd=t,check=True)
        for rel in rutas:
            if not rel.endswith('.csv'):
                continue
            if not (t/rel).is_file():
                raise RuntimeError('Archivo CSV no reproducido: '+rel)
            resultado=comparar_csv(RAIZ/rel,t/rel)
            comparaciones.append(dict(archivo=rel,**resultado))
        df=pd.DataFrame(comparaciones)
        df.to_csv(SALIDAS/'verificacion_equivalencia.csv',index=False,float_format='%.12g')
        if df.empty or not df.columnas_tipos.all() or not df.claves.all() or (df.equivalencia<UMBRAL).any():
            raise RuntimeError('Reproducción no conforme; revisar verificacion_equivalencia.csv')
        originales={p.name for p in SALIDAS.glob('figura*.png')}
        nuevos={p.name for p in (t/'salidas').glob('figura*.png')}
        if not originales or originales!=nuevos or any((t/'salidas'/n).stat().st_size==0 for n in nuevos):
            raise RuntimeError('No se regeneraron todas las figuras.')
        registro.append(f'Prueba 4. {len(df)} CSV equivalentes al umbral del 95%; mínimo observado {df.equivalencia.min():.2%}. {len(nuevos)} figuras regeneradas; no se exige identidad de bytes PNG entre plataformas.')
        registro.extend(f'- {r.archivo}: {r.coinciden}/{r.celdas} celdas ({r.equivalencia:.2%}); tipos y claves conformes.' for r in df.itertuples())
    muestra_panel().to_csv(SALIDAS/'muestra_cotejo_2024200501G.csv',index=False)
    registro.append('APROBADO: reproducción computacional local. No equivale a acreditar una consulta nueva de las fuentes vivas.')
    (SALIDAS/'verificacion_local.md').write_text('\n\n'.join(registro)+'\n',encoding='utf-8')
    print('\n'.join(registro))


def importar(ruta,nombre):
    """Carga una función de extracción desde la copia temporal, sin ejecutarla."""
    spec=importlib.util.spec_from_file_location(nombre,ruta)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    return mod


def cotejo_vivo():
    """Pruebas 5 y 6: consultas auténticas, acotadas al periodo de la muestra.
    Se consultan dos boletines (t y t-1) y tres series BCRP. Se cotejan las diez
    filas seleccionadas y los valores utilizados para calcular el exceso y X2.
    La volatilidad histórica de 12 meses se coteja íntegramente en modo local,
    no se afirma haber reextraído sus 12 boletines en esta demostración.
    """
    muestra=muestra_panel();mes=muestra.mes.iloc[0];previo=str(pd.Period(mes,freq='M')-1)
    manifiesto=leer_csv(RAIZ/INVENTARIO).set_index('mes')
    original_b=leer_csv(RAIZ/CRUDO_BCRP);original_b['fecha']=pd.to_datetime(original_b.fecha)
    errores=[];comps=[];fuentes=[];bcrp={};aaf={}
    def comparar(fuente,clave,campo,original,vivo,url,pagina='',encontrado=True):
        comps.append(dict(fuente=fuente,clave=clave,variable=campo,entregado=original,consultado=vivo,url=url,pagina=pagina,coincide=bool(encontrado and igual(original,vivo))))
    with tempfile.TemporaryDirectory(prefix='cotejo_fuentes_') as tmp:
        t=Path(tmp);copia_temporal(t)
        api=importar(t/'codigo/01_extraccion_api.py','aporte_bcrp')
        pdf=importar(t/'codigo/02_scraping_web.py','aporte_aaf')
        limpieza=importar(t/'codigo/03_limpieza_datos.py','identificadores')
        inicio=previo+'-01';fin=str(pd.Period(mes,freq='M').end_time.date())
        print(f'PRUEBA 5 | BCRP: ventana {inicio} a {fin}.')
        for codigo in api.SERIES:
            direccion=api.url(codigo,inicio,fin)
            try:
                contenido=api.consultar(direccion)
                nuevo=api.leer(codigo,contenido)
                antiguo=original_b[original_b.codigo.eq(codigo)&original_b.fecha.between(inicio,fin)]
                a=antiguo.set_index('fecha').valor_original;b=nuevo.set_index('fecha').valor_original
                if a.empty or b.empty:raise RuntimeError('Consulta sin registros para cotejar')
                bcrp[codigo]=nuevo
                for periodo in sorted(set(a.index)|set(b.index)):
                    comparar('BCRP',f'{codigo} | {periodo:%Y-%m-%d}','valor_original',a.get(periodo),b.get(periodo),direccion,encontrado=periodo in a.index and periodo in b.index)
                fuentes.append(f'BCRP {codigo}: {len(a)} registros entregados y {len(b)} consultados.')
            except Exception as e:
                errores.append(f'BCRP {codigo}: {type(e).__name__}: {e}')
                # Ante un rechazo explícito, no seguir consultando el portal.
                if any(c in str(e) for c in ['401','403','418','429']):break
        print(f'PRUEBA 6 | AAF: boletines {previo} y {mes}; muestra aleatoria de diez filas.')
        try:
            reglas=pdf.reglas_portal()
            for p in [previo,mes]:
                row=manifiesto.loc[p]
                contenido=pdf.pedir(row.url,reglas)
                if not contenido.startswith(b'%PDF'):raise RuntimeError('La respuesta no es PDF: '+row.url)
                ruta=t/'datos_crudos/scraping/pdf_boletines'/row.archivo
                # Únicamente en copia temporal; los bytes de la entrega permanecen intactos.
                ruta.write_bytes(contenido)
                filas,_,candidatos=pdf.leer_pdf(ruta,p)
                if len(filas)<25 or not candidatos or len(filas)/candidatos<.90:
                    raise RuntimeError('Formato AAF distinto o parseo insuficiente: '+p)
                aaf[p]=pd.DataFrame(filas)
                aaf[p]['id_fondo_serie']=[limpieza.identidad(f,z,c) for f,z,c in zip(aaf[p].fondo,aaf[p].administradora,aaf[p].moneda)]
                fuentes.append(f'AAF {p}: {len(filas)} filas reconocidas. SHA original igual: {sha(ruta)==row.sha256}.')
        except Exception as e:
            errores.append(f'AAF: {type(e).__name__}: {e}')
        # Se cotejan las cifras originales (no las tratadas); se conserva URL/página.
        for r in muestra.itertuples():
            if mes in aaf:
                h=aaf[mes];z=h[h.id_fondo_serie.eq(r.id_fondo_serie)&h.moneda.eq(r.moneda)&h.tipo.eq(r.tipo)].drop_duplicates(['valor_cuota','rent_mes'])
                unico=len(z)==1
                for campo,entregado in [('rent_original',r.rent_original),('valor_cuota',r.valor_cuota)]:
                    campo_fuente='rent_mes' if campo=='rent_original' else campo
                    comparar('AAF',r.id_fondo_serie+' | '+mes,campo,entregado,z.iloc[0][campo_fuente] if unico else None,manifiesto.loc[mes].url,int(z.iloc[0].pagina) if unico else '',unico)
            if previo in aaf:
                h=aaf[previo];z=h[h.id_fondo_serie.eq(r.id_fondo_serie)&h.moneda.eq(r.moneda)&h.tipo.eq(r.tipo)].drop_duplicates(['rent_mes'])
                unico=len(z)==1
                comparar('AAF',r.id_fondo_serie+' | '+previo,'rent_lag1_original',r.rent_lag1_original,z.iloc[0].rent_mes if unico else None,manifiesto.loc[previo].url,int(z.iloc[0].pagina) if unico else '',unico)
        # Recalcular las variables macroeconómicas desde registros recién consultados.
        if len(bcrp)==3:
            valores={}
            for codigo,h in bcrp.items():
                h=h.copy();h['mes']=h.fecha.dt.to_period('M').astype(str);h['valor']=pd.to_numeric(h.valor_original,errors='coerce')
                valores[codigo]=h.groupby('mes').valor.mean()
            tc=valores['PN01216PM'];var=np.log(tc.get(mes,np.nan))-np.log(tc.get(previo,np.nan))
            for r in muestra.itertuples():
                tc_url=api.url('PN01216PM',inicio,fin)
                comparar('BCRP_calculo',r.id_fondo_serie+' | '+mes,'tc_fin',r.tc_fin,tc.get(mes),tc_url)
                comparar('BCRP_calculo',r.id_fondo_serie+' | '+mes,'var_tc',r.var_tc,var,tc_url)
                cod='PD04692MD' if r.moneda=='PEN' else 'PD04693MD';tasa=valores[cod].get(mes,np.nan);rf=(1+tasa/100)**(1/12)-1
                comparar('BCRP_calculo',r.id_fondo_serie+' | '+mes,'rf_mensual',r.rf_mensual,rf,api.url(cod,inicio,fin))
    # El informe se guarda aparte del conjunto de archivos sellados con hash.
    tab=pd.DataFrame(comps,columns=['fuente','clave','variable','entregado','consultado','url','pagina','coincide'])
    tab.to_csv(SALIDAS/'verificacion_cotejo_vivo.csv',index=False)
    resumen=tab.groupby('fuente').coincide.agg(['sum','count']) if not tab.empty else pd.DataFrame()
    completo=not errores and len(bcrp)==3 and len(aaf)==2 and len(tab[tab.fuente.eq('AAF')])==30 and len(tab[tab.fuente.eq('BCRP_calculo')])==30
    # Una discrepancia no se justifica como revisión oficial sin evidencia.
    conforme=bool(completo and not tab.empty and tab.coincide.all())
    estado='CONFORME: muestra viva cotejada completamente' if conforme else ('NO VERIFICABLE COMPLETAMENTE: acceso o cobertura insuficiente' if not completo else 'DISCREPANCIAS: revisar los registros y posibles revisiones oficiales')
    lineas=['# Cotejo en vivo de ambas fuentes',f'Fecha de consulta: {fecha_peru()}',f'Muestra: diez fondo/serie-mes de {mes}; semilla {SEMILLA}; mes previo {previo}.',*fuentes,'Coincidencias por fuente:',resumen.to_string(),*errores,estado,'Alcance: muestra acotada. No certifica todos los PDF ni todas las fechas. No se reextrae vol12 en vivo; se cotejan rentabilidades publicadas antes de winsorizar y filas no interpoladas. Los originales y hashes se conservan.']
    (SALIDAS/'verificacion_en_vivo.md').write_text('\n\n'.join(lineas)+'\n',encoding='utf-8')
    print('\n'.join(lineas))
    print(tab.loc[tab.fuente.eq('AAF'),['clave','variable','entregado','consultado','pagina','coincide']].to_string(index=False))
    return conforme


def main():
    p=argparse.ArgumentParser(description=__doc__)
    g=p.add_mutually_exclusive_group()
    g.add_argument('--sin-internet',action='store_true',help='Reproducción íntegra sin acceso a las fuentes')
    g.add_argument('--en-vivo',action='store_true',help='Cotejo acotado para la exposición')
    a=p.parse_args()
    rutas=integridad()
    vivo_ok=True
    if not a.sin_internet:vivo_ok=cotejo_vivo()
    if not a.en_vivo:informe_local(rutas)
    # Confirma la integridad otra vez para detectar cualquier modificación accidental.
    integridad()
    if not vivo_ok:sys.exit(2)


if __name__=='__main__':main()
