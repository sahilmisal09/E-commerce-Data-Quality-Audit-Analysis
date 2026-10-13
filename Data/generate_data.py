import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import os

np.random.seed(42)
random.seed(42)

# ─── CONFIG ───────────────────────────────────────────────────────────────────
N_CUSTOMERS = 1000
N_ORDERS    = 5000
START_DATE  = datetime(2023, 1, 1)
END_DATE    = datetime(2024, 12, 31)

# ─── CUSTOMERS ────────────────────────────────────────────────────────────────
cities    = ['Mumbai','Delhi','Bangalore','Hyderabad','Chennai','Pune','Kolkata','Ahmedabad','Jaipur','Surat']
segments  = ['Premium','Regular','Budget']
genders   = ['Male','Female']

customers = pd.DataFrame({
    'customer_id'  : [f'CUST{str(i).zfill(4)}' for i in range(1, N_CUSTOMERS+1)],
    'customer_name': [f'Customer_{i}' for i in range(1, N_CUSTOMERS+1)],
    'city'         : np.random.choice(cities,    N_CUSTOMERS, p=[0.15,0.15,0.12,0.10,0.10,0.10,0.08,0.08,0.06,0.06]),
    'gender'       : np.random.choice(genders,   N_CUSTOMERS),
    'age'          : np.random.randint(18, 65,   N_CUSTOMERS),
    'segment'      : np.random.choice(segments,  N_CUSTOMERS, p=[0.20,0.55,0.25]),
    'registration_date': [START_DATE - timedelta(days=random.randint(0,730)) for _ in range(N_CUSTOMERS)],
})

# ─── PRODUCTS ─────────────────────────────────────────────────────────────────
categories = {
    'Electronics'   : ['Smartphone','Laptop','Tablet','Earphones','Smartwatch','Camera','Speaker'],
    'Fashion'       : ['T-Shirt','Jeans','Dress','Sneakers','Jacket','Kurta','Saree'],
    'Home & Kitchen': ['Mixer','Pressure Cooker','Bedsheet','Curtain','Air Purifier','LED Lamp'],
    'Beauty'        : ['Face Cream','Shampoo','Perfume','Lipstick','Sunscreen','Serum'],
    'Books'         : ['Fiction Novel','Self-Help','Biography','Textbook','Comic Book'],
    'Sports'        : ['Yoga Mat','Cricket Bat','Football','Dumbbells','Cycle Helmet'],
}

price_ranges = {
    'Electronics'   : (999,  79999),
    'Fashion'       : (299,   4999),
    'Home & Kitchen': (199,   9999),
    'Beauty'        : (99,    2999),
    'Books'         : (99,     999),
    'Sports'        : (199,   4999),
}

products_list = []
pid = 1
for cat, items in categories.items():
    for item in items:
        lo, hi = price_ranges[cat]
        products_list.append({
            'product_id'  : f'PROD{str(pid).zfill(3)}',
            'product_name': item,
            'category'    : cat,
            'price'       : round(random.uniform(lo, hi), 2),
            'cost_price'  : None,  # filled below
        })
        pid += 1

products = pd.DataFrame(products_list)
products['cost_price'] = (products['price'] * np.random.uniform(0.40, 0.65, len(products))).round(2)

# ─── ORDERS ───────────────────────────────────────────────────────────────────
date_range = (END_DATE - START_DATE).days
order_dates = [START_DATE + timedelta(days=random.randint(0, date_range)) for _ in range(N_ORDERS)]

payment_methods = ['UPI','Credit Card','Debit Card','Net Banking','COD','Wallet']
statuses        = ['Delivered','Cancelled','Returned','Processing','Shipped']
status_probs    = [0.70, 0.10, 0.08, 0.07, 0.05]

orders = pd.DataFrame({
    'order_id'      : [f'ORD{str(i).zfill(5)}' for i in range(1, N_ORDERS+1)],
    'customer_id'   : np.random.choice(customers['customer_id'], N_ORDERS),
    'order_date'    : order_dates,
    'payment_method': np.random.choice(payment_methods, N_ORDERS, p=[0.35,0.22,0.18,0.10,0.10,0.05]),
    'status'        : np.random.choice(statuses, N_ORDERS, p=status_probs),
    'shipping_city' : np.random.choice(cities, N_ORDERS),
    'discount_pct'  : np.random.choice([0,5,10,15,20,25,30], N_ORDERS, p=[0.40,0.15,0.15,0.10,0.10,0.05,0.05]),
})
orders['order_date'] = pd.to_datetime(orders['order_date'])

# ─── ORDER ITEMS ──────────────────────────────────────────────────────────────
items_list = []
for _, order in orders.iterrows():
    n_items = random.choices([1,2,3,4], weights=[50,30,15,5])[0]
    selected_products = products.sample(n_items)
    for _, prod in selected_products.iterrows():
        qty       = random.randint(1, 4)
        unit_price= prod['price']
        disc_amt  = unit_price * (order['discount_pct'] / 100)
        final_price = round((unit_price - disc_amt) * qty, 2)
        items_list.append({
            'item_id'    : f'ITEM{len(items_list)+1:06d}',
            'order_id'   : order['order_id'],
            'product_id' : prod['product_id'],
            'quantity'   : qty,
            'unit_price' : unit_price,
            'discount_amt': round(disc_amt * qty, 2),
            'total_price': final_price,
        })

order_items = pd.DataFrame(items_list)

# ─── REVIEWS ──────────────────────────────────────────────────────────────────
delivered_orders = orders[orders['status']=='Delivered']['order_id'].tolist()
review_orders    = random.sample(delivered_orders, int(len(delivered_orders)*0.65))

reviews = pd.DataFrame({
    'review_id'  : [f'REV{str(i).zfill(5)}' for i in range(1, len(review_orders)+1)],
    'order_id'   : review_orders,
    'rating'     : np.random.choice([1,2,3,4,5], len(review_orders), p=[0.05,0.08,0.15,0.35,0.37]),
    'review_date': [order_dates[0] + timedelta(days=random.randint(1,10)) for _ in review_orders],
})

# ─── SAVE ─────────────────────────────────────────────────────────────────────
out = '/home/claude/ecommerce_analytics/data'
customers.to_csv(f'{out}/customers.csv',   index=False)
products.to_csv(f'{out}/products.csv',     index=False)
orders.to_csv(f'{out}/orders.csv',         index=False)
order_items.to_csv(f'{out}/order_items.csv', index=False)
reviews.to_csv(f'{out}/reviews.csv',       index=False)

print("✅ Dataset generated!")
print(f"   Customers : {len(customers)}")
print(f"   Products  : {len(products)}")
print(f"   Orders    : {len(orders)}")
print(f"   Order Items: {len(order_items)}")
print(f"   Reviews   : {len(reviews)}")
