import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

from stt.order import Order
from stt.data import Olist

class Items():

    def __init__(self):
        self.order = Order().get_training_data()
        self.data = Olist().get_data()

    def product_cat(self):
        data = self.data
        orderitems = data['order_items']
        products = data['products']

        itemsproducts = products.merge(orderitems, on='product_id')
        itemsproducts['volume'] = itemsproducts['product_length_cm']/100*itemsproducts['product_height_cm']/100*itemsproducts['product_width_cm']/100
        itemsproducts['volume_per_item'] = itemsproducts['volume'] * itemsproducts['order_item_id']
        itemsproducts['price_per_item'] = round(itemsproducts['price'] / itemsproducts['order_item_id'],0)

        return itemsproducts

    def get_top_orders(self):
        itemsproducts = self.product_cat()

        category = itemsproducts.groupby('product_category_name')\
                .agg({'order_item_id':'sum'})

        top_cat_orders = pd.DataFrame(category['order_item_id']\
                .sort_values(ascending=False))\
                .rename(columns={'order_item_id':'# items ordered'})[0:14]

        return top_cat_orders

    def get_top_volume(self):
        itemsproducts = self.product_cat()

        category = itemsproducts.groupby('product_category_name')\
            .agg({'volume':'sum'})

        top_cat_volume = pd.DataFrame(category['volume']\
                .sort_values(ascending=False))\
                .rename(columns={'volume':'# volume ordered'})[0:14]

        return top_cat_volume
