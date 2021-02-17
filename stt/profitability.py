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
        seller['rev_seller'] = seller['active_months']*80
        seller['rev_orders'] = seller['sales']*0.1
        return seller[['seller_id', 'rev_seller', 'rev_orders']]

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
        seller_rc['total_rev'] = seller_rc['rev_seller']+seller_rc['rev_orders']
        seller_rc['profit'] = seller_rc['total_rev'] - seller_rc['cost_reviews']
        seller_rc = seller_rc.round(2)
        #seller_rc = seller_rc.rename(columns={'rev_seller_monthly':'rev_seller','rev_orders_monthly' : 'rev_orders', 'cost reviews':'cost_reviews'})
        seller_rc['profitable'] = seller_rc['profit'].apply(lambda x: 0 if x < 0 else 1)

        return seller_rc

    def cumul_table(self):
        prof = self.merge_table()[['seller_id','n_orders','rev_seller','rev_orders','cost_reviews','profit']]
        sorted_profit = prof.sort_values('profit').reset_index()

        sorted_profit['cum_orders'] = sorted_profit['n_orders'].cumsum()
        sorted_profit['cum_rev_seller'] = sorted_profit['rev_seller'].cumsum()
        sorted_profit['cum_rev_orders'] = sorted_profit['rev_orders'].cumsum()
        sorted_profit['cum_cost_reviews'] = (sorted_profit['cost_reviews'].cumsum())*-1
        sorted_profit['cum_rev'] = sorted_profit['profit'].cumsum()
        c = 500000/np.sqrt(sorted_profit['n_orders'].sum())
        sorted_profit['cum_it_cost'] = (round(c * np.sqrt(sorted_profit["cum_orders"]),2))*-1
        sorted_profit['cum_profit'] = round(sorted_profit['cum_rev'] - sorted_profit['cum_it_cost'],2)

        return sorted_profit


    def optimisation(self):
        optim_profit = self.cumul_table().copy()

        length = len(optim_profit)
        ls = []
        i = 0
        while i < length-1:
            # get necessary results in new list
            ls.append([optim_profit['seller_id'].iloc[0],optim_profit['cum_profit'].iloc[-1]])
            # drop top row
            optim_profit = optim_profit.drop(optim_profit.index[0])
            i += 1
            # recalculate DF
            optim_profit['cum_orders'] = optim_profit['n_orders'].cumsum()
            optim_profit['cum_rev'] = round(optim_profit['profit'].cumsum(),1)
            c = 500000/np.sqrt(optim_profit['n_orders'].sum())
            optim_profit['it_cost'] = round(c * np.sqrt(optim_profit["n_orders"]),1)
            optim_profit['cum_it_cost'] = round(c * np.sqrt(optim_profit["cum_orders"]),1)
            optim_profit['prof/it'] = optim_profit['profit']/optim_profit['it_cost']
            optim_profit['cum_profit'] = round(optim_profit['cum_rev'] - optim_profit['cum_it_cost'],1)

        optim = pd.DataFrame(ls).rename(columns={0:'seller_id',1:'profit'})
        optim.reset_index(inplace=True)
        optim.rename(columns={'index':'companies to cut'},inplace=True)

        return optim, optim_profit

    def optim_df(self):
        optim, sorted_profit = self.optimisation()

        to_cut = pd.DataFrame(optim[optim.index < optim[optim['profit']==optim['profit'].max()].index[0]]['seller_id'])
        to_cut['cut'] = "cut"
        sorted_profit_cut = sorted_profit.merge(to_cut, on = 'seller_id', how = 'left')
        new_df = sorted_profit[sorted_profit_cut['cut'] != 'cut']

        return new_df

