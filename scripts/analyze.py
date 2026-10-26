"""Run e-commerce conversion funnel SQL analysis and export a dashboard."""
import argparse
import json
import sqlite3
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from dashboard_utils import dashboard

BASE=Path(__file__).resolve().parents[1]

def funnel(events: pd.DataFrame) -> pd.DataFrame:
    required={'timestamp','visitorid','event'}
    if not required.issubset(events.columns):
        raise ValueError('Missing columns: '+', '.join(sorted(required-set(events.columns))))
    events=events.copy()
    events['timestamp']=pd.to_numeric(events['timestamp'],errors='coerce')
    events=events.dropna(subset=['timestamp','visitorid','event'])
    events=events[events['event'].isin(['view','addtocart','transaction'])]
    if events.empty:
        raise ValueError('No valid events found')
    events['timestamp']=events['timestamp'].astype('int64')
    # Only used columns are loaded into SQLite; extra raw dataset columns are allowed.
    with sqlite3.connect(':memory:') as con:
        events[['timestamp','visitorid','event']].to_sql('events',con,index=False,if_exists='replace',chunksize=10000)
        con.execute('CREATE INDEX idx_visitor_event_ts ON events (visitorid, event, timestamp)')
        sql=(BASE/'sql/funnel.sql').read_text()
        return pd.read_sql_query(sql,con)

def summarize(stages):
    views=len(stages)
    carts=int(stages.first_cart_ms.notna().sum())
    purchases=int(stages.first_purchase_ms.notna().sum())
    assert views>=carts>=purchases
    return {'viewers':views,'added_to_cart':carts,'purchasers':purchases,
            'view_to_cart_rate':carts/views if views else 0,
            'cart_to_purchase_rate':purchases/carts if carts else 0,
            'overall_conversion_rate':purchases/views if views else 0}

def run(data_path=None, output_dir=None):
    source=Path(data_path or BASE/'data/raw/events.csv')
    out=Path(output_dir or BASE/'outputs')
    out.mkdir(parents=True,exist_ok=True)
    events=pd.read_csv(source,low_memory=False)
    stages=funnel(events)
    metrics=summarize(stages)
    metrics.update({'source_filename':source.name,'demo_data':source.resolve()==(BASE/'data/raw/events.csv').resolve()
                    and (BASE/'data/raw/DEMO_DATA.txt').exists()})
    stages['first_view_month']=pd.to_datetime(stages.first_view_ms,unit='ms',utc=True).dt.strftime('%Y-%m')
    cohorts=stages.groupby('first_view_month',sort=True).agg(
        viewers=('visitorid','size'),added_to_cart=('first_cart_ms','count'),purchasers=('first_purchase_ms','count'))
    cohorts['conversion_rate']=cohorts.purchasers/cohorts.viewers
    cohorts=cohorts.reset_index().rename(columns={'first_view_month':'cohort_month'})
    cohorts.to_csv(out/'monthly_funnel.csv',index=False)
    stages.to_csv(out/'visitor_funnel.csv',index=False)
    (out/'metrics.json').write_text(json.dumps(metrics,indent=2))

    labels=['Viewed product','Added to cart','Purchased']
    vals=[metrics['viewers'],metrics['added_to_cart'],metrics['purchasers']]
    fig1=go.Figure(go.Bar(x=labels,y=vals,marker_color=['#51d3c7','#5795ef','#af91f5'],text=[f'{x:,}' for x in vals],textposition='outside'))
    fig1.update_yaxes(title='Unique visitors',range=[0,max(vals)*1.16])
    fig2=go.Figure()
    fig2.add_trace(go.Scatter(x=cohorts.cohort_month,y=cohorts.conversion_rate*100,mode='lines+markers',name='Purchase conversion',line=dict(color='#36d6bd',width=3)))
    fig2.update_yaxes(title='% of first-time viewers in cohort',ticksuffix='%')
    fig3=go.Figure(go.Bar(x=['View → Cart','Cart → Purchase'],
          y=[100*metrics['view_to_cart_rate'],100*metrics['cart_to_purchase_rate']],marker_color=['#5795ef','#af91f5'],
          text=[f"{100*metrics['view_to_cart_rate']:.1f}%",f"{100*metrics['cart_to_purchase_rate']:.1f}%"],textposition='outside'))
    fig3.update_yaxes(title='Step conversion (%)',range=[0,100])

    biggest='view-to-cart' if metrics['view_to_cart_rate'] < metrics['cart_to_purchase_rate'] else 'cart-to-purchase'
    recommendation=('Investigate whether product discovery and product-detail pages make it easy to add items to cart.'
                    if biggest=='view-to-cart' else 'Audit checkout usability, payment errors, and any unexpected costs before placing an order.')
    finding=f'The largest proportional drop-off is at <b>{biggest}</b>. {recommendation} Test any changes with an experiment before claiming an improvement.'
    footnote=('DATA: SYNTHETIC DEMO — NOT REAL CUSTOMER RESULTS. ' if metrics['demo_data'] else 'DATA: USER-SUPPLIED DATASET. ')+(
        'Visitor-level chronological progression, where the next step may involve a different product; does not infer causality. '
        'Monthly cohorts are grouped by first product view and may have different follow-up windows near data end.')
    dashboard(out/'dashboard.html','E-commerce Conversion Funnel',
              'Understand where visitors exit the product journey and what to investigate next.',
              [('Product viewers',f"{metrics['viewers']:,}"),('Reached cart',f"{metrics['added_to_cart']:,}"),
               ('Purchasers',f"{metrics['purchasers']:,}"),('View → Purchase',f"{metrics['overall_conversion_rate']:.1%}")],
              [('Funnel progression',fig1),('Conversion by first-view month',fig2),('Conversion between steps',fig3)],finding,footnote)
    fig,ax=plt.subplots(figsize=(9.8,5.5))
    fig.patch.set_facecolor('#0b1324');ax.set_facecolor('#17223a')
    bars=ax.bar(labels,vals,color=['#51d3c7','#5795ef','#af91f5'],width=.55)
    for b,n in zip(bars,vals):ax.text(b.get_x()+b.get_width()/2,n+max(vals)*.01,f'{n:,}',ha='center',color='white',fontweight='bold')
    ax.set_ylim(0,max(vals)*1.16);ax.set_title('E-COMMERCE CONVERSION FUNNEL',color='white',weight='bold',fontsize=16,pad=18)
    ax.tick_params(colors='white');ax.spines[:].set_visible(False);ax.set_ylabel('Unique visitors',color='white')
    fig.tight_layout();fig.savefig(out/'overview.png',dpi=170,facecolor=fig.get_facecolor());plt.close(fig)
    insights=f'''# Product insight memo — Conversion Funnel

**Dataset:** {'Synthetic demonstration data (not actual shoppers)' if metrics['demo_data'] else source.name}

**Question:** Where does the visitor conversion journey lose the most users?

**Definition:** First product view → first subsequent add-to-cart → first subsequent purchase, tracked at visitor level. Actions may relate to different items. Full observation window; no sessionization.

## Results

- Product viewers: **{vals[0]:,}**; added to cart: **{vals[1]:,}**; purchased: **{vals[2]:,}**.
- View-to-cart conversion: **{metrics['view_to_cart_rate']:.2%}**.
- Cart-to-purchase conversion: **{metrics['cart_to_purchase_rate']:.2%}**.
- Overall view-to-purchase conversion: **{metrics['overall_conversion_rate']:.2%}**.

## Recommendation

The largest conditional-stage loss is **{biggest}**. {recommendation}

**Next experiment:** Define a specific UI hypothesis, randomly assign eligible visitors, and track purchase conversion plus guardrails such as errors and refunds.

## Limitations

Observational data do not establish causality. Visitor-level sequences can involve different products and multiple sessions. First-view cohorts near the dataset boundary have less time to convert. Do not describe synthetic demo results as real business impact.
'''
    (out/'insights.md').write_text(insights)
    print(f"Funnel: {metrics['viewers']:,} viewers → {metrics['added_to_cart']:,} carts → {metrics['purchasers']:,} purchases. Dashboard: {out/'dashboard.html'}")
    return metrics

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--data',default=None);ap.add_argument('--out',default=None)
    args=ap.parse_args();run(args.data,args.out)
