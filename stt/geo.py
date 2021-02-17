import pandas as pd
import numpy as np

from stt.utils import haversine_distance
from stt.data import Olist
from stt.items import Items

class Geo():

    def __init__(self):
        self.sellers = Olist().get_data()['sellers']
        self.geo = Olist().get_data()['geolocation']
        self.cut_prod, self.itemsproducts = Items().product_cat_cut()

    def geo_map(self):
        geo = self.geo
        sellers = self.sellers
        itemsproducts = self.itemsproducts

        geo.rename(columns={'geolocation_zip_code_prefix':'seller_zip_code_prefix'},inplace=True)
        zipcode = geo.groupby('seller_zip_code_prefix').agg({'geolocation_lat':'mean','geolocation_lng':'mean'})
        seller_geo = sellers.merge(zipcode, on='seller_zip_code_prefix')
        items_geo = itemsproducts.merge(seller_geo, on='seller_id')
        seller_cut = items_geo[['seller_id','cut','seller_city','seller_state']].drop_duplicates()

        mp = items_geo.groupby('seller_id').agg({'order_id':'nunique','geolocation_lat':'mean','geolocation_lng':'mean'}).merge(seller_cut, on='seller_id')

        state_pivot = pd.pivot_table(mp, columns = 'cut', index = 'seller_state', values = 'seller_id', aggfunc = 'count',fill_value = 0)

        return mp, state_pivot
