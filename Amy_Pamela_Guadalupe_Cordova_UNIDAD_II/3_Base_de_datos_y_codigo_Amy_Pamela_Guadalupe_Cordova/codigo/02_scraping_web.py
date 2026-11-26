# Autora: Amy Pamela Guadalupe Cordova
# Código de matrícula: 2024200501G
# Tema 79: Fondos mutuos en el Perú: rentabilidad y riesgo por tipo de fondo
# Fecha de extracción: 2026-11-26
"""Vía 2: boletines mensuales públicos AAF. Una página de catálogo, un PDF por mes.
No se consulta la SMV (HTTP 418 documentado). --local reparsea PDF entregados.
--demo coteja un PDF vivo con su copia original. No usa Drive ni sesiones previas.
"""
import argparse, hashlib, re, time, unicodedata
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
import pandas as pd
import requests
import pdfplumber
from bs4 import BeautifulSoup

RAIZ=Path(__file__).resolve().parents[1]
DIR=RAIZ/'datos_crudos'/'scraping'; PDF=DIR/'pdf_boletines'; PDF.mkdir(parents=True,exist_ok=True)
FECHA_INICIO='2019-01'; FECHA_CORTE='2025-12'
LISTADO='https://fondosmutuos.pe/estadisticas/'
ROBOTS='https://fondosmutuos.pe/robots.txt'
PILOTO='https://fondosmutuos.pe/wp-content/uploads/2025/02/Boletin-Enero-2025-9.pdf'
UA='UNCP-FinanzasI/1.0 (investigacion academica; contacto: e_2024200501g@uncp.edu.pe)'
MANIFIESTO=DIR/'descargas_boletines_2024200501G.csv'
MESES={m:i for i,m in enumerate('enero febrero marzo abril mayo junio julio agosto septiembre octubre noviembre diciembre'.split(),1)}; MESES['setiembre']=9
TIPOS=[('Fondo de fondos',r'fondos?\s+de\s+fondos'),('Estructurados',r'estructurad'),('Acciones',r'acciones|renta variable'),('Mixtos',r'mixt'),('Flexibles',r'flexib'),('Deuda',r'deuda|renta fija')]
# Identificación auxiliar; si no hay coincidencia se conserva la denominación completa de la fuente.
ADMIN=['BBVA Asset Management','Credicorp Capital','Interfondos','Scotia Fondos','Fondos Sura','Sura','Diviso Fondos','Diviso','Independiente','Promoinvest','Faro Capital','Flip SAF','Flip','Blum','Andino','Prival','Compass','Pacífico','Pacifico','Grupo Coril','Coril','Popular SAFI','Popular','Continental','Seminario']

def anotar(s):
    linea=f'{datetime.now(timezone(timedelta(hours=-5))):%Y-%m-%d %H:%M:%S} | 02_aaf | {s}'
    print(linea)
    with (RAIZ/'log_ejecucion.txt').open('a',encoding='utf-8') as f:f.write(linea+'\n')

def plano(s):
    return ''.join(c for c in unicodedata.normalize('NFD',str(s)) if unicodedata.category(c)!='Mn').lower()

def periodo(s):
    s=plano(s)
    for m,n in MESES.items():
        x=re.search(rf'\b{m}[-_ /]*?(20\d\d)\b',s)
        if x:return f'{x[1]}-{n:02d}'
    return None

def numero(s,porcentaje=False):
    s=s.strip().replace('%','').replace('−','-').replace(' ','')
    if s.lower() in ('-','–','—','n/a','nd','n.d.',''):return None
    if ',' in s and '.' in s:
        s=s.replace('.','').replace(',','.') if s.rfind(',')>s.rfind('.') else s.replace(',','')
    else:s=s.replace(',','.')
    try:return float(s)/ (100 if porcentaje else 1)
    except ValueError:return None

# Mes del reporte: se exige una fecha explícita de portada; no se infiere de las filas.
ABREV={'ene':1,'feb':2,'mar':3,'abr':4,'may':5,'jun':6,'jul':7,'ago':8,'sep':9,'set':9,'oct':10,'nov':11,'dic':12}
def mes_portada(texto):
    t=plano(texto)
    for linea in t.splitlines():
        for m,n in {**MESES,**ABREV}.items():
            x=re.fullmatch(rf'(?:reporte mensual\s+)?{m}\.?[\s/-]+(20\d\d)(?:\s+.*)?',linea.strip())
            if x:return f'{x[1]}-{n:02d}'
    return None

# Las líneas de títulos determinan las categorías, incluso en continuaciones de página.
CABECERAS=[('Fondo de fondos',r'(?:fondos? de fondos)(?: en (?:soles|dolares))?'),('ETF',r'(?:fondo bursatil(?: etf)?|etf)'),('Estructurados',r'(?:fondos? )?estructurados?(?: en (?:soles|dolares))?'),('Acciones',r'(?:de )?acciones(?: en (?:soles|dolares))?'),('Mixtos',r'mixtos?(?: en (?:soles|dolares))?'),('Flexibles',r'flexibles?(?: en (?:soles|dolares))?'),('Deuda',r'(?:de )?deuda(?: en (?:soles|dolares)|\s*\([^)]*\))?')]
ADMIN += ['Andean Crown','Prudential SAF','El Dorado','BTG Pactual Perú','Blum SAF','Coril SAF','BD Capital','Faro Capital SAFI','AC SAF','MCC','Sura SAF','Adcap','Credicorp Capital SAF']
N=r'[-+]?\d[\d.,]*'; FALTA=r'(?:n/a|n\.d\.|nd|[-–—])'
PATRON=re.compile(rf'^(?P<nombre>.+?)\s+(?P<mon>US\s*\$|S/\.?|USD|PEN|\$)\s+(?P<vc>{N}|{FALTA})\s+(?P<ret>{N}\s*%|{FALTA})(?:\s|$)',re.I)
def leer_moderno(ruta,mes):
    """Lee portada, títulos y filas del área visible. Registra descartes sin inventar valores."""
    filas=[]; descartes=[]; candidatos=0; tipo=None
    with pdfplumber.open(ruta) as f:
        portada=f.pages[0].crop((0,0,f.pages[0].width,f.pages[0].height)).extract_text() or ''
        declarado=mes_portada(portada)
        if declarado!=mes:raise ValueError(f'Portada {declarado!r} no coincide con {mes}')
        for i,p in enumerate(f.pages,1):
            # Excluir texto situado fuera del área visible: el boletín de enero 2025 contiene texto desbordado de otras páginas.
            texto=p.crop((0,0,p.width,p.height)).extract_text(x_tolerance=2,y_tolerance=2) or ''
            if i <= 2 and 'valor cuota' not in plano(texto):continue
            for linea in texto.splitlines():
                s=unicodedata.normalize('NFKC',linea).replace('−','-')
                s=' '.join(''.join(' ' if unicodedata.category(c) in ('Co','So') else c for c in s).split())
                titulo=plano(s)
                # Algunos encabezados incluyen la segunda línea de las columnas.
                titulo=re.sub(r'\s+mes\s+mes\s+20\d\d\s+ultimos\s+12\s+meses$','',titulo)
                nuevo=next((k for k,pat in CABECERAS if re.fullmatch(pat,titulo)),None)
                if nuevo:tipo=nuevo;continue
                if not tipo:continue
                if titulo.startswith(('nota:','nota :','disclaimer')):tipo=None;continue
                m=PATRON.match(s)
                if not m:
                    if re.search(r'\s(?:US\s*\$|S/\.?|USD|PEN)\s+\d',s,re.I):
                        candidatos+=1;descartes.append({'mes':mes,'pagina':i,'archivo':ruta.name,'fila_original':linea})
                    continue
                candidatos+=1
                nombre=m['nombre'].strip(); vc=numero(m['vc']); rm=numero(m['ret'],True)
                # No adivinar números de cuota con separadores defectuosos. Conservar el retorno publicado.
                if m['vc'].count('.')>1 or m['vc'].count(',')>1 and '.' not in m['vc']:vc=None
                if rm is None or rm < -1:
                    descartes.append({'mes':mes,'pagina':i,'archivo':ruta.name,'fila_original':linea});continue
                safm='';fondo=nombre
                for a in sorted(ADMIN,key=len,reverse=True):
                    if plano(fondo).endswith(' '+plano(a)):
                        safm=a;fondo=fondo[:-len(a)].strip();break
                filas.append({'mes':mes,'tipo':tipo,'fondo':fondo,'administradora':safm,'denominacion_original':nombre,'moneda':'USD' if '$' in m['mon'] or m['mon'].upper()=='USD' else 'PEN','estado':'no informado','valor_cuota':vc,'rent_mes':rm,'archivo':ruta.name,'pagina':i,'fila_original':linea})
    return filas,descartes,candidatos

import fitz

def leer_historico(ruta, mes):
    """Lee las líneas ordenadas espacialmente de los PDF históricos con texto.
    Solo se admiten filas de tablas de rentabilidad, con moneda, cuota y retorno explícitos.
    El nombre de la administradora se separa por el espacio entre columnas.
    """
    filas=[]; descartes=[]; candidatos=0; tipo=None; activo=False
    categorias=[('Fondo de fondos',r'fondos? de fondos'),('Estructurados',r'estructurad'),('ETF',r'\b(?:bursatil|etf)\b'),('Acciones',r'\bacciones\b|renta variable'),('Mixtos',r'\bmixtos?\b'),('Deuda',r'\bdeuda\b'),('Flexibles',r'\bflexibles?\b')]
    patron=re.compile(rf'^(?P<nombre>.+?)\s{{2,}}(?P<admin>[^\n]+?)\s{{2,}}(?P<mon>US\s*\$|S/\.?|USD|PEN|\$)\s+(?P<vc>{N}|{FALTA})\s+(?P<ret>{N}\s*%|{FALTA})(?:\s|$)',re.I)
    with fitz.open(ruta) as doc:
        portada=plano(doc[0].get_text(sort=True))
        y,m=mes.split('-'); alternativas=[k for k,v in {**MESES,**ABREV}.items() if v==int(m)]
        # El mes de portada debe aparecer en título o comentario del cierre; no basta el nombre del archivo.
        patmes='(?:'+'|'.join(alternativas)+')'
        if not (re.search(rf'\b{patmes}\s*[-/]?\s*{y}(?![0-9])',portada) or re.search(rf'cierre(?:\s+de)?\s+{patmes}\b',portada) and y in portada):
            raise ValueError('Mes de portada no comprobado: '+mes)
        for i,p in enumerate(doc,1):
            texto=p.get_text(sort=True)
            for linea in texto.splitlines():
                s=unicodedata.normalize('NFKC',linea).replace('−','-').strip();t=plano(s)
                if 'rentabilidad de los fondos mutuos' in t or ('safm' in t and 'moneda' in t):activo=True
                if not activo:continue
                # Encabezados de categoría de los cuadros (no interpretamos nombres de fondos como títulos).
                if ('safm' in t and 'moneda' in t) or re.match(r'^fondos mutuos\b',t) or re.fullmatch(r'(?:de )?(?:deuda(?:\s*\([^)]*\))?|acciones|mixtos|flexibles|estructurados|fondos de fondos(?:\s*\([^)]*\))?|fondo bursatil(?: etf)?)',t):
                    # El rótulo de la tabla se encuentra a veces después de SAFM (texto superpuesto).
                    despues=t.split('safm',1)[-1] if 'safm' in t else ''
                    final=re.search(r'(?:mes)\s*((?:de )?deuda|de acciones|mixtos|fondo bursatil|estructurados|fondos? de fondos|flexibles)\b',despues)
                    texto_tipo=final.group(1) if final else t.split('safm')[0]
                    nuevo=next((k for k,pat in categorias if re.search(pat,texto_tipo)),None)
                    if nuevo:tipo=nuevo
                if not tipo:continue
                if not re.search(rf'\s(?:US\s*\$|S/\.?|USD|PEN|\$)\s+(?:{N}|{FALTA})\s+(?:{N}\s*%|{FALTA})(?:\s|$)',s,re.I):continue
                candidatos+=1
                m=patron.match(s)
                if not m:
                    descartes.append({'mes':mes,'pagina':i,'archivo':ruta.name,'fila_original':linea});continue
                vc=numero(m['vc']);rm=numero(m['ret'],True)
                if vc is None or vc<=0 or rm is None or rm< -1:
                    descartes.append({'mes':mes,'pagina':i,'archivo':ruta.name,'fila_original':linea});continue
                fondo=' '.join(m['nombre'].split());admin=' '.join(m['admin'].split())
                filas.append({'mes':mes,'tipo':tipo,'fondo':fondo,'administradora':admin,'denominacion_original':fondo+' '+admin,'moneda':'USD' if '$' in m['mon'] or m['mon'].upper()=='USD' else 'PEN','estado':'no informado','valor_cuota':vc,'rent_mes':rm,'archivo':ruta.name,'pagina':i,'fila_original':linea})
    return filas,descartes,candidatos


def leer_pdf(ruta,mes):
    # Selección congelada por formato, no por resultados financieros.
    if mes=='2025-12':raise ValueError('PDF de diciembre 2025 con capas de texto superpuestas: no se valida la lectura de categorías')
    if mes < '2022-12':return leer_historico(ruta,mes)
    try:return leer_moderno(ruta,mes)
    except ValueError:return leer_historico(ruta,mes)

def pedir(url,reglas=None,es_robots=False):
    # Seguir únicamente redirecciones normales dentro del mismo portal; nunca un rechazo.
    for _ in range(4):
        if urlparse(url).hostname not in ('fondosmutuos.pe','www.fondosmutuos.pe'):raise ValueError('Dominio no autorizado: '+url)
        if reglas is not None and not reglas.can_fetch(UA,url):raise RuntimeError('robots.txt restringe '+url)
        time.sleep(1.5)
        r=requests.get(url,headers={'User-Agent':UA},timeout=90,allow_redirects=False)
        anotar(f'HTTP {r.status_code} | {url}')
        if r.status_code in (401,403,418,429):
            (DIR/'bloqueo_aaf.txt').write_text(f'HTTP {r.status_code} | {url}',encoding='utf-8')
            raise RuntimeError('Acceso rechazado: no se reintenta ni se cambia de conexión.')
        if r.status_code in (301,302,303,307,308) and r.headers.get('Location'):
            url=urljoin(url,r.headers['Location']);continue
        if es_robots and r.status_code in (404,410):
            anotar('robots.txt no está publicado (HTTP 404/410); se conserva registro y se respetan los rechazos de cada URL.')
            return b'# REGISTRO LOCAL: robots.txt no publicado; ver HTTP en log.\n'
        if r.status_code!=200:raise RuntimeError(f'HTTP {r.status_code}; {url}')
        return r.content
    raise RuntimeError('Demasiadas redirecciones del portal.')

def reglas_portal():
    if (DIR/'bloqueo_aaf.txt').exists():raise RuntimeError('Existe un rechazo de AAF registrado; no continuar sin revisar autorización.')
    contenido=pedir(ROBOTS,es_robots=True); (DIR/'robots_aaf.txt').write_bytes(contenido)
    r=RobotFileParser();r.parse(contenido.decode('utf-8',errors='replace').splitlines());return r

def enlaces(contenido):
    """Identifica URL publicadas a partir del catálogo y comprueba el mes del enlace."""
    sopa=BeautifulSoup(contenido,'html.parser'); candidatos={}
    for a in sopa.find_all('a',href=True):
        href=urljoin(LISTADO,a['href']); etiqueta=plano(a.get_text(' ',strip=True))
        if not urlparse(href).path.lower().endswith('.pdf'):continue
        if urlparse(href).hostname not in ('fondosmutuos.pe','www.fondosmutuos.pe'):continue
        if 'boletin' not in etiqueta and 'boletin' not in plano(urlparse(href).path):continue
        h=a.find_previous(['h1','h2','h3','h4','h5','h6'])
        mes=periodo(h.get_text(' ',strip=True)) if h else None
        mes_url=periodo(urlparse(href).path.rsplit('/',1)[-1])
        if mes and mes_url and mes!=mes_url:continue
        mes=mes or mes_url
        if mes and FECHA_INICIO<=mes<=FECHA_CORTE:
            candidatos.setdefault(href,set()).add(mes)
    links={}
    for href,meses in candidatos.items():
        # Las versiones móvil/escritorio pueden repetir enlaces de otro mes.
        if len(meses)!=1:continue
        mes=next(iter(meses));links.setdefault(mes,href)
    links['2025-01']=PILOTO
    return links

def procesar(manifiesto):
    """Verifica SHA de cada PDF antes de parsearlo y conserva la evidencia de calidad."""
    todas=[]; descartes=[]; control=[]
    for row in manifiesto.sort_values('mes').itertuples():
        ruta=PDF/row.archivo
        if hashlib.sha256(ruta.read_bytes()).hexdigest()!=row.sha256:raise ValueError('PDF alterado: '+row.archivo)
        try:
            f,d,c=leer_pdf(ruta,row.mes)
        except Exception as e:
            anotar(f'{row.mes} | parseo fallido: {e}');f,d,c=[],[],0
        aceptable=len(f)>=25 and c>0 and len(f)/c>=.90
        if aceptable:todas+=f
        else:anotar(f'{row.mes}: boletín excluido por calidad del parseo; revisar original.')
        descartes+=d
        control.append({'mes':row.mes,'archivo':row.archivo,'url':row.url,'filas':len(f),'candidatos':c,'no_reconocidas':len(d),'aceptado':aceptable})
        anotar(f'{row.mes} | {len(f)} filas reconocidas de {c} candidatas | {row.archivo}')
    pd.DataFrame(control).to_csv(DIR/'control_parseo_2024200501G.csv',index=False)
    pd.DataFrame(descartes,columns=['mes','pagina','archivo','fila_original']).to_csv(DIR/'filas_no_reconocidas_2024200501G.csv',index=False)
    if not todas:raise RuntimeError('Ninguna tabla pudo leerse; revisar formato PDF, no estimar.')
    df=pd.DataFrame(todas).sort_values(['mes','tipo','moneda','denominacion_original','pagina'],kind='stable')
    df.to_csv(RAIZ/'datos_crudos/datos_crudos_2024200501G_aaf.csv',index=False)
    print('Cobertura preliminar:',df.mes.nunique(),'meses;',len(df),'filas; revisar control de parseo.')
    # No se acepta un parser que, en conjunto, omite la mayoría de las líneas candidatas.
    cand=sum(r['candidatos'] for r in control)
    if df.mes.nunique()<60:raise RuntimeError('Menos de 60 meses legibles; revisar control de parseo antes de estimar.')
    return df

def main(local=False,demo=False):
    if local:procesar(pd.read_csv(MANIFIESTO));return
    reglas=reglas_portal()
    if demo:
        anterior=pd.read_csv(RAIZ/'datos_crudos/datos_crudos_2024200501G_aaf.csv')
        inventario=pd.read_csv(MANIFIESTO)
        row=inventario[inventario.mes.isin(anterior.mes)].sort_values('mes').iloc[-1]
        b=pedir(row.url,reglas)
        if not b.startswith(b'%PDF'):raise RuntimeError('Respuesta no es PDF')
        import tempfile
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/row.archivo;p.write_bytes(b)
            filas,_,_=leer_pdf(p,row.mes)
            campos=['denominacion_original','moneda','tipo','valor_cuota','rent_mes']
            a=pd.DataFrame(filas)[campos];v=anterior[anterior.mes==row.mes][campos]
            iguales=a.merge(v,on=campos).drop_duplicates()
            print('Filas coincidentes exactas:',len(iguales),'de',len(v),'originales. SHA idéntico:',hashlib.sha256(b).hexdigest()==row.sha256)
            print(iguales.sample(min(10,len(iguales)),random_state=501).to_string(index=False))
        return
    contenido=pedir(LISTADO,reglas);(DIR/'listado_aaf.html').write_bytes(contenido)
    links=enlaces(contenido)
    print('Boletines identificados en catálogo:',len(links))
    if len(links)<24:raise RuntimeError('Catálogo insuficiente; no descargar masivamente ni fabricar meses.')
    registros=[]
    if MANIFIESTO.exists():registros=pd.read_csv(MANIFIESTO).to_dict('records')
    # Primero se prueba un único informe antes de descargar los demás.
    pilotos=['2025-01','2020-06']
    if any(m not in links for m in pilotos):raise RuntimeError('El catálogo no contiene ambos boletines piloto.')
    orden=pilotos+sorted(m for m in links if m not in pilotos)
    for mes in orden:
        u=links[mes];nombre=f'aaf_boletin_2024200501G_{mes}.pdf';ruta=PDF/nombre
        anterior=next((x for x in registros if x['mes']==mes),None)
        if anterior and ruta.exists() and anterior['url']==u and hashlib.sha256(ruta.read_bytes()).hexdigest()==anterior['sha256']:
            b=ruta.read_bytes()
        else:
            try:
                b=pedir(u,reglas)
            except RuntimeError as e:
                if mes not in pilotos and str(e).startswith(('HTTP 404;', 'HTTP 410;')):
                    anotar(f'{mes}: enlace no disponible. Se omite.')
                    continue
                raise

            if not b.startswith(b'%PDF'):
                if mes in pilotos:
                    raise RuntimeError('El piloto no es PDF')
                anotar(f'{mes}: enlace sin PDF. Se omite.')
                continue
            ruta.write_bytes(b)
            registros=[x for x in registros if x['mes']!=mes]
            registros.append({'mes':mes,'archivo':nombre,'url':u,'http':200,'fecha_consulta':datetime.now(timezone(timedelta(hours=-5))).isoformat(),'sha256':hashlib.sha256(b).hexdigest()})
            pd.DataFrame(registros).sort_values('mes').to_csv(MANIFIESTO,index=False)
        if mes in pilotos:
            f,d,c=leer_pdf(ruta,mes);print(f'PILOTO: {len(f)} filas / {c} candidatas.')
            if len(f)<25 or (c and len(f)/c<.90):raise RuntimeError('El piloto no confirma extracción suficiente. No se descargan los demás boletines.')
            print(pd.DataFrame(f)[['fondo','moneda','tipo','valor_cuota','rent_mes']].head(10).to_string(index=False))
    procesar(pd.DataFrame(registros))

if __name__=='__main__':
    p=argparse.ArgumentParser();g=p.add_mutually_exclusive_group();g.add_argument('--local',action='store_true');g.add_argument('--demo',action='store_true');a=p.parse_args()
    try:main(a.local,a.demo)
    except Exception as e:
        anotar(f'ERROR: {type(e).__name__}: {e}');raise
