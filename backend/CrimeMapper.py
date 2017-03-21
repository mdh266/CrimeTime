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

from shapely.geometry import Point, MultiPoint, MultiPolygon
from descartes import PolygonPatch
import matplotlib.pyplot as plt


from statsmodels.tsa.seasonal import seasonal_decompose
import sys
import os.path
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/..")
import warnings
warnings.filterwarnings('ignore')

class CrimeMapper:
	"""
	This is the main class for CrimeTime. It will deal with all the backend
	data management and interacting with the SQLite database.

	It will be used by :class:`backend.Forecasting.Seasonal_ARIMA` class.


	:attributes:
	------------

		**production_mode** (boolean):
			Boolean to describe if code is running in production mode. Will be
			used for describing where database is.

		**geo_df** (`GeoPandas DataFrame <http://geopandas.org/data_structures.html#geodataframe>`_):
			The GeoPandas DataFrame of the geojson file, to plot the NYPD Precincts.

		**prec_found** (boolean):
			Boolean to record if the police precinct of the user entered address has been found.
		
		**location** (dict):
			Dictionary returned by `geopy <https://pypi.python.org/pypi/geopy/1.11.0>`_
			of the address, lattitude and longitude.

		**address** (str): 
			Address returned by `geopy <https://pypi.python.org/pypi/geopy/1.11.0>`_ .

		**prec** (int):
			Police precinct of the address.
		
		**crime_name** (str):
			The name of the crime, i.e., 'Larceny', 'Assault', etc.

		**crime_df** (`Pandas DataFrame <http://pandas.pydata.org/pandas-docs/stable/generated/pandas.DataFrame.html>`_):
			The Pandas DataFrame for the selected 'crime_name' history of the selected police precinct.

		**ts** (`Pandas DataFrame <http://pandas.pydata.org/pandas-docs/stable/generated/pandas.DataFrame.html>`_):
			The Pandas DataFrame that will act as our monthly time series data for our 
			precinct and selected crime.

		**sql_query** (str): 
			The SQL query that will depend on the crime type and police precinct.

		**DAYS_OF_CRIME** (`Pandas DataFrame <http://pandas.pydata.org/pandas-docs/stable/generated/pandas.DataFrame.html>`_):
			Pandas Series which contain the day of week and the percentage of crimes that occured on each day.

		**TIME_OF_DAY** (`Pandas DataFrame <http://pandas.pydata.org/pandas-docs/stable/generated/pandas.DataFrame.html>`_):
			Pandas Series which contain the hours of the day and the percentage of crimes that occured at each hour.

		**assault_ ts** (`Pandas DataFrame <http://pandas.pydata.org/pandas-docs/stable/generated/pandas.DataFrame.html>`_):
			The Pandas DataFrame that will have the monlthy trends in the assault.

		**burglary ts** (`Pandas DataFrame <http://pandas.pydata.org/pandas-docs/stable/generated/pandas.DataFrame.html>`_):
			The Pandas DataFrame that will have the monlthy trends in the burglary.

		**larceny ts** (`Pandas DataFrame <http://pandas.pydata.org/pandas-docs/stable/generated/pandas.DataFrame.html>`_):
			The Pandas DataFrame that will have the monlthy trends in the larceny.

		**car_ts** (`Pandas DataFrame <http://pandas.pydata.org/pandas-docs/stable/generated/pandas.DataFrame.html>`_):
			The Pandas DataFrame that will have the monlthy trends in the car theft.

		**robbery_ts** (`Pandas DataFrame <http://pandas.pydata.org/pandas-docs/stable/generated/pandas.DataFrame.html>`_):
			The Pandas DataFrame that will have the monlthy trends in the robbery.
	:methods:
	"""    
    
	def __init__(self, production_mode):
		"""
		Constructor just makes a GeoPandas <http://geopandas.org/data_structures.html#geodataframe>`_)
		based off the police precincts in the /data/ directory.

		:Parameters: production_mode (boolean):
			Boolean to describe if code is running in production mode. Will be
			used for describing where database is.

		"""
		## Boolean to know to run in production mode, changes location of database
		self.production_mode = production_mode

		## Geolocator object
		self._geolocator = Nominatim()
	
		## Police precinct geopandas dataframe
		self.geo_df = None

		if self.production_mode == True:
			self.geo_df = gpd.read_file("./data/NYC_Police_Precincts.geojson")
		else:
			self.geo_df = gpd.read_file("../data/NYC_Police_Precincts.geojson")
		
		## boolean as to whether the precinct was found in the find_precinct call
		self.prec_found    = None

		## The location dictionary returned by geopy
		self.location      = None

		## Address of the location from geopy
		self.address       = None 

		## Precinct of the address
		self.prec		   = None
		
		## The name crime the user input
		self.crime_name    = None

		## Dataframe which contains all the crime data for precinct and type of crime
		self.crime_df	   = None

		## Dataframe monthly crime data
		self.ts			   = None

		## Dataframe that has all days in the week and the crimes occurring each day
		self.DAYS_OF_CRIME = None

		## Dataframe that has all the hours in the day and the crimes occurring each hour
		self.CRIME_HOURS   = None

		## sql_query to 
		self.sql_query	   = None

		#
		self.assault_ts    = None

		self.larceny_ts    = None

		self.robbery_ts    = None

		self.burglary_ts   = None

		self.car_ts        = None


	def find_precinct(self, address):
		""" 
		Takes in address and finds the police precint the address belongs to.

		:Parameters: address (str): 
			The address contianing number, street and borough.

		:returns: 
			Boolean of whether the police precinct of address is found.

		:rtype: 
			Boolean.
		"""

		## Boolean of whether the precinct of address is found	
		self.prec_found = False
		## location of the address
		try:
			self.location = self._geolocator.geocode(address)
		except:
			pass
		
		if(self.location == None):
			return self.prec_found
		else:
			self.address = self.location.address
	
			# Get the longitude and latitude of the address
			point =  Point(self.location.longitude, self.location.latitude)

			# Central coordinates for NYC
			self.nyc_coor = [40.7128,-74.0059]

 			# Loop through all the NYC precincts geometries and
			# find which precinct the address is in.
			N = self.geo_df.shape[0]
			for i in range(0,N):
	 			if(point.within(self.geo_df.loc[i,'geometry'])):
 					self.prec = int(self.geo_df.loc[i,'precinct'])
					self.prec_found = True

			if self.production_mode:
				return self.prec_found
	

	def get_all_crime_data(self):
		"""
		Get all the crime data for this police precinct (excluding rape 
		and murder) by querying the SQLite database.

		**NOTE:** find_precinct() must have been called first.
		"""

		self.sql_query = 'SELECT * FROM NYC_CRIME WHERE PRECINCT = '\
				+ str(self.prec) + ' AND OFFENSE != \'RAPE\''\
				+ 'AND OFFENSE != \'MURDER & NON-NEGL. MANSLAUGHTER\''

		if self.production_mode == True:
			conn = sqlite3.connect('./data/CrimeTime.db')
		else:
			conn = sqlite3.connect('../data/CrimeTime.db')

		# The crime dataframe for the selected police precint.
		df = pd.read_sql_query(self.sql_query, conn)
		conn.close()

		# Make the trend time series for all the different crimes
		self.crime_df = df[df.OFFENSE == 'FELONY ASSAULT'] 
		self.make_time_series()
		self.assault_ts = seasonal_decompose(self.ts,freq=12).trend
		self.assault_ts.dropna(inplace=True)

		self.crime_df = df[df.OFFENSE == 'ROBBERY'] 
		self.make_time_series()
		self.robbery_ts  = seasonal_decompose(self.ts,freq=12).trend
		self.robbery_ts.dropna(inplace=True)

		self.crime_df = df[df.OFFENSE == 'GRAND LARCENY'] 
		self.make_time_series()
		self.larceny_ts  = seasonal_decompose(self.ts,freq=12).trend
		self.larceny_ts.dropna(inplace=True)

		self.crime_df = df[df.OFFENSE == 'BURGLARY'] 
		self.make_time_series()
		self.burglary_ts  = seasonal_decompose(self.ts,freq=12).trend
		self.burglary_ts.dropna(inplace=True)

		self.crime_df = df[df.OFFENSE == 'GRAND LARCENY OF MOTOR VEHICLE'] 
		self.make_time_series()
		self.car_ts  = seasonal_decompose(self.ts,freq=12).trend
		self.car_ts.dropna(inplace=True)

	def get_crime_data(self, crime_name):
		"""
		Gets the crime data for the user supplied crime in the users 
		police precinct from the SQLite database.

		**NOTE:** find_precinct() must have been called first.

		:Parameters: crime_name (str): 
			The user selected crime. Accepts:

			* 'Larceny'
			* 'Robbery'
			* 'Assault' 
			* 'Burglary'
			* 'Car Theft'
		"""
		self.crime_name = crime_name
		dont_continue = False

		if(crime_name == 'Larceny'):
			self.crime_name = 'GRAND LARCENY'
		elif(crime_name == 'Robbery'):
			self.crime_name = 'ROBBERY'
		elif(crime_name == 'Assault'):
			self.crime_name = 'FELONY ASSAULT'
		elif(crime_name == 'Burglary'):
			self.crime_name = 'BURGLARY'
		elif(crime_name == 'Car Theft'):
			self.crime_name = 'GRAND LARCENY OF MOTOR VEHICLE'
		else:
			dont_continue = True
			print "Cant Work With That Crime Type"

		if(dont_continue == False):
			self.sql_query = 'SELECT * FROM NYC_CRIME WHERE PRECINCT = '\
					+ str(self.prec) + ' AND OFFENSE = \'' \
					+ str(self.crime_name) + '\' ' 

			if self.production_mode == True:
				conn = sqlite3.connect('./data/CrimeTime.db')
			else:
				conn = sqlite3.connect('../data/CrimeTime.db')

			# The crime dataframe for the selected police precint.
			self.crime_df = pd.read_sql_query(self.sql_query, conn)
			conn.close()
        
	def restamp(self, row):
		"""
		Rewrite the date into an appropriate formate for pandas time series.
		
		:Parameters: row (str):
			The string that contains the stamp, e.g.: '01/31/2006 12:00:00 AM'
	
		:returns: (str)
			The datetime.date version of the date, e.g. '01-31-2006'
		
		:rtype: str

		"""
		return datetime.strptime(row, '%m/%d/%Y %I:%M:%S %p').date()
    
	def make_time_series(self):
		""" 
		Rewrites the self.crime_df into self.ts where the crimes have been resampled
		for each month.
		"""
		aux = self.crime_df['DATE'].apply(self.restamp)
		temp = pd.Series(Counter(aux))
		## The pandas time series of the monthly number of specified crimes in precinct
		self.ts = temp.to_frame()
		self.ts.reset_index(inplace=True)
		self.ts.columns = ['Date','Crimes']
		self.ts['Date'] = pd.to_datetime(self.ts['Date'])
		self.ts = self.ts.set_index('Date')
		self.ts = self.ts.resample('M').sum()
		if(self.ts.isnull().values.any()):
			self.ts.dropna(inplace=True)           

	def percent_per_day(self):
		"""
		Makes a Pandas DataFrame for the number of crimes that occurred in 
		the selected precinct on each day of the week.
		"""
		CRIME_DAYS = 100 * (self.crime_df.groupby('WEEKDAY').size() 
                    /self.crime_df.groupby('WEEKDAY').size().sum())

		#print type(CRIME_DAYS)
    
		days = ['Monday','Tuesday','Wednesday',
						'Thursday','Friday','Saturday','Sunday']
    
		## Time series of the number of crimes that occurred in the day of week
		self.DAYS_OF_CRIME = pd.Series()
		for day in days:
			self.DAYS_OF_CRIME.loc[day] = CRIME_DAYS.loc[day]
    
        
	def percent_per_hour(self):
		""" 
		Makes a Pandas DataFrame for the number of crimes that occurred in 
		the selected precinct on hour of the day.
		"""
		self.crime_df['HOUR'] = self.crime_df['HOUR'].astype(int)
		self.CRIME_HOURS =  self.crime_df.groupby('HOUR').size() #\
		self.CRIME_HOURS = 100 * (self.CRIME_HOURS
                          /self.CRIME_HOURS.sum())

	def get_precinct(self):
		"""
		Returns the precinct of the address that was searched for.
		
		:returns: prec
		:rtype: int
		"""
		return str(self.prec)

	def get_address(self):
		"""
		Returns the address that was searched for.
		
		:returns: address
		:rtype: str
		"""
		return str(self.address)

	def get_precinct_info(self):
		"""
		This function will query the SQLite databse to obtain
		the police precinct info for users precinct.

		:returns: precinct's name, address and telephone number.
		:rtype: dict
		"""
		sql_query = 'SELECT * FROM NYC_CRIME WHERE Precinct = '\
				+ str(self.prec)

		if self.production_mode == True:		
			conn = sqlite3.connect('./data/CrimeTime.db')
		else:
			conn = sqlite3.connect('../data/CrimeTime.db')

		df = pd.read_sql_query(sql_query, conn)
		conn.close()
	
		precinct_info = {}

		precinct_info['name'] = str(df['Name'][0])
		precinct_info['address'] = str(df['Address'][0])
		precinct_info['tele'] = str(df['Telephone'][0])

		return precinct_info

	def plot_decompose(self):
		"""
		This plots the raw monthly number of crimes, as well as the trend and seasonality
		of crime in the precinct.  Under the hood it is calling StatsModels'
		`seasonal_decompose(...) <http://www.statsmodels.org/dev/generated/statsmodels.tsa.seasonal.seasonal_decompose.html>`_
		"""
		fig = plt.figure(figsize=(9, 5))
		plt.clf()

		decomp_crime = seasonal_decompose(self.ts,freq=12)
		season_crime = decomp_crime.seasonal
		trend_crime   = decomp_crime.trend
		
		title = 'Decomposition Of Crimes Involving ' + self.crime_name +\
						' in Precinct ' + str(self.prec)

		plt.plot(self.ts, label='Monthly data', linewidth=3)
		plt.plot(season_crime, label='Seasonality', linewidth=3)
		plt.plot(trend_crime, label='Trend', linewidth=3)
		plt.title(title,fontsize=13)
		plt.xlabel('Year', fontsize=13)
		plt.legend()


	def plot_per_day(self):
		"""
		Makes a bar plot of percent of crimes which occur during each day in the week.
		"""
		plt.clf()
		self.percent_per_day()
		
		title = 'Percentage of ' +\
			self.crime_name +' in Precinct ' +\
			str(self.prec) + ' by day of week' 
        
		fig = plt.figure(figsize=(8, 5))
  	      
 		self.DAYS_OF_CRIME.plot(kind='bar')
      
		plt.title(title,fontsize=13)
		plt.yticks(size=14)
 		plt.xticks(rotation=30,size=14)
		plt.ylabel('Percent of crimes', fontsize=13)

	def plot_per_hour(self):
		"""
		Makes a bar plot of percent of crimes which occur during each day in the week.
		"""
		plt.clf()
		self.percent_per_hour()
		title = 'Percentage of ' + self.crime_name +\
			' in Precinct ' + str(self.prec) +\
			' by time of day' 

		fig = plt.figure(figsize=(8, 5))
		self.CRIME_HOURS.plot(kind='bar')
		plt.title(title,fontsize=13)
		plt.yticks(size=14)
		plt.xticks(rotation=45,size=16)
		plt.xlabel('Hour In Day', fontsize=13)
		plt.ylabel('Pecent of crimes', fontsize=13)
