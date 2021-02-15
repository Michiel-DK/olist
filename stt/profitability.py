import os
import pandas as pd
import numpy as np
import datetime

from stt.data import Olist
from stt.order import Order
from stt.seller import Seller

class Profitability():

    """
    Add revenue and costs to seller data based on orders and assumptions
    """

    def __init__(self):
        self.data = Olist().get_data()
        self.seller = Seller().get_training_data()
        self.order = Order().get_training_data()
        self.order_id_seller_id = Olist().get_data()['order_items'][['order_id','seller_id']]

    def prep_seller(self):
        seller = self.seller
        seller['date_first_sale'] = pd.to_datetime(seller['date_first_sale'].map(lambda x: x.strftime("%Y-%m-%d")))
        seller['date_last_sale'] = pd.to_datetime(seller['date_last_sale'])
        seller['date_last_sale']=seller['date_last_sale'].map(lambda x: x.strftime("%Y-%m-%d"))
        seller['date_last_sale'] = pd.to_datetime(seller['date_last_sale'])
        seller['active_months'] = round((seller['date_last_sale']-seller['date_first_sale'])/datetime.timedelta(days=1)/30,0)
        seller['active_months'] = seller['active_months'].apply(lambda x: 1 if x == 0 else x)

        return seller

    def revenue(self):
        """
        Revenue made through 80 BRL per month active, 10% of sales
        """
        seller = self.prep_seller()
        seller['rev_seller_monthly'] = seller['active_months']*80
        seller['rev_orders_monthly'] = seller['sales']*0.1
        return seller[['seller_id', 'rev_seller_monthly', 'rev_orders_monthly']]

    def review_cost(self):
        """
        Sellers fined for 1/2/3 star reviews at fixed rate
        """
        orders = self.order
        matching = self.order_id_seller_id

        order_sel = orders.merge(matching, on='order_id')

        def dim_two_star(d):
            if d == 2:
                return 1
            else:
                return 0

        def dim_three_star(d):
            if d == 3:
                 return 1
            else:
                return 0

        order_sel['dim_is_two_star'] = order_sel['review_score'].apply(dim_two_star)
        order_sel['dim_is_three_star'] = order_sel['review_score'].apply(dim_three_star)

        seller_small = order_sel.groupby('seller_id').agg('sum')[['dim_is_one_star','dim_is_two_star','dim_is_three_star']]

        seller_small['dim_is_one_star'] = seller_small['dim_is_one_star']*100
        seller_small['dim_is_two_star'] = seller_small['dim_is_two_star']*50
        seller_small['dim_is_three_star'] = seller_small['dim_is_three_star']*40
        seller_small['sum'] = seller_small.sum(axis=1)
        seller_cost = seller_small[['sum']].rename(columns={'sum':'cost_reviews'})

        return seller_cost

    def merge_table(self):
            seller_rc = self.prep_seller()\
            .merge(self.review_cost(), on='seller_id')\
            .merge(self.revenue(), on='seller_id')
            seller_rc['total_rev'] = seller_rc['rev_seller_monthly']+seller_rc['rev_orders_monthly']
            seller_rc['profit'] = seller_rc['total_rev'] - seller_rc['cost_reviews']
            seller_rc = seller_rc.round(2)
            seller_rc = seller_rc.rename(columns={'rev_seller_monthly':'rev_seller','rev_orders_monthly' : 'rev_orders', 'cost reviews':'cost_reviews'})
            seller_rc['profitable'] = seller_rc['profit'].apply(lambda x: 0 if x < 0 else 1)

            return seller_rc
