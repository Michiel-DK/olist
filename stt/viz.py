import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import plotly.express as px

from stt.order import Order
from stt.profitability import Profitability
from stt.items import Items
from stt.geo import Geo


class Viz:

        def __init__(self):
        # Import only data once
            self.order = Order().get_training_data()
            self.profit = Profitability().merge_table()
            self.items = Items().product_cat()
            self.top_orders = Items().get_top_orders()
            self.top_volume = Items().get_top_volume()
            self.sorted_profit = Profitability().cumul_table()
            self.optim_df = Profitability().optim_df()
            self.cut_prod, self.itemsproducts = Items().product_cat_cut()
            self.geo_map = Geo().geo_map()

        def order_viz(self):
            order = self.order

            order_count = order.groupby(order['order_delivered_customer_date']\
                .dt.strftime("%y/%m")).agg({'price':'sum'})

            plt.figure(figsize=(40,20))
            sns.barplot(y='price', x = order_count.index, data=order_count)
            plt.title("Sales per month", fontsize=40)
            plt.xlabel('Delivery date', fontsize=20)
            plt.xticks(fontsize=20)
            plt.yticks(fontsize=20)
            plt.ylabel('Sales', fontsize=20)
            plt.show()

            order_count_d = order.groupby(order['order_purchase_timestamp']\
                .dt.dayofweek.map({0 : 'Monday', 1: 'Tuesday',2:'Wednesday',3:'Thursday'\
                ,4:'Friday',5:'Saturday',6:'Sunday'})).agg({'price':'sum'})

            #order_count_d = order_count_d[['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']]

            plt.figure(figsize=(40,20))
            sns.barplot(y='price', x = order_count_d.index, data=order_count_d,\
                order = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'])
            plt.title("Total sales per day", fontsize=40)
            plt.xlabel('Purchase date', fontsize=20)
            plt.xticks(fontsize=20)
            plt.yticks(fontsize=20)
            plt.ylabel('Sales', fontsize=20)
            plt.show()

        def top_category(self):
            top_cat_orders =  self.top_orders[0:14]
            top_cat_volume = self.top_volume[0:14]

            fig, (ax0, ax1) = plt.subplots(1, 2, figsize=(15,10))
            fig.suptitle('Most popular products')

            sns.barplot(y=top_cat_orders.index, x="# items ordered",
                        edgecolor=".6",
                        data=top_cat_orders, ax=ax0)
            ax0.set_ylabel('')
            ax0.set_title("Top products by items ordered")
            sns.barplot( y=top_cat_volume.index, x="# volume ordered"
                        , edgecolor=".6",
                        data=top_cat_volume, ax=ax1)
            ax1.set_title("Top products by volume ordered")
            ax1.set_ylabel('')
            plt.tight_layout()
            plt.show()

        def top_geo(self):
            prof = self.profit

            geo_state = prof.groupby('seller_state').agg({'sales':'sum'}).sort_values(by='sales',ascending=False)
            geo_city = prof.groupby('seller_city').agg({'sales':'sum'}).sort_values(by='sales',ascending=False)[0:19]

            fig, (ax0, ax1) = plt.subplots(1, 2, sharex=True, figsize=(15,10))
            fig.suptitle('Most popular areas')

            sns.barplot(y=geo_state.index,x="sales",
                        edgecolor=".6",
                        data=geo_state, ax=ax0)
            ax0.set_ylabel('')
            ax0.set_title("Sales by state")
            sns.barplot( y=geo_city.index,x="sales"
                        , edgecolor=".6",
                        data=geo_city, ax=ax1)
            ax1.set_title("Sales by city")
            ax1.set_ylabel('')
            plt.tight_layout()
            plt.show()

        def delivery_viz(self):
            order = self.order

            plt.figure(figsize=(40,20))
            sns.kdeplot(order["wait_time"] , color="skyblue", label="Actual", fill=True)
            sns.kdeplot(order["expected_wait_time"] , color="red", label="Expected", fill=True)
            plt.legend(fontsize=40)
            plt.title("Distribution expected and actual wait time", fontsize=40)
            plt.xlabel('Wait-time', fontsize=20)
            plt.xticks(fontsize=20)
            plt.yticks(fontsize=20)
            plt.ylabel('Density', fontsize=20)
            plt.show()

        def profit_viz(self):

            profit = self.profit

            profit['profitable_1'] = profit['profitable'].map({0:'Loss',1:'Profit'})
            plt.figure(figsize=(20,6))
            plt.title('Scatterplot revenue generated by suppliers')
            sns.scatterplot(data=profit, x='n_orders', y='profit', hue='profitable_1'\
                ,palette=['orange','blue'])
            plt.xlabel('# orders processed')
            plt.ylabel('revenue generated')
            plt.show()

            summary = profit.groupby('profitable')\
                .agg({'seller_id':'count','n_orders':'sum','cost_reviews':'sum','profit':'sum','review_score': 'mean','wait_time':'mean'})

            fig, ax = plt.subplots(1, 2, sharex=True, figsize=(20,10))
            fig.suptitle('Split profitable/non-profitable suppliers')
            sns.set()
            for e, i in enumerate(['seller_id','n_orders']):
                summary[i].plot(ax = ax[e], kind='pie', title=f'Split based on {i}', labels=['non-profitable','profitable'],
                      autopct=lambda p: '{:.2f}% ({:.0f})'.format(p,(p/100)*summary[i].sum()))
                ax[e].set_ylabel('')
            plt.show()

        def cumul_viz(self, optimisation='no'):

            if optimisation == 'no':
                sorted_profit = self.sorted_profit
            else:
                sorted_profit, _ = self.optim_df

            plt.figure(figsize=(40,20))
            plt.title('Cumulative revenue and costs per seller sorted from least to most profitable', fontsize=40)
            plt.bar(sorted_profit.index, sorted_profit['cum_rev_seller'], label='Revenue sellers', color='r')
            plt.bar(sorted_profit.index, sorted_profit['cum_rev_orders'], bottom=sorted_profit['cum_rev_seller'], label = 'Revenue orders', color='y')
            plt.bar(sorted_profit.index, sorted_profit['cum_it_cost'], label='IT cost')
            plt.bar(sorted_profit.index, sorted_profit['cum_cost_reviews'], bottom=sorted_profit['cum_it_cost'], label = 'Review cost')
            plt.plot(sorted_profit['cum_profit'], color='black',linewidth=7.0 , linestyle='--', label = 'Profit')
            plt.xlabel('Sellers', fontsize=20)
            plt.xticks(fontsize=20)
            plt.yticks(fontsize=20)
            plt.ylabel('100k BRL', fontsize=20)
            plt.grid(b=True, which='major', color='#666666', linestyle='-')
            plt.minorticks_on()
            plt.grid(b=True, which='minor', color='#999999', linestyle='-', alpha=0.2)
            plt.legend(fontsize=20)
            plt.ylim([-3000000,3000000])
            plt.show()

        def cut_products(self):
            cut_prod = self.cut_prod

            plt.figure(figsize=(20,30))
            plt.title('Product categories sorted by orders cut due to optimisation', fontsize=20)
            sns.barplot(data = cut_prod.sort_values(by='%pcs_cut', ascending=False), x = '%pcs_cut', y = cut_prod.index, hue='50%_treshold')
            plt.ylabel('')
            plt.show()

            plt.figure(figsize=(20,30))
            plt.title('Product categories sorted by orders cut due to optimisation', fontsize=20)
            sns.relplot(x="%pcs_cut", y=cut_prod.index, hue="50%_treshold", size="# items ordered",
            sizes=(40, 400), alpha=.5, palette="muted",
            height=12, data=cut_prod.sort_values(by=["50%_treshold",'# items ordered'], ascending=False))
            plt.ylabel('')
            plt.show()

        def geo(self):
            mp, state_pivot = self.geo_map

            plt.figure(figsize=(20,6))
            plt.title("Sellers to keep/cut per state")
            plt.bar(state_pivot.index, state_pivot['keep'], label='Sellers to keep', color='g')
            plt.bar(state_pivot.index, state_pivot['cut'], bottom=state_pivot['keep'], label='Sellers to cut', color='r')
            plt.legend(fontsize=15)
            plt.show()

            fig = px.scatter_geo(mp[mp['cut']!='cut'], lat="geolocation_lat", lon="geolocation_lng",
                    size="order_id", title="Spread sellers to keep",
                     scope = 'south america',
                     opacity = 0.5,
                     center = {'lat':-19.8, 'lon':-43})
            fig.update_geos(fitbounds="locations")
            fig.show()

            fig = px.scatter_geo(mp[mp['cut']=='cut'], lat="geolocation_lat", lon="geolocation_lng",
                    size="order_id", title="Spread sellers to cut",
                     scope = 'south america',
                     opacity = 0.5,
                     center = {'lat':-19.8, 'lon':-43})
            fig.update_geos(fitbounds="locations")
            fig.show()
