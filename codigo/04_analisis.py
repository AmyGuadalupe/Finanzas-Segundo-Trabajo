# Autora: Amy Pamela Guadalupe Cordova
# Código de matrícula: 2024200501G
# Tema 79: Fondos mutuos en el Perú: rentabilidad y riesgo por tipo de fondo
# Fecha de extracción: 2026-11-26
"""Panel balanceado: desempeño ajustado al riesgo y un modelo de tres X.
Inferencia agrupada por fondo/serie y mes; asociación, no causalidad.
"""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.colors import SymLogNorm
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.ticker import FuncFormatter
import statsmodels.formula.api as smf
from statsmodels.stats.outliers_influence import variance_inflation_factor

RAIZ=Path(__file__).resolve().parents[1]; S=RAIZ/'salidas';S.mkdir(exist_ok=True)
FORMULA='rent_mes ~ vol12 + var_tc + rent_lag1 + C(tipo) + C(moneda)'

def guardar(d,n):d.to_csv(S/(n+'.csv'),index=False,float_format='%.10g')
def figura(fig,n):
    # Las figuras usan diseño restringido (layout='constrained'); aquí solo se guardan.
    fig.savefig(S/(n+'.png'),dpi=300,bbox_inches='tight');plt.close(fig)

def estimar(d,nombre):
    ajuste=smf.ols(FORMULA,data=d).fit()
    if np.linalg.matrix_rank(ajuste.model.exog)<ajuste.model.exog.shape[1]:raise RuntimeError('Modelo sin rango completo; revisar variables o categorías.')
    grupos=np.column_stack([pd.factorize(d.id_fondo_serie)[0],pd.factorize(d.mes)[0]])
    robusto=ajuste.get_robustcov_results(cov_type='cluster',groups=grupos,use_correction=True,df_correction=True,use_t=True)
    conf=robusto.conf_int()
    t=pd.DataFrame({'modelo':nombre,'variable':ajuste.model.exog_names,'coeficiente':robusto.params,'error_estandar':robusto.bse,'p_valor':robusto.pvalues,'ic95_inf':conf[:,0],'ic95_sup':conf[:,1],'n':int(ajuste.nobs),'r2':ajuste.rsquared,'fondos_series':d.id_fondo_serie.nunique(),'meses':d.mes.nunique(),'inferencia_valida':np.isfinite(robusto.bse)&(robusto.bse>0)})
    return ajuste,t

# ---------------------------------------------------------------------------
# Figuras del artículo. Cada una muestra información que no está en las tablas:
# las series individuales, sus trayectorias mensuales o la variación mensual que
# identifica el coeficiente cambiario. Ninguna recalcula ni altera resultados.
# ---------------------------------------------------------------------------
COLORES={'Acciones':'#0072B2','Mixtos':'#D55E00','Fondo de fondos':'#CC79A7','Deuda':'#E69F00','Flexibles':'#009E73'}
MARCAS={'Acciones':'o','Mixtos':'v','Fondo de fondos':'D','Deuda':'s','Flexibles':'^'}
ORDEN=list(COLORES)
TITULO_MONEDA={'PEN':'Fondos en soles (PEN)','USD':'Fondos en dólares (USD)'}
MESES=['ene','feb','mar','abr','may','jun','jul','ago','set','oct','nov','dic']

def numero(v,_=None):
    """Rótulo de eje con coma decimal y signo menos tipográfico."""
    return f'{v:g}'.replace('.',',').replace('-','−')

def estilo():
    # Times New Roman o su sustituto métrico; en Colab se usa DejaVu Serif si faltan ambas.
    # Las figuras miden 6,3 pulgadas de ancho, el ancho de texto del artículo, para
    # insertarse sin reducción y conservar letras de 8,5 a 9,5 puntos.
    plt.rcParams.update({'font.family':'serif','font.serif':['Liberation Serif','Times New Roman','DejaVu Serif'],
        'font.size':9,'axes.spines.top':False,'axes.spines.right':False,'axes.grid':True,'grid.alpha':.25,
        'grid.linewidth':.5,'axes.linewidth':.7})

def leyenda_tipos(fig,forma='marca',lugar='outside lower center'):
    if forma=='marca':mangos=[Line2D([],[],marker=MARCAS[t],color=COLORES[t],ls='',ms=6,label=t) for t in ORDEN]
    elif forma=='linea':mangos=[Line2D([],[],color=COLORES[t],lw=2,label=t) for t in ORDEN]
    else:mangos=[Patch(color=COLORES[t],label=t) for t in ORDEN]
    fig.legend(handles=mangos,loc=lugar,ncol=5,frameon=False,columnspacing=1.3,handletextpad=.5,handlelength=1.8)

def figura_riesgo_rentabilidad(f):
    """Figura 1. Riesgo y rentabilidad anualizados de cada serie. Se señalan las dos
    razones de Sharpe extremas, que corresponden a series de volatilidad muy baja."""
    extremos=f.loc[[f.sharpe_anualizado.idxmax(),f.sharpe_anualizado.idxmin()]]
    fig,axs=plt.subplots(1,2,figsize=(6.3,3.25),sharey=True,layout='constrained')
    for ax,mon in zip(axs,['PEN','USD']):
        # Fondo de fondos, el grupo más numeroso, se dibuja primero para no tapar a los demás.
        for t in ['Fondo de fondos','Deuda','Acciones','Mixtos','Flexibles']:
            g=f[f.moneda.eq(mon)&f.tipo.eq(t)]
            ax.scatter(100*g.vol_anualizada,100*g.rent_anualizada,s=24,marker=MARCAS[t],color=COLORES[t],alpha=.85,edgecolor='white',linewidth=.4)
        for k,(_,r) in enumerate(extremos[extremos.moneda.eq(mon)].iterrows()):
            arriba=r.sharpe_anualizado>0
            ax.annotate('Sharpe '+f'{r.sharpe_anualizado:.2f}'.replace('.',',').replace('-','−'),(100*r.vol_anualizada,100*r.rent_anualizada),
                xytext=(14,12 if arriba else -16),textcoords='offset points',fontsize=8.5,
                arrowprops=dict(arrowstyle='-',lw=.6,color='#444'))
        ax.set_xscale('log');ax.axhline(0,color='#555',lw=.8)
        ax.set_xticks([.5,1,2,5,10,20]);ax.set_xticklabels(['0,5','1','2','5','10','20']);ax.minorticks_off()
        ax.set_title(TITULO_MONEDA[mon],fontsize=9.5);ax.set_xlabel('Volatilidad anualizada (%, escala logarítmica)')
    axs[0].set_ylabel('Rentabilidad anualizada (%)');axs[0].yaxis.set_major_formatter(FuncFormatter(numero))
    leyenda_tipos(fig,'marca');figura(fig,'figura1_riesgo_rentabilidad')

def figura_indice_riqueza(mensual):
    """Figura 2. Índice de riqueza (julio de 2020 = 100) y caída desde el máximo de una
    cartera equiponderada de las series de cada tipo, rebalanceada cada mes."""
    filas=[]
    for (mon,t),g in mensual.sort_values('mes').groupby(['moneda','tipo']):
        indice=100*np.cumprod(1+g.rent_mes.to_numpy())
        maximo=np.maximum.accumulate(np.r_[100.,indice])[1:]
        filas.append(pd.DataFrame({'mes':g.mes.to_numpy(),'tipo':t,'moneda':mon,'rent_promedio':g.rent_mes.to_numpy(),
            'indice':indice,'caida_desde_maximo':indice/maximo-1}))
    riqueza=pd.concat(filas,ignore_index=True);guardar(riqueza,'tabla23_indice_riqueza')
    fig,axs=plt.subplots(2,2,figsize=(6.3,4.4),sharex=True,sharey='row',gridspec_kw={'height_ratios':[2.1,1]},layout='constrained')
    for j,mon in enumerate(['PEN','USD']):
        for t in ORDEN:
            g=riqueza[riqueza.moneda.eq(mon)&riqueza.tipo.eq(t)]
            fechas=pd.to_datetime(g.mes+'-01')+pd.offsets.MonthEnd(0)
            fechas=pd.DatetimeIndex([fechas.iloc[0]-pd.offsets.MonthEnd(1)]).append(pd.DatetimeIndex(fechas))
            w=np.r_[100.,g.indice.to_numpy()];c=100*np.r_[0.,g.caida_desde_maximo.to_numpy()]
            axs[0,j].plot(fechas,w,color=COLORES[t],lw=1.4)
            axs[1,j].plot(fechas,c,color=COLORES[t],lw=1);axs[1,j].fill_between(fechas,c,0,color=COLORES[t],alpha=.06)
        axs[0,j].axhline(100,color='#555',lw=.7);axs[1,j].axhline(0,color='#555',lw=.7)
        axs[0,j].set_title(TITULO_MONEDA[mon],fontsize=9.5)
    axs[0,0].set_ylabel('Índice (julio de 2020 = 100)');axs[1,0].set_ylabel('Caída desde\nel máximo (%)')
    for ax in axs.ravel():ax.yaxis.set_major_formatter(FuncFormatter(numero))
    axs[1,0].xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    leyenda_tipos(fig,'linea');figura(fig,'figura2_indice_riqueza')

def figura_sharpe_ordenado(f):
    """Figura 3. Razón de Sharpe de cada serie, ordenada de mayor a menor por moneda."""
    n=f.groupby('moneda').size()
    fig,axs=plt.subplots(1,2,figsize=(6.3,3.1),sharey=True,gridspec_kw={'width_ratios':[n['PEN'],n['USD']]},layout='constrained')
    for ax,mon in zip(axs,['PEN','USD']):
        g=f[f.moneda.eq(mon)].sort_values('sharpe_anualizado',ascending=False).reset_index(drop=True)
        ax.bar(np.arange(len(g)),g.sharpe_anualizado,color=[COLORES[t] for t in g.tipo],width=.82)
        ax.axhline(0,color='#555',lw=.7);ax.set_xticks([]);ax.set_xlim(-.8,len(g)-.2);ax.grid(axis='x',alpha=0)
        ax.set_title(f'{TITULO_MONEDA[mon]}, {len(g)} series',fontsize=9.5)
    axs[0].set_ylabel('Razón de Sharpe anualizada');axs[0].yaxis.set_major_formatter(FuncFormatter(numero))
    fig.supxlabel('Series ordenadas de mayor a menor razón de Sharpe',fontsize=9)
    leyenda_tipos(fig,'barra','outside upper center');figura(fig,'figura3_sharpe_ordenado')

def figura_diferencias_mensuales(dif,cc):
    """Figura 4. Diferencias mensuales del exceso mediano de cada tipo frente a Deuda.
    Muestra la trayectoria que resume la Tabla 14 sin repetir sus medias ni valores p;
    en negrita, los contrastes significativos con la corrección de Holm."""
    filas=[(r.moneda,r.tipo,r.p_holm) for r in cc.itertuples()]
    meses=sorted(dif.mes.unique())
    Z=np.vstack([dif[dif.moneda.eq(m)&dif.tipo.eq(t)].set_index('mes').diferencia_exceso_pp.reindex(meses).to_numpy() for m,t,_ in filas])
    lim=float(np.ceil(np.nanmax(np.abs(Z))))
    fig,ax=plt.subplots(figsize=(6.3,2.75),layout='constrained')
    im=ax.imshow(Z,aspect='auto',cmap='RdBu',norm=SymLogNorm(linthresh=.25,linscale=.7,vmin=-lim,vmax=lim),interpolation='nearest')
    ax.set_yticks(range(len(filas)));ax.set_yticklabels([f'{t} ({m})' for m,t,_ in filas])
    for etiqueta,(_,_,p) in zip(ax.get_yticklabels(),filas):
        if pd.notna(p) and p<.05:etiqueta.set_fontweight('bold')
    pos=[i for i,m in enumerate(meses) if m.endswith('-01')];ax.set_xticks(pos);ax.set_xticklabels([meses[i][:4] for i in pos])
    ax.grid(False)
    for borde in ax.spines.values():borde.set_visible(False)
    barra=fig.colorbar(im,ax=ax,orientation='horizontal',fraction=.08,pad=.04,aspect=45)
    marcas=[-lim,-1,-.25,0,.25,1,lim];barra.set_ticks(marcas);barra.set_ticklabels([numero(v) for v in marcas])
    barra.set_label('Diferencia mensual frente a Deuda (puntos porcentuales; escala logarítmica simétrica)',fontsize=8.5);barra.outline.set_visible(False)
    figura(fig,'figura4_diferencias_deuda')

def figura_regresion_parcial(df,ajuste,principal):
    """Figura 5. Residuos parciales de la variación cambiaria (residuo más su componente
    estimado), promediados por mes. Con el panel balanceado y el tipo de cambio común
    a todas las series de un mes, la pendiente de los 61 puntos es igual al coeficiente.
    Se rotulan el mes de mayor depreciación y los tres de menor rentabilidad parcial."""
    b=ajuste.params['var_tc']
    parcial=df[['mes','var_tc']].assign(parcial=ajuste.resid.to_numpy()+b*df.var_tc.to_numpy())
    if parcial.groupby('mes').var_tc.nunique().max()!=1:raise RuntimeError('La variación cambiaria debe ser común dentro de cada mes.')
    m=parcial.groupby('mes').agg(var_tc=('var_tc','first'),rent_parcial_media=('parcial','mean'),series=('parcial','size')).reset_index()
    pendiente,intercepto=np.polyfit(m.var_tc,m.rent_parcial_media,1)
    if not np.isclose(pendiente,b,rtol=1e-8,atol=1e-12):raise RuntimeError('La pendiente mensual no reproduce el coeficiente cambiario.')
    guardar(m,'tabla25_regresion_parcial_mensual')
    ic=principal.set_index('variable').loc['var_tc']
    X=100*m.var_tc;Y=100*m.rent_parcial_media;xs=np.linspace(X.min()-.3,X.max()+.3,50);xb,yb=X.mean(),Y.mean()
    fig,ax=plt.subplots(figsize=(6.3,3.3),layout='constrained')
    ax.fill_between(xs,yb+ic.ic95_inf*(xs-xb),yb+ic.ic95_sup*(xs-xb),color='#1F3A5F',alpha=.10,lw=0)
    ax.plot(xs,100*intercepto+b*xs,color='#1F3A5F',lw=1.6)
    ax.scatter(X,Y,s=20,color='#1F3A5F',alpha=.75,edgecolor='white',linewidth=.4)
    bajos=list(Y.sort_values().index[:3])
    # El mes más bajo se rotula a la izquierda y los otros dos a la derecha, escalonados;
    # el de mayor depreciación, a la izquierda para no salir del área del gráfico.
    rotulos=[(X.idxmax(),(-6,5),'right')]+[(i,d,h) for i,(d,h) in zip(bajos,[((-6,-4),'right'),((6,-5),'left'),((6,4),'left')])]
    for i,desplazamiento,lado in rotulos:
        anio,mes=m.mes[i].split('-');ax.annotate(f'{MESES[int(mes)-1]} {anio}',(X[i],Y[i]),xytext=desplazamiento,textcoords='offset points',fontsize=8.5,
            ha=lado,va='center',bbox=dict(boxstyle='round,pad=.15',fc='white',ec='none',alpha=.85))
    ax.axhline(0,color='#555',lw=.6);ax.axvline(0,color='#555',lw=.6)
    ax.set_xlabel('Variación mensual del tipo de cambio (%; positivo = depreciación del sol)')
    ax.set_ylabel('Rentabilidad parcial media (pp)')
    ax.xaxis.set_major_formatter(FuncFormatter(numero));ax.yaxis.set_major_formatter(FuncFormatter(numero))
    figura(fig,'figura5_regresion_parcial')

# ---------------------------------------------------------------------------
# Auditoría financiera y análisis complementario adecuados al panel mensual
# ---------------------------------------------------------------------------
def complementos(d, df, f):
    """No altera el procesado ni interpreta automáticamente un salto como error.
    Los contrastes se especifican por objetivo económico, no por valor p.
    """
    from statsmodels.stats.multitest import multipletests
    import statsmodels.api as sm
    # El rendimiento implícito en la cuota permite detectar incongruencias de
    # escala, pero no acredita por sí solo distribuciones ni cambios de clase.
    a=d.sort_values(['id_fondo_serie','mes']).copy()
    a['periodo_num']=pd.PeriodIndex(a.mes,freq='M').asi8
    g=a.groupby('id_fondo_serie')
    a['cuota_previa']=g.valor_cuota.shift()
    a['mes_previo']=g.mes.shift()
    consecutivo=(a.periodo_num-g.periodo_num.shift()==1)&a.imputado.eq(0)&g.imputado.shift().eq(0)
    a['retorno_cuota']=(a.valor_cuota/a.cuota_previa-1).where(consecutivo)
    a['diferencia_pp']=100*(a.rent_original-a.retorno_cuota)
    # Umbrales de auditoría EXPRESOS, no hipótesis de fraude ni regla automática
    # de corrección: |retorno| >=50%, o discrepancia de >=1 punto porcentual.
    a['salto_50pct']=a.rent_original.abs().ge(.50)&a.imputado.eq(0)
    a['discrepancia_cuota']=a.diferencia_pp.abs().ge(1)
    a['alerta']=a.salto_50pct|a.discrepancia_cuota
    a['estado_auditoria']=np.where(a.retorno_cuota.isna(),'Sin cuota previa consecutiva',np.where(a.discrepancia_cuota,'Diferencia >=1 pp: revisar fuente y eventos','Compatible con cuota al umbral de 1 pp'))
    cols=['mes','id_fondo_serie','tipo','moneda','valor_cuota','mes_previo','cuota_previa','rent_original','rent_mes','retorno_cuota','diferencia_pp','salto_50pct','discrepancia_cuota','estado_auditoria','archivo','pagina','fila_original']
    guardar(a.loc[a.alerta,cols],'tabla9_auditoria_financiera')
    guardar(a.groupby(['tipo','moneda']).agg(filas=('mes','size'),cuotas_comparables=('retorno_cuota','count'),saltos_50pct=('salto_50pct','sum'),discrepancias=('discrepancia_cuota','sum')).reset_index(),'tabla10_control_cuotas')
    # Sensibilidad estricta: omitimos ventanas con saltos extremos actuales o
    # pasados, sin sustituir su valor ni borrar observaciones de la base final.
    # Una alerta en t afecta Y_t, X3_(t+1) y X1_(t+1...t+12); se deja fuera
    # toda la ventana para no introducir un retorno implícito inventado.
    a['ventana_salto']=False
    a['ventana_alerta']=False
    for _,h in a.groupby('id_fondo_serie'):
        s=h.set_index('periodo_num').salto_50pct.reindex(range(h.periodo_num.min(),h.periodo_num.max()+1),fill_value=False)
        a.loc[h.index,'ventana_salto']=s.rolling(13,min_periods=1).max().reindex(h.periodo_num).to_numpy().astype(bool)
        s2=h.set_index('periodo_num').alerta.reindex(range(h.periodo_num.min(),h.periodo_num.max()+1),fill_value=False)
        a.loc[h.index,'ventana_alerta']=s2.rolling(13,min_periods=1).max().reindex(h.periodo_num).to_numpy().astype(bool)
    alt=a[a.muestra_modelo.eq(1)&~a.ventana_salto].copy()
    if len(alt)<=1000:raise RuntimeError('Sensibilidad de ventanas: menos de 1001 filas completas')
    _,t=estimar(alt,'sensibilidad_ventana_saltos_50pct')
    alt2=a[a.muestra_modelo.eq(1)&~a.ventana_alerta].copy()
    if len(alt2)>1000:
        _,t2=estimar(alt2,'sensibilidad_ventana_todas_alertas');t=pd.concat([t,t2],ignore_index=True)
    guardar(t,'tabla11_robustez_ventana_saltos')
    # Efectos fijos de fondo/serie: compara cada unidad consigo misma;
    # el tipo y la moneda constantes quedan absorbidos. NO se incluyen efectos
    # fijos mensuales: absorberían por completo el tipo de cambio común del mes.
    # Con rezago de Y el estimador within puede sufrir sesgo dinámico; no es causal.
    variables=['rent_mes','vol12','var_tc','rent_lag1']
    tablas=[]
    for nombre,datos in [('efectos_fijos',df),('efectos_fijos_sin_ventanas_salto',alt)]:
        h=datos.groupby('id_fondo_serie').filter(lambda x:len(x)>=2).copy()
        w=h[variables]-h.groupby('id_fondo_serie')[variables].transform('mean')
        fit=sm.OLS(w.rent_mes,w[variables[1:]]).fit()
        if np.linalg.matrix_rank(fit.model.exog)<3 or len(h)<=1000:raise RuntimeError('Efectos fijos sin rango o muestra suficiente')
        # Agrupación mensual como sensibilidad a la dependencia transversal;
        # agrupar por mes no corrige por sí solo autocorrelación entre meses.
        # Dos vías se presenta adicionalmente, sin ocultar covarianzas inválidas.
        grupos=np.column_stack([pd.factorize(h.id_fondo_serie)[0],pd.factorize(h.mes)[0]])
        for modo,gg in [('mes',grupos[:,1]),('serie_mes',grupos)]:
            rr=fit.get_robustcov_results(cov_type='cluster',groups=gg,use_correction=True,df_correction=True,use_t=True)
            # Ajuste conservador de grados de libertad por los interceptos absorbidos.
            # Hace explícito el ajuste de n-k que el modelo transformado no conoce.
            factor=np.sqrt((len(h)-3)/(len(h)-h.id_fondo_serie.nunique()-3))
            from scipy.stats import t as tdist
            se=rr.bse*factor;gl=h.mes.nunique()-1;crit=tdist.ppf(.975,gl);pv=2*tdist.sf(np.abs(rr.params/se),gl)
            ic=np.column_stack([rr.params-crit*se,rr.params+crit*se]); tablas.append(pd.DataFrame({'modelo':nombre,'agrupacion':modo,'variable':variables[1:],'coeficiente':rr.params,'error_estandar':se,'p_valor':pv,'ic95_inf':ic[:,0],'ic95_sup':ic[:,1],'n':len(h),'r2_within':fit.rsquared,'series':h.id_fondo_serie.nunique(),'meses':h.mes.nunique(),'inferencia_valida':np.isfinite(se)&(se>0),'gl_inferencia':gl}))
    guardar(pd.concat(tablas,ignore_index=True),'tabla12_efectos_fijos')
    # Inferencia principal y sensibilidad a la dimensión de agrupación.
    ajuste=smf.ols(FORMULA,data=df).fit(); sal=[]
    for nombre,grupos in [('serie',pd.factorize(df.id_fondo_serie)[0]),('mes',pd.factorize(df.mes)[0])]:
        r=ajuste.get_robustcov_results(cov_type='cluster',groups=grupos,use_t=True,df_correction=True,use_correction=True); ic=r.conf_int()
        sal.append(pd.DataFrame({'agrupacion':nombre,'variable':ajuste.model.exog_names,'coeficiente':r.params,'error_estandar':r.bse,'p_valor':r.pvalues,'ic95_inf':ic[:,0],'ic95_sup':ic[:,1],'n':len(df),'clusters':len(np.unique(grupos))}))
    guardar(pd.concat(sal,ignore_index=True),'tabla13_sensibilidad_inferencia')
    # Contraste de desempeño: exceso mensual mediano por tipo y moneda frente
    # a deuda (referencia económica). Se exige >=3 series en ambas categorías
    # por mes y >=12 meses consecutivos comunes. HAC(3) en la diferencia de
    # medianas mensuales; Holm controla la multiplicidad de contrastes.
    # No equivale a un test del Sharpe ni a una comparación causal.
    agregado=d.dropna(subset=['exceso']).groupby(['mes','tipo','moneda']).exceso.agg(['median','size']).reset_index()
    agregado=agregado[agregado['size']>=3]
    contrastes=[]; sharpe_contrastes=[]; diferencias=[]
    rng=np.random.default_rng(501)
    for moneda,h in agregado.groupby('moneda'):
        piv=h.pivot(index='mes',columns='tipo',values='median')
        if 'Deuda' not in piv:continue
        for tipo in sorted(c for c in piv.columns if c!='Deuda'):
            s=(piv[tipo]-piv.Deuda).dropna().sort_index(); periods=pd.PeriodIndex(s.index,freq='M').asi8
            if not len(s):continue
            bloques=np.cumsum(np.r_[True,np.diff(periods)!=1]); bloques_validos=[s.iloc[np.flatnonzero(bloques==k)] for k in np.unique(bloques)]
            z=max(bloques_validos,key=len)
            if len(z)<12:continue
            # Trayectoria mensual del contraste, publicada en tabla24 y dibujada en la figura 4.
            diferencias.append(pd.DataFrame({'moneda':moneda,'tipo':tipo,'referencia':'Deuda','mes':z.index,'diferencia_exceso_pp':100*z.to_numpy()}))
            modelo=sm.OLS(z.to_numpy(),np.ones((len(z),1))).fit(cov_type='HAC',cov_kwds={'maxlags':3,'use_correction':True},use_t=True)
            # Remuestreo pareado circular por bloques de tres meses: preserva
            # la dependencia contemporánea de ambos tipos y parcialmente la temporal.
            # IC exploratorios por contraste, NO ajustados por multiplicidad.
            pareja=piv.loc[z.index,[tipo,'Deuda']].to_numpy();n=len(pareja)
            def sh(x):
                sd=x.std(axis=0,ddof=1);return np.divide(x.mean(axis=0)*np.sqrt(12),sd,out=np.full(2,np.nan),where=sd>0)
            sj=sh(pareja); boots=[]
            for _ in range(1999):
                ini=rng.integers(0,n,size=int(np.ceil(n/3)));ix=((ini[:,None]+np.arange(3))%n).ravel()[:n]
                q=sh(pareja[ix]);boots.append(q[0]-q[1])
            b=np.asarray(boots);b=b[np.isfinite(b)];ci=np.quantile(b,[.025,.975]) if len(b)>=1800 else [np.nan,np.nan]
            sharpe_contrastes.append({'moneda':moneda,'tipo':tipo,'referencia':'Deuda','inicio':z.index[0],'fin':z.index[-1],'n_meses':n,'sharpe_tipo':sj[0],'sharpe_deuda':sj[1],'diferencia_sharpe':sj[0]-sj[1],'ic95_inf':ci[0],'ic95_sup':ci[1],'remuestras_validas':len(b),'semilla':501,'bloque_meses':3})
            ic=modelo.conf_int()[0]; contrastes.append({'moneda':moneda,'tipo':tipo,'referencia':'Deuda','inicio':z.index[0],'fin':z.index[-1],'n_meses':len(z),'diferencia_media_pp':100*modelo.params[0],'ic95_inf_pp':100*ic[0],'ic95_sup_pp':100*ic[1],'p_valor':modelo.pvalues[0]})
    cc=pd.DataFrame(contrastes,columns=['moneda','tipo','referencia','inicio','fin','n_meses','diferencia_media_pp','ic95_inf_pp','ic95_sup_pp','p_valor'])
    cc['p_holm']=np.nan
    valid=cc.p_valor.notna()
    if valid.any():cc.loc[valid,'p_holm']=multipletests(cc.loc[valid,'p_valor'],method='holm')[1]
    guardar(cc,'tabla14_contrastes_tipo')
    guardar(pd.DataFrame(sharpe_contrastes),'tabla19_sharpe_contraste_exploratorio')
    dif=pd.concat(diferencias,ignore_index=True) if diferencias else pd.DataFrame(columns=['moneda','tipo','referencia','mes','diferencia_exceso_pp'])
    guardar(dif,'tabla24_diferencias_mensuales_deuda')
    # Comparación ajustada al riesgo: distribución del Sharpe entre unidades,
    # se preservan grupos pequeños como descriptivos y se informa el tamaño.
    sharpe=f.groupby(['tipo','moneda']).sharpe_anualizado.agg(n='count',mediana='median',q25=lambda x:x.quantile(.25),q75=lambda x:x.quantile(.75)).reset_index()
    guardar(sharpe,'tabla15_distribucion_sharpe')
    # Estadística descriptiva de retornos, con percentiles y número de unidades.
    desc=d.groupby(['tipo','moneda']).rent_mes.agg(n='size',media='mean',mediana='median',desv='std',p05=lambda x:x.quantile(.05),p95=lambda x:x.quantile(.95),minimo='min',maximo='max').reset_index()
    guardar(desc,'tabla16_descriptivos')
    # Comparación descriptiva de métricas recalculadas sin ventanas con saltos.
    # No sustituye la tabla base. Las series requieren >=12 meses observados.
    out=[]
    for (id_,tipo,mon),h in a[~a.ventana_salto].dropna(subset=['exceso']).groupby(['id_fondo_serie','tipo','moneda']):
        if len(h)<12:continue
        r=h.rent_mes.to_numpy();e=h.exceso.to_numpy();des=e.std(ddof=1)
        out.append({'tipo':tipo,'moneda':mon,'id_fondo_serie':id_,'n_meses':len(h),'rent_anualizada':-1 if (r==-1).any() else np.expm1(np.log1p(r).mean()*12),'vol_anualizada':r.std(ddof=1)*np.sqrt(12),'sharpe_anualizado':e.mean()/des*np.sqrt(12) if des>0 else np.nan})
    ff=pd.DataFrame(out,columns=['tipo','moneda','id_fondo_serie','n_meses','rent_anualizada','vol_anualizada','sharpe_anualizado'])
    guardar(ff.groupby(['tipo','moneda']).agg(unidades=('id_fondo_serie','nunique'),rent_mediana=('rent_anualizada','median'),vol_mediana=('vol_anualizada','median'),sharpe_mediana=('sharpe_anualizado','median')).reset_index(),'tabla17_desempeno_sensibilidad')
    cob=pd.DataFrame([{'muestra':'panel','filas':len(d),'series':d.id_fondo_serie.nunique(),'meses':d.mes.nunique()},{'muestra':'MCO completo','filas':len(df),'series':df.id_fondo_serie.nunique(),'meses':df.mes.nunique()},{'muestra':'sin ventanas de salto','filas':len(alt),'series':alt.id_fondo_serie.nunique(),'meses':alt.mes.nunique()},{'muestra':'sin ventanas de todas las alertas','filas':len(alt2),'series':alt2.id_fondo_serie.nunique(),'meses':alt2.mes.nunique()}]);guardar(cob,'tabla18_muestras')
    # Figura 4: trayectoria mensual de cada contraste; sus medias y valores p quedan en la tabla 14.
    if not dif.empty:figura_diferencias_mensuales(dif,cc)
    print('\nAUDITORÍA FINANCIERA: alertas',int(a.alerta.sum()),'; saltos >=50%:',int(a.salto_50pct.sum()))
    print(cob.to_string(index=False));print(cc.to_string(index=False))


def main():
    d=pd.read_csv(RAIZ/'datos_procesados/datos_procesados_2024200501G.csv',dtype={'mes':str})
    # El modelo usa toda la base procesada, no un subconjunto silencioso.
    if d.isna().any().any() or d.duplicated(['id_fondo_serie','mes']).any():raise RuntimeError('Base inválida: faltantes o duplicados')
    assert d.groupby('id_fondo_serie').mes.nunique().eq(d.mes.nunique()).all()
    assert len(d)==d.mes.nunique()*d.id_fondo_serie.nunique()
    df=d.copy()
    if len(df)<=1000:raise RuntimeError('Muestra de modelo insuficiente.')
    # Las categorías de vida corta no se ocultan: se describen sobre datos
    # observados en el mismo periodo, pero NO se mezclan con el panel balanceado.
    obs=pd.read_csv(RAIZ/'datos_procesados/base_integrada_observada.csv',dtype={'mes':str})
    obs=obs[obs.mes.between(d.mes.min(),d.mes.max())]
    disp=obs.groupby(['tipo','moneda']).agg(series_observadas=('id_fondo_serie','nunique'),filas_observadas=('mes','size'),meses_observados=('mes','nunique'),retorno_mediano_observado=('rent_mes','median')).reset_index()
    inc=d.groupby(['tipo','moneda']).agg(series_panel=('id_fondo_serie','nunique'),filas_panel=('mes','size'),imputadas=('imputado','sum'),winsorizadas=('atipico','sum')).reset_index()
    disp=disp.merge(inc,on=['tipo','moneda'],how='outer');k=['series_panel','filas_panel','imputadas','winsorizadas'];disp[k]=disp[k].fillna(0).astype(int)
    guardar(disp,'tabla20_cobertura_tipos_observados')
    # Comparación descriptiva de series fuera del panel. No afirma igualdad de
    # horizonte: métricas solo para tramos consecutivos de al menos 12 meses.
    contexto=pd.read_csv(S/'tabla_contexto_bcrp.csv',dtype={'mes':str})
    obs=obs.merge(contexto[['mes','rf_pen','rf_usd']],on='mes',how='left',validate='many_to_one');obs['rf']=np.where(obs.moneda.eq('PEN'),obs.rf_pen,obs.rf_usd)
    filas_obs=[]
    for (id_,tipo,mon),h in obs.groupby(['id_fondo_serie','tipo','moneda']):
        h=h.sort_values('mes').dropna(subset=['rf']);periodos=pd.PeriodIndex(h.mes,freq='M').asi8
        if not len(h):continue
        segmentos=h.groupby(np.cumsum(np.r_[True,np.diff(periodos)!=1]));z=max((q for _,q in segmentos),key=len)
        if len(z)<12:continue
        r=z.rent_mes.to_numpy();e=r-z.rf.to_numpy();sd=e.std(ddof=1)
        filas_obs.append(dict(id_fondo_serie=id_,tipo=tipo,moneda=mon,inicio=z.mes.iloc[0],fin=z.mes.iloc[-1],meses=len(z),rent_anualizada=-1 if (r==-1).any() else np.expm1(np.log1p(r).mean()*12),vol_anualizada=r.std(ddof=1)*np.sqrt(12),sharpe_anualizado=e.mean()/sd*np.sqrt(12) if sd>0 else np.nan))
    guardar(pd.DataFrame(filas_obs),'tabla21_desempeno_observado_contextual')
    # Métricas por fondo/serie, tipo y moneda; solo retornos y tasa observados.
    # La anualización usa meses observados (mínimo 12), no implica 12 meses consecutivos.
    # El Sharpe usa desviación del exceso mensual y tasa interbancaria como proxy,
    # no como rendimiento de un activo libre de riesgo directamente invertible.
    filas=[]
    for (id_,tipo,mon),g in d.dropna(subset=['exceso']).groupby(['id_fondo_serie','tipo','moneda']):
        if len(g)<12:continue
        r=g.rent_mes.to_numpy();e=g.exceso.to_numpy();des=e.std(ddof=1)
        geo=-1. if (r==-1).any() else np.expm1(np.log1p(r).mean()*12)
        filas.append({'id_fondo_serie':id_,'tipo':tipo,'moneda':mon,'n_meses':len(g),'rent_anualizada':geo,'vol_anualizada':r.std(ddof=1)*np.sqrt(12),'sharpe_anualizado':e.mean()/des*np.sqrt(12) if des>0 else np.nan,'meses_con_perdida':(r<0).mean()})
    f=pd.DataFrame(filas)
    if f.empty:raise RuntimeError('Ninguna unidad tiene 12 meses válidos para desempeño.')
    guardar(f,'tabla1_metricas_por_fondo_serie')
    resumen=f.groupby(['tipo','moneda']).agg(unidades=('id_fondo_serie','nunique'),rent_mediana=('rent_anualizada','median'),vol_mediana=('vol_anualizada','median'),sharpe_mediana=('sharpe_anualizado','median'),meses_perdida_mediana=('meses_con_perdida','median')).reset_index()
    guardar(resumen,'tabla2_riesgo_rentabilidad_por_tipo')
    # MCO; corrección de inferencia, no modificación de coeficientes. Dos dimensiones de agrupación.
    inicial,principal=estimar(df,'principal_cluster_fondo_mes')
    guardar(principal,'tabla3_modelo_principal')
    clasico=pd.DataFrame({'variable':inicial.model.exog_names,'coeficiente':inicial.params.to_numpy(),'error_estandar_mco':inicial.bse.to_numpy(),'p_valor_mco':inicial.pvalues.to_numpy()})
    guardar(clasico,'tabla4_modelo_inicial_mco')
    # Sensibilidad principal: cambiar tratamiento manteniendo EXACTAMENTE la muestra.
    # La versión original conserva estimaciones de vacíos internos señaladas por imputado.
    original=df.copy();original[['rent_mes','vol12','rent_lag1']]=original[['rent_original','vol12_original','rent_lag1_original']].to_numpy()
    _,raw=estimar(original,'misma_muestra_sin_winsorizar');rob=pd.concat([principal,raw],ignore_index=True)
    # Robustez adicional sin filas imputadas ni ventanas que usen imputaciones.
    # Este subconjunto sí puede ser no balanceado; se declara su tamaño efectivo.
    observadas=df[df.imputado.eq(0)&df.historia_imputada.eq(0)].copy()
    if len(observadas)>1000 and observadas.mes.nunique()>=24:
        _,sens=estimar(observadas,'sin_imputacion_actual_ni_historica');rob=pd.concat([rob,sens],ignore_index=True)
    guardar(rob,'tabla5_robustez')
    # Comparar desempeño por serie con y sin winsorización sobre el mismo panel.
    sin=[]
    for (id_,tipo,mon),h in original.groupby(['id_fondo_serie','tipo','moneda']):
        r=h.rent_mes.to_numpy();e=r-h.rf_mensual.to_numpy();sd=e.std(ddof=1)
        sin.append(dict(id_fondo_serie=id_,tipo=tipo,moneda=mon,meses=len(h),rent_anualizada=-1 if (r==-1).any() else np.expm1(np.log1p(r).mean()*12),vol_anualizada=r.std(ddof=1)*np.sqrt(12),sharpe_anualizado=e.mean()/sd*np.sqrt(12) if sd>0 else np.nan))
    guardar(pd.DataFrame(sin),'tabla22_desempeno_sin_winsorizar')
    vif=pd.DataFrame({'variable':inicial.model.exog_names,'VIF':[variance_inflation_factor(inicial.model.exog,i) for i in range(inicial.model.exog.shape[1])]})
    guardar(vif,'tabla6_vif')
    # Correlación residual rezagada descriptiva dentro de cada serie; no apilar para aplicar DW/ADF.
    resid=df[['id_fondo_serie','mes']].copy();resid['residuo']=inicial.resid.to_numpy();resid=resid.sort_values(['id_fondo_serie','mes'])
    resid['mes_num']=pd.PeriodIndex(resid.mes,freq='M').asi8
    g=resid.groupby('id_fondo_serie');resid['rezago']=g.residuo.shift();resid.loc[resid.mes_num-g.mes_num.shift()!=1,'rezago']=np.nan
    guardar(pd.DataFrame([{'n':len(df),'fondos_series':df.id_fondo_serie.nunique(),'meses':df.mes.nunique(),'corr_residuos_lag1':resid[['residuo','rezago']].corr().iloc[0,1],'advertencia':'Correlación descriptiva; errores agrupados, no prueba causal.'}]),'tabla7_diagnosticos')
    estilo()
    figura_riesgo_rentabilidad(f)
    mensual=d.groupby(['mes','tipo','moneda']).rent_mes.mean().reset_index();guardar(mensual,'tabla8_rentabilidades_mensuales')
    figura_indice_riqueza(mensual)
    figura_sharpe_ordenado(f)
    figura_regresion_parcial(df,inicial,principal)
    complementos(d,df,f)
    print(resumen.to_string(index=False));print(principal.to_string(index=False))
    with (RAIZ/'log_ejecucion.txt').open('a',encoding='utf-8') as ar:ar.write(f'{datetime.now(timezone(timedelta(hours=-5))):%Y-%m-%d %H:%M:%S} | 04_analisis | {len(df)} filas; tablas y figuras guardadas\n')

if __name__=='__main__':main()
