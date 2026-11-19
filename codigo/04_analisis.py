# Autora: Amy Pamela Guadalupe Cordova
# Código de matrícula: 2024200501G
# Tema 79: Fondos mutuos en el Perú: rentabilidad y riesgo por tipo de fondo
# Fecha de extracción: 2026-11-19
"""Desempeño ajustado al riesgo por tipo/moneda y un modelo de tres X.
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
    t=pd.DataFrame({'modelo':nombre,'variable':ajuste.model.exog_names,'coeficiente':robusto.params,'error_estandar':robusto.bse,'p_valor':robusto.pvalues,'ic95_inf':conf[:,0],'ic95_sup':conf[:,1],'n':int(ajuste.nobs),'r2':ajuste.rsquared,'fondos_series':d.id_fondo_serie.nunique(),'meses':d.mes.nunique()})
    return ajuste,t

def main():
    d=pd.read_csv(RAIZ/'datos_procesados/datos_procesados_2024200501G.csv',dtype={'mes':str})
    df=d[d.muestra_modelo.eq(1)].copy()
    if len(df)<=1000:raise RuntimeError('Muestra de modelo insuficiente.')
    # Métricas por fondo/serie, tipo y moneda; solo retornos y tasa observados.
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
    alt=df[df.atipico.eq(0)].copy();rob=principal.copy()
    if len(alt)>1000 and alt.mes.nunique()>=24 and alt.id_fondo_serie.nunique()>=10:
        try:_,t=estimar(alt,'sensibilidad_sin_atipicos');rob=pd.concat([rob,t],ignore_index=True)
        except RuntimeError as e:print('Robustez no estimable:',e)
    guardar(rob,'tabla5_robustez')
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
    print(resumen.to_string(index=False));print(principal.to_string(index=False))
    with (RAIZ/'log_ejecucion.txt').open('a',encoding='utf-8') as ar:ar.write(f'{datetime.now(timezone(timedelta(hours=-5))):%Y-%m-%d %H:%M:%S} | 04_analisis | {len(df)} filas; tablas y figuras guardadas\n')

if __name__=='__main__':main()
