"""
E-Commerce Analytics — Exploratory Data Analysis
Author  : Abhay Yadav
Tools   : Python, Pandas, Matplotlib, Seaborn
Dataset : Synthetic Indian E-commerce Data (2023-2024)
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.patches as mpatches
from matplotlib.ticker import FuncFormatter
import seaborn as sns
import sqlite3
import warnings
import os

warnings.filterwarnings('ignore')

# ─── THEME ────────────────────────────────────────────────────────────────────
BG      = '#0D1117'
PANEL   = '#161B22'
BORDER  = '#30363D'
TEXT    = '#E6EDF3'
MUTED   = '#8B949E'
ACCENT  = ['#58A6FF','#3FB950','#FF7B72','#D2A8FF','#FFA657','#79C0FF','#56D364']
plt.rcParams.update({
    'figure.facecolor' : BG,
    'axes.facecolor'   : PANEL,
    'axes.edgecolor'   : BORDER,
    'axes.labelcolor'  : TEXT,
    'text.color'       : TEXT,
    'xtick.color'      : MUTED,
    'ytick.color'      : MUTED,
    'grid.color'       : BORDER,
    'grid.alpha'       : 0.5,
    'font.family'      : 'DejaVu Sans',
})

def fmt_inr(x, _): return f'₹{x/1e5:.1f}L' if x >= 1e5 else f'₹{x:,.0f}'

# ─── LOAD DATA ────────────────────────────────────────────────────────────────
BASE = '/home/claude/ecommerce_analytics/data'
customers  = pd.read_csv(f'{BASE}/customers.csv',   parse_dates=['registration_date'])
products   = pd.read_csv(f'{BASE}/products.csv')
orders     = pd.read_csv(f'{BASE}/orders.csv',      parse_dates=['order_date'])
order_items= pd.read_csv(f'{BASE}/order_items.csv')
reviews    = pd.read_csv(f'{BASE}/reviews.csv',     parse_dates=['review_date'])

# ─── PREP ─────────────────────────────────────────────────────────────────────
delivered  = orders[orders['status']=='Delivered'].copy()
oi_full    = order_items.merge(products[['product_id','product_name','category','cost_price']], on='product_id')
oi_del     = oi_full.merge(delivered[['order_id','order_date','payment_method','discount_pct','shipping_city','customer_id']], on='order_id')

oi_del['year_month'] = oi_del['order_date'].dt.to_period('M')
oi_del['year']       = oi_del['order_date'].dt.year
oi_del['month_name'] = oi_del['order_date'].dt.strftime('%b')
oi_del['profit']     = oi_del['total_price'] - (oi_del['cost_price'] * oi_del['quantity'])

# ─── DASHBOARD 1: SALES OVERVIEW (3×3) ────────────────────────────────────────
fig = plt.figure(figsize=(22, 18))
fig.patch.set_facecolor(BG)
gs  = gridspec.GridSpec(3, 3, figure=fig, hspace=0.45, wspace=0.35)

# -- KPI Cards (top row) -------
kpis = [
    ('Total Revenue',    f"₹{oi_del['total_price'].sum()/1e7:.2f} Cr", ACCENT[0]),
    ('Total Orders',     f"{delivered['order_id'].nunique():,}",         ACCENT[1]),
    ('Avg Order Value',  f"₹{oi_del.groupby('order_id')['total_price'].sum().mean():,.0f}", ACCENT[2]),
]
for col, (label, val, color) in enumerate(kpis):
    ax = fig.add_subplot(gs[0, col])
    ax.set_facecolor(PANEL)
    for sp in ax.spines.values(): sp.set_color(color); sp.set_linewidth(2)
    ax.text(0.5, 0.62, val,   transform=ax.transAxes, ha='center', va='center',
            fontsize=28, fontweight='bold', color=color)
    ax.text(0.5, 0.25, label, transform=ax.transAxes, ha='center', va='center',
            fontsize=13, color=MUTED)
    ax.set_xticks([]); ax.set_yticks([])

# -- Monthly Revenue Trend -----
ax1 = fig.add_subplot(gs[1, :2])
monthly = oi_del.groupby('year_month')['total_price'].sum().reset_index()
monthly['ym_str'] = monthly['year_month'].astype(str)
x = range(len(monthly))
ax1.fill_between(x, monthly['total_price'], alpha=0.15, color=ACCENT[0])
ax1.plot(x, monthly['total_price'], color=ACCENT[0], lw=2.5, marker='o', ms=5)
ax1.set_xticks(x[::2])
ax1.set_xticklabels(monthly['ym_str'].iloc[::2], rotation=30, ha='right', fontsize=8)
ax1.yaxis.set_major_formatter(FuncFormatter(fmt_inr))
ax1.set_title('Monthly Revenue Trend (2023–2024)', color=TEXT, fontsize=12, pad=10)
ax1.grid(True, axis='y')

# -- Category Revenue Pie ------
ax2 = fig.add_subplot(gs[1, 2])
cat_rev = oi_del.groupby('category')['total_price'].sum().sort_values(ascending=False)
wedges, texts, autotexts = ax2.pie(
    cat_rev, labels=None, autopct='%1.1f%%', startangle=140,
    colors=ACCENT, pctdistance=0.78,
    wedgeprops=dict(edgecolor=BG, linewidth=2))
for at in autotexts: at.set_fontsize(8); at.set_color(BG)
ax2.legend(cat_rev.index, loc='lower left', fontsize=7,
           facecolor=PANEL, edgecolor=BORDER, labelcolor=TEXT)
ax2.set_title('Revenue by Category', color=TEXT, fontsize=12, pad=10)

# -- Top 10 Products -----------
ax3 = fig.add_subplot(gs[2, :2])
top_prod = oi_del.groupby('product_name')['total_price'].sum().nlargest(10).sort_values()
bars = ax3.barh(top_prod.index, top_prod.values, color=ACCENT[0], alpha=0.85, height=0.6)
for bar in bars:
    ax3.text(bar.get_width()*1.01, bar.get_y()+bar.get_height()/2,
             fmt_inr(bar.get_width(), None), va='center', fontsize=8, color=MUTED)
ax3.set_xlabel('Revenue', color=MUTED, fontsize=9)
ax3.set_title('Top 10 Products by Revenue', color=TEXT, fontsize=12, pad=10)
ax3.xaxis.set_major_formatter(FuncFormatter(fmt_inr))
ax3.grid(True, axis='x')

# -- Order Status Donut --------
ax4 = fig.add_subplot(gs[2, 2])
status_cnt = orders['status'].value_counts()
wedges, _, autos = ax4.pie(
    status_cnt, labels=None, autopct='%1.1f%%', startangle=90,
    colors=ACCENT[:len(status_cnt)], pctdistance=0.82,
    wedgeprops=dict(width=0.45, edgecolor=BG, linewidth=2))
for at in autos: at.set_fontsize(8); at.set_color(BG)
ax4.legend(status_cnt.index, loc='lower left', fontsize=7,
           facecolor=PANEL, edgecolor=BORDER, labelcolor=TEXT)
ax4.set_title('Order Status Distribution', color=TEXT, fontsize=12, pad=10)

# Title
fig.text(0.5, 0.97, '🛒  E-Commerce Analytics — Sales Overview Dashboard',
         ha='center', va='top', fontsize=18, fontweight='bold', color=TEXT)
fig.text(0.5, 0.945, 'India | 2023–2024 | 5,000 Orders Analysed',
         ha='center', va='top', fontsize=11, color=MUTED)

plt.savefig('/home/claude/ecommerce_analytics/python/dashboard_1_sales_overview.png',
            dpi=150, bbox_inches='tight', facecolor=BG)
plt.close()
print("✅ Dashboard 1 saved")

# ─── DASHBOARD 2: CUSTOMER & PAYMENT ANALYSIS (3×3) ──────────────────────────
fig2 = plt.figure(figsize=(22, 18))
fig2.patch.set_facecolor(BG)
gs2  = gridspec.GridSpec(3, 3, figure=fig2, hspace=0.45, wspace=0.35)

# -- Customer Segment Revenue --
ax5 = fig2.add_subplot(gs2[0, :2])
cust_seg = (oi_del.merge(customers[['customer_id','segment']], on='customer_id')
                  .groupby('segment')['total_price'].sum().sort_values(ascending=False))
colors_seg = [ACCENT[0], ACCENT[1], ACCENT[2]]
b = ax5.bar(cust_seg.index, cust_seg.values, color=colors_seg[:len(cust_seg)],
            width=0.5, edgecolor=BG, linewidth=1.5)
for bar in b:
    ax5.text(bar.get_x()+bar.get_width()/2, bar.get_height()*1.02,
             fmt_inr(bar.get_height(), None), ha='center', fontsize=10, color=TEXT)
ax5.yaxis.set_major_formatter(FuncFormatter(fmt_inr))
ax5.set_title('Revenue by Customer Segment', color=TEXT, fontsize=12, pad=10)
ax5.grid(True, axis='y')

# -- Age Distribution ----------
ax6 = fig2.add_subplot(gs2[0, 2])
cust_merged = customers.merge(
    oi_del.groupby('customer_id')['total_price'].sum().reset_index(), on='customer_id', how='left')
cust_merged['age_group'] = pd.cut(cust_merged['age'],
    bins=[17,25,35,45,55,65], labels=['18-25','26-35','36-45','46-55','56-65'])
ag_rev = cust_merged.groupby('age_group', observed=True)['total_price'].sum()
ax6.bar(ag_rev.index.astype(str), ag_rev.values, color=ACCENT[3], width=0.55)
ax6.yaxis.set_major_formatter(FuncFormatter(fmt_inr))
ax6.set_title('Revenue by Age Group', color=TEXT, fontsize=12, pad=10)
ax6.grid(True, axis='y')

# -- City Performance ----------
ax7 = fig2.add_subplot(gs2[1, :])
city_rev = oi_del.groupby('shipping_city')['total_price'].sum().sort_values(ascending=False)
bars7 = ax7.bar(city_rev.index, city_rev.values,
                color=[ACCENT[i % len(ACCENT)] for i in range(len(city_rev))],
                width=0.55, edgecolor=BG)
for bar in bars7:
    ax7.text(bar.get_x()+bar.get_width()/2, bar.get_height()*1.01,
             fmt_inr(bar.get_height(), None), ha='center', fontsize=9, color=MUTED)
ax7.yaxis.set_major_formatter(FuncFormatter(fmt_inr))
ax7.set_title('City-wise Revenue', color=TEXT, fontsize=12, pad=10)
ax7.grid(True, axis='y')

# -- Payment Method ------------
ax8 = fig2.add_subplot(gs2[2, 0])
pay = orders['payment_method'].value_counts()
ax8.barh(pay.index, pay.values, color=ACCENT[:len(pay)], height=0.6)
ax8.set_title('Orders by Payment Method', color=TEXT, fontsize=11, pad=10)
ax8.grid(True, axis='x')
for i,(v,name) in enumerate(zip(pay.values, pay.index)):
    ax8.text(v+30, i, str(v), va='center', fontsize=9, color=MUTED)

# -- Rating Distribution -------
ax9 = fig2.add_subplot(gs2[2, 1])
rating_cnt = reviews['rating'].value_counts().sort_index()
colors_r = ['#FF7B72','#FFA657','#FFA657','#3FB950','#3FB950']
ax9.bar(rating_cnt.index, rating_cnt.values, color=colors_r, width=0.55)
ax9.set_xlabel('Rating (Stars)', color=MUTED, fontsize=9)
ax9.set_title('Review Rating Distribution', color=TEXT, fontsize=11, pad=10)
ax9.grid(True, axis='y')
for x_val, y_val in zip(rating_cnt.index, rating_cnt.values):
    ax9.text(x_val, y_val+5, str(y_val), ha='center', fontsize=9, color=MUTED)

# -- Discount vs AOV -----------
ax10 = fig2.add_subplot(gs2[2, 2])
disc_aov = oi_del.groupby('discount_pct').agg(
    aov=('total_price','mean'), orders=('order_id','count')).reset_index()
sc = ax10.scatter(disc_aov['discount_pct'], disc_aov['aov'],
                  s=disc_aov['orders']/3, c=ACCENT[4], alpha=0.8, edgecolors=BG)
ax10.yaxis.set_major_formatter(FuncFormatter(fmt_inr))
ax10.set_xlabel('Discount %', color=MUTED, fontsize=9)
ax10.set_title('Discount % vs Avg Order Value\n(bubble = order count)',
               color=TEXT, fontsize=10, pad=8)
ax10.grid(True)

fig2.text(0.5, 0.97, '👥  E-Commerce Analytics — Customer & Payment Insights',
          ha='center', va='top', fontsize=18, fontweight='bold', color=TEXT)
fig2.text(0.5, 0.945, 'India | 2023–2024 | 1,000 Customers',
          ha='center', va='top', fontsize=11, color=MUTED)

plt.savefig('/home/claude/ecommerce_analytics/python/dashboard_2_customer_insights.png',
            dpi=150, bbox_inches='tight', facecolor=BG)
plt.close()
print("✅ Dashboard 2 saved")

# ─── POWER BI EXPORT ──────────────────────────────────────────────────────────
# Flat fact table for Power BI import
powerbi_fact = (
    oi_del
    .merge(customers[['customer_id','city','segment','age','gender']]
           .rename(columns={'city':'customer_city'}), on='customer_id', how='left')
    .assign(
        profit_margin=lambda d: ((d['profit'] / d['total_price'].replace(0,np.nan)) * 100).round(2),
        order_month=lambda d: d['order_date'].dt.strftime('%Y-%m'),
        order_quarter=lambda d: d['order_date'].dt.to_period('Q').astype(str),
    )
)

powerbi_cols = [
    'order_id','order_date','order_month','order_quarter',
    'customer_id','customer_city','segment','age','gender',
    'product_id','product_name','category',
    'quantity','unit_price','discount_amt','total_price',
    'cost_price','profit','profit_margin',
    'payment_method','shipping_city','discount_pct'
]
powerbi_fact[powerbi_cols].to_csv(
    '/home/claude/ecommerce_analytics/powerbi_export/ecommerce_fact_table.csv', index=False)

# Dim tables
customers.to_csv('/home/claude/ecommerce_analytics/powerbi_export/dim_customers.csv', index=False)
products.to_csv('/home/claude/ecommerce_analytics/powerbi_export/dim_products.csv',   index=False)

print("✅ Power BI export files saved")

# ─── SUMMARY STATS ────────────────────────────────────────────────────────────
print("\n" + "="*55)
print("  E-COMMERCE ANALYTICS — KEY INSIGHTS")
print("="*55)
print(f"  💰 Total Revenue    : ₹{oi_del['total_price'].sum()/1e7:.2f} Crore")
print(f"  📦 Total Orders     : {delivered['order_id'].nunique():,}")
print(f"  👥 Unique Customers : {oi_del['customer_id'].nunique():,}")
print(f"  🏆 Best Category    : {oi_del.groupby('category')['total_price'].sum().idxmax()}")
print(f"  🌆 Top City         : {oi_del.groupby('shipping_city')['total_price'].sum().idxmax()}")
print(f"  💳 Top Payment      : {orders['payment_method'].value_counts().index[0]}")
print(f"  ⭐ Avg Rating       : {reviews['rating'].mean():.2f} / 5.0")
print(f"  🎯 Delivery Rate    : {(orders['status']=='Delivered').mean()*100:.1f}%")
print("="*55)
print("  📊 All files ready in ecommerce_analytics/")
