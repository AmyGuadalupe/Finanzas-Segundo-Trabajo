# Autora: Amy Pamela Guadalupe Cordova
# Código de matrícula: 2024200501G
# Tema 79: Fondos mutuos en el Perú: rentabilidad y riesgo por tipo de fondo
# Fecha de extracción: 2026-11-21
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
import statsmodels.formula.api as smf
from statsmodels.stats.outliers_influence import variance_inflation_factor

RAIZ=Path(__file__).resolve().parents[1]; S=RAIZ/'salidas';S.mkdir(exist_ok=True)
FORMULA='rent_mes ~ vol12 + var_tc + rent_lag1 + C(tipo) + C(moneda)'

def guardar(d,n):d.to_csv(S/(n+'.csv'),index=False,float_format='%.10g')
def figura(fig,n):
    fig.tight_layout();fig.savefig(S/(n+'.png'),dpi=160,bbox_inches='tight');plt.close(fig)

def estimar(d,nombre):
    ajuste=smf.ols(FORMULA,data=d).fit()
    if np.linalg.matrix_rank(ajuste.model.exog)<ajuste.model.exog.shape[1]:raise RuntimeError('Modelo sin rango completo; revisar variables o categorías.')
    grupos=np.column_stack([pd.factorize(d.id_fondo_serie)[0],pd.factorize(d.mes)[0]])
    robusto=ajuste.get_robustcov_results(cov_type='cluster',groups=grupos,use_correction=True,df_correction=True,use_t=True)
    conf=robusto.conf_int()
    t=pd.DataFrame({'modelo':nombre,'variable':ajuste.model.exog_names,'coeficiente':robusto.params,'error_estandar':robusto.bse,'p_valor':robusto.pvalues,'ic95_inf':conf[:,0],'ic95_sup':conf[:,1],'n':int(ajuste.nobs),'r2':ajuste.rsquared,'fondos_series':d.id_fondo_serie.nunique(),'meses':d.mes.nunique(),'inferencia_valida':np.isfinite(robusto.bse)&(robusto.bse>0)})
    return ajuste,t

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
    contrastes=[]; sharpe_contrastes=[]
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
    # Figuras complementarias con escalas robustas; no recortar puntos ni ejes
    # para esconder extremos. Los extremos se muestran separadamente en tabla 9.
    fig,axs=plt.subplots(1,2,figsize=(11,5),sharey=True)
    for ax,mon in zip(axs,['PEN','USD']):
        q=sharpe[sharpe.moneda.eq(mon)&sharpe.n.gt(0)].sort_values('mediana')
        ax.errorbar(q.mediana,q.tipo,xerr=[q.mediana-q.q25,q.q75-q.mediana],fmt='o',capsize=3,color='#315c80');ax.axvline(0,color='gray',lw=1);ax.set(title=mon,xlabel='Sharpe: mediana e intervalo intercuartílico')
    figura(fig,'figura5_distribucion_sharpe')
    fig,ax=plt.subplots(figsize=(9,5));sub=cc.dropna(subset=['ic95_inf_pp','ic95_sup_pp'])
    if not sub.empty:
        ax.errorbar(sub.diferencia_media_pp,sub.tipo+' | '+sub.moneda,xerr=[sub.diferencia_media_pp-sub.ic95_inf_pp,sub.ic95_sup_pp-sub.diferencia_media_pp],fmt='o',capsize=3,color='#315c80');ax.axvline(0,color='gray',lw=1)
    else:ax.text(.5,.5,'Sin contrastes estimables con los criterios establecidos',transform=ax.transAxes,ha='center')
    ax.set(title='Diferencia de exceso mensual mediano frente a deuda',xlabel='Puntos porcentuales; IC95% HAC sin ajuste de multiplicidad');figura(fig,'figura6_contrastes_tipo')
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
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'axes.grid':True,'grid.alpha':.2})
    fig,axs=plt.subplots(1,2,figsize=(11,4),sharey=True)
    for ax,mon in zip(axs,['PEN','USD']):
        for tipo,gg in f[f.moneda.eq(mon)].groupby('tipo'):ax.scatter(gg.vol_anualizada*100,gg.rent_anualizada*100,label=tipo,s=18,alpha=.6)
        ax.set(title=mon,xlabel='Volatilidad anualizada (%)',ylabel='Rentabilidad anualizada (%)')
        ax.set_xscale('symlog',linthresh=1);ax.set_yscale('symlog',linthresh=5)
        if ax.has_data():ax.legend(fontsize=7,loc='best')
    figura(fig,'figura1_riesgo_rentabilidad')
    fig,axs=plt.subplots(1,2,figsize=(11,4),sharey=True)
    for ax,mon in zip(axs,['PEN','USD']):
        a=resumen[resumen.moneda.eq(mon)].sort_values('sharpe_mediana');ax.barh(a.tipo,a.sharpe_mediana,color='#315c80');ax.set(title=mon,xlabel='Mediana del Sharpe anualizado')
    figura(fig,'figura2_sharpe_por_tipo')
    mensual=d.groupby(['mes','tipo','moneda']).rent_mes.mean().reset_index();guardar(mensual,'tabla8_rentabilidades_mensuales')
    fig,axs=plt.subplots(2,1,figsize=(11,7),sharex=True)
    for ax,mon in zip(axs,['PEN','USD']):
        for tipo,g in mensual[mensual.moneda.eq(mon)].groupby('tipo'):
            ax.plot(pd.to_datetime(g.mes+'-01'),100*g.rent_mes,label=tipo,lw=1)
        ax.set(title=mon,ylabel='Rentabilidad mensual (%)');ax.legend(fontsize=7,ncol=3)
    figura(fig,'figura3_rentabilidad_mensual')
    fig,ax=plt.subplots(figsize=(7,4));x=principal[principal.variable.isin(['vol12','var_tc','rent_lag1'])].dropna(subset=['ic95_inf','ic95_sup'])
    if not x.empty:ax.errorbar(x.coeficiente,x.variable,xerr=[x.coeficiente-x.ic95_inf,x.ic95_sup-x.coeficiente],fmt='o',color='#315c80',capsize=4)
    ax.axvline(0,color='gray',lw=1);ax.set(xlabel='Coeficiente e intervalo de confianza al 95 %',title='Modelo principal: tres factores');figura(fig,'figura4_coeficientes')
    complementos(d,df,f)
    print(resumen.to_string(index=False));print(principal.to_string(index=False))
    with (RAIZ/'log_ejecucion.txt').open('a',encoding='utf-8') as ar:ar.write(f'{datetime.now(timezone(timedelta(hours=-5))):%Y-%m-%d %H:%M:%S} | 04_analisis | {len(df)} filas; tablas y figuras guardadas\n')

if __name__=='__main__':main()
