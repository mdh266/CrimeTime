#!/usr/bin/env/python
from collections import Counter

from datetime import datetime
from dateutil.relativedelta import relativedelta

import sqlite3
import pandas as pd

from geopy.geocoders import Nominatim
from geopy.distance import great_circle

import geopandas as gpd 
from shapely.geometry import Point

import matplotlib
matplotlib.use('Agg')
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
import StringIO

import matplotlib.pyplot as plt
from matplotlib.collections import PatchCollection
from mpl_toolkits.basemap import Basemap
import base64

from shapely.geometry import Point, MultiPoint, MultiPolygon
from descartes import PolygonPatch

#import folium

from statsmodels.tsa.seasonal import seasonal_decompose
import sys
import os.path
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/..")

class CrimeMapper(object):
	"""
    
	"""    
	geolocator = Nominatim()
    
	def __init__(self):
		self.geo_df = gpd.read_file("./data/Police_Precincts.geojson")
        
	def find_precinct(self, address):
		## Boolean of whether the precinct of address is found
		self.prec_found = False
		## location of the address
		self.location = self.geolocator.geocode(address)
		if(self.location == None):
			return self.prec_found
		else:
			## Address of the location 
			self.address = self.location.address
	
			# Get the longitude and latitude of the address
			point =  Point(self.location.longitude, self.location.latitude)

			## Central coordinates for NYC
			self.nyc_coor = [40.7128,-74.0059]

 			# Loop through all the NYC precincts geometries and
			# find which precinct the address is in.
			N = self.geo_df.shape[0]
			for i in range(0,N):
	 			if(point.within(self.geo_df.loc[i,'geometry'])):
					## Precinct of the address
 					self.prec = int(self.geo_df.loc[i,'precinct'])
					self.prec_found = True

			return self.prec_found

	def get_crime_data(self):
		sql_query = 'SELECT * FROM Crime_Data WHERE PRECINCT = '\
								+ str(self.prec)
		conn = sqlite3.connect('./data/CrimeTime.db')
		self.df = pd.read_sql_query(sql_query, conn)
		conn.close()
        
	def restamp(self, row):
		"""
		Rewrite the date into an appropriate 
		formate for pandas time series.
		"""
		return datetime.strptime(row, '%m/%d/%Y %I:%M:%S %p').date()
    
	def make_timeseries(self, crime_name):
		""" 
		Turn the dataframe into a pandas series with daily events.
		"""
		dont_continue = False
		self.crime_name = crime_name
        
		if(crime_name == 'Larceny'):
			self.crime_df = self.df[self.df.OFFENSE == 'GRAND LARCENY']
		elif(crime_name == 'Robbery'):
			self.crime_df = self.df[self.df.OFFENSE == 'ROBBERY']
		elif(crime_name == 'Assault'):
			self.crime_df = self.df[self.df.OFFENSE == 'FELONY ASSAULT']
		elif(crime_name == 'Burglary'):
			self.crime_df = self.df[self.df.OFFENSE == 'BURGLARY']  
		else:
			dont_continue = True
			print "Cant Work With That Crime Type"
    
		if(dont_continue == False):
			aux = self.crime_df['DATE'].apply(self.restamp)
			temp = pd.Series(Counter(aux))
			self.ts = temp.to_frame()
			self.ts.reset_index(inplace=True)
			self.ts.columns = ['Date','Crimes']
			self.ts['Date'] = pd.to_datetime(self.ts['Date'])
			self.ts = self.ts.set_index('Date')
			self.ts = self.ts.resample('M').sum()
            

	def percent_per_day(self):
		"""
		"""
		CRIME_DAYS = 100 * (self.crime_df.groupby('WEEKDAY').size() 
                    /self.crime_df.groupby('WEEKDAY').size().sum())

		#print type(CRIME_DAYS)
    
		days = ['Monday','Tuesday','Wednesday',
						'Thursday','Friday','Saturday','Sunday']
    
		self.DAYS_OF_CRIME = pd.Series()
		for day in days:
			self.DAYS_OF_CRIME.loc[day] = CRIME_DAYS.loc[day]
    

        
        
	def percent_per_hour(self):
		""" 
		"""
		self.crime_df['HOUR'] = self.crime_df['HOUR'].astype(int)
		self.CRIME_HOURS =  self.crime_df.groupby('HOUR').size() #\
		self.CRIME_HOURS = 100 * (self.CRIME_HOURS
                          /self.CRIME_HOURS.sum())
    

	def get_precinct(self):
		"""
		Returns the precinct of the address searched for.
		"""
		return str(self.prec)

	def get_address(self):
		return str(self.address)
