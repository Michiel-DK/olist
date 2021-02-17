import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

from stt.order import Order
from stt.data import Olist
from stt.profitability import Profitability

class Items():

    def __init__(self):
        self.order = Order().get_training_data()
        self.data = Olist().get_data()
        self.optim_df, self.to_cut = Profitability().optim_df()

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
                .rename(columns={'order_item_id':'# items ordered'})

        return top_cat_orders

    def get_top_volume(self):
        itemsproducts = self.product_cat()

        category = itemsproducts.groupby('product_category_name')\
            .agg({'volume':'sum'})

        top_cat_volume = pd.DataFrame(category['volume']\
                .sort_values(ascending=False))\
                .rename(columns={'volume':'# volume ordered',})

        return top_cat_volume


    def product_cat_cut(self):
        to_cut = self.to_cut
        itemsproducts = self.product_cat()

        itemsproducts = pd.merge(itemsproducts, to_cut, on='seller_id', how="left")
        itemsproducts['cut'] = itemsproducts['cut'].apply(lambda x: 'cut' if x == 'cut' else 'keep')

        itemprod_pivot = pd.pivot_table(itemsproducts, columns = 'cut', index = 'product_category_name', values = 'order_item_id', aggfunc = np.sum,fill_value = 0)

        itemprod_pivot['total'] = itemprod_pivot['keep'] + itemprod_pivot['cut']
        itemprod_pivot['%pcs_cut'] = itemprod_pivot['cut'] / itemprod_pivot['total']
        itemprod_pivot['50%_treshold'] = itemprod_pivot['%pcs_cut'].apply(lambda x: ">50%" if x > 0.5 else "<50%")

        top_orders = self.get_top_orders()
        top_volume = self.get_top_volume()

        cut_prod = itemprod_pivot.merge(top_orders, on='product_category_name').merge(top_volume, on='product_category_name')

        return cut_prod, itemsproducts
