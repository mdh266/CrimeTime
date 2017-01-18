from flask import render_template
from flask import Response
from flask import request
from frontend import app
from flask import send_file
from flask import redirect, url_for
import os.path

import sqlite3
import geopandas as gpd 

import matplotlib
matplotlib.use('Agg')
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
from StringIO import StringIO

import matplotlib.pyplot as plt
from matplotlib.collections import PatchCollection
from mpl_toolkits.basemap import Basemap
import base64
import io
from io import BytesIO 
import urllib

from shapely.geometry import Point, MultiPoint, MultiPolygon
from descartes import PolygonPatch

from statsmodels.tsa.seasonal import seasonal_decompose

import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../backend/")
from CrimeMapper import CrimeMapper
from Forcasting import Seasonal_Arima


@app.route('/')
@app.route('/input')
def crime_time_input():
	"""
	Forwards the input page for the website.
	"""
	return render_template("input.html")

@app.route('/contact')
def contact():
	"""
	Forwards the contact page for the website.
	"""
	return render_template("contact.html")

@app.route('/about')
def about():
	"""
	Forwards the about page for the website.
	"""
	return render_template("about.html")


@app.route('/output')
def crime_time_output():
	"""
	This function drives the output for the website. It takes in the address supplied by
	the user and drives all the plotting and then fowards to the output page for the 
	website.
	"""
	## Crime type: Larceny, Robbery, Burglary, Assault
	crime_type = str(request.args.get('crime_type'))
	## The address entered by the user.
	street = str(request.args.get('nyc_address'))
	borough = str(request.args.get('borough'))
	address = street + ' ' + borough
	timeline = str(request.args.get('timeline'))

	CT = CrimeMapper(True)
	if CT.find_precinct(address) == False:
		return render_template("error.html")
	else:
		if crime_type == "All Crimes":
			return all_crimes(CT, borough)
		else:
			CT.get_crime_data(crime_type)
			CT.make_time_series()
			## police precinct of the address
			precinct = int(CT.get_precinct())
			CT.geo_df['precinct'] = CT.geo_df['precinct'].astype(int)
			prec_index = CT.geo_df[CT.geo_df.precinct==precinct].index
			prec = CT.geo_df['geometry'][prec_index[0]]
			
			if timeline == "Historical":
				return historical(CT,prec,crime_type)
			else:
				return future(CT, crime_type, borough)


def all_crimes(CT, borough):
	"""
	Make the map of the precinct and historical crime rates 
	for that all the different 
	crimes and send the images off to the html file.
	"""
	# get the address, crime stats and precinct info
	crime_info = {}
	crime_info['address'] = CT.get_address()
	crime_info['precinct'] = CT.get_precinct()

	CT.get_all_crime_data()
	
	precinct_info = CT.get_precinct_info()
	precinct_info['borough'] = borough

	#######################################################
	# make map
	#######################################################

	precinct = int(CT.get_precinct())
	CT.geo_df['precinct'] = CT.geo_df['precinct'].astype(int)
	prec_index = CT.geo_df[CT.geo_df.precinct==precinct].index
	prec = CT.geo_df['geometry'][prec_index[0]]

	# Now make the map of the police precincts and color in the one
	# that includes the address the user suppslied.
	cm = plt.get_cmap('RdBu')
	num_colours = len(prec)
 
	fig = plt.figure(figsize=(5, 4))
	ax = fig.add_subplot(111)
	CT.geo_df.plot(ax=ax, color='white')

	patches = []
	for idx, p in enumerate(prec):
		colour = cm(1. * idx / num_colours)
		patches.append(PolygonPatch(p, fc='#cc00cc', ec='#555555', 
      		                          lw=0.2, alpha=1., zorder=4))
	ax.add_collection(PatchCollection(patches, match_original=True))
	ax.set_xticks([])
	ax.set_yticks([])
	#plt.label("New York City Police Precincts")
	plt.tight_layout()

	# Have to save the image this way so that the program can be run on AWS
	io = StringIO()
	fig.savefig(io, format='png')
	precinct_map = base64.encodestring(io.getvalue())
	precinct_map = urllib.quote(precinct_map.rstrip('\n'))

	#######################################################
	# make breakdown of stuff
	#######################################################

	y_max = 1.5 * float(CT.larceny_ts.max())
	y_min = 0

	plt.clf()
	fig = plt.figure(figsize=(6, 5))
	plt.ylim([y_min,y_max])
	plt.plot(CT.larceny_ts, label='Larceny', linewidth=3)
	plt.plot(CT.assault_ts, label='Assault', linewidth=3)
	plt.plot(CT.robbery_ts, label='Robbery', linewidth=3)
	plt.plot(CT.burglary_ts, label='Burglary', linewidth=3)
	plt.plot(CT.car_ts, label='Car Theft', linewidth=3)
	plt.xlabel('Year', fontsize=13)
	plt.ylabel('Monthly Incidents', fontsize=13)
	plt.legend(fontsize=13,ncol=2)
	plt.title("Monthly Crime Trends",fontsize=13)
	
	# Have to save the image this way so that the program can be run on AWS
	io2 = StringIO()
	fig.savefig(io2, format='png')
	trends = base64.encodestring(io2.getvalue())
	trends = urllib.quote(trends.rstrip('\n'))

	return render_template("AllCrimes.html",
				precinct_map=precinct_map,
				trends=trends,
				crime_info = crime_info,
				precinct_info=precinct_info)


def future(CT, crime_type, borough):
	"""
	Make the map of the precinct and forecasted crime rate 
	plot based of the seasonal arima model for that specific
	crime and send the images off to the html file.
	"""
	# get the crime and precinct info
	crime_info = {}
	crime_info['address'] = CT.get_address()
	crime_info['precinct'] = CT.get_precinct()
	crime_info['crime_type'] = crime_type
	
	precinct_info = CT.get_precinct_info()
	precinct_info['borough'] = borough

	#######################################################
	# make map
	#######################################################

	precinct = int(CT.get_precinct())
	CT.geo_df['precinct'] = CT.geo_df['precinct'].astype(int)
	prec_index = CT.geo_df[CT.geo_df.precinct==precinct].index
	prec = CT.geo_df['geometry'][prec_index[0]]

	# Now make the map of the police precincts and color in the one
	# that includes the address the user suppslied.
	cm = plt.get_cmap('RdBu')
	num_colours = len(prec)
 
	fig = plt.figure(figsize=(5, 4))
	ax = fig.add_subplot(111)
	CT.geo_df.plot(ax=ax, color='white')

	patches = []
	for idx, p in enumerate(prec):
		colour = cm(1. * idx / num_colours)
		patches.append(PolygonPatch(p, fc='#cc00cc', ec='#555555', 
      		                          lw=0.2, alpha=1., zorder=4))
	ax.add_collection(PatchCollection(patches, match_original=True))
	ax.set_xticks([])
	ax.set_yticks([])
	#plt.label("New York City Police Precincts")
	plt.tight_layout()

	# Have to save the image this way so that the program can be run on AWS
	io = StringIO()
	fig.savefig(io, format='png')
	precinct_map = base64.encodestring(io.getvalue())
	precinct_map = urllib.quote(precinct_map.rstrip('\n'))

	fig2 = plt.figure(figsize=(7, 6))
	plt.clf()

	#######################################################
	# Make the forecasted crime rates
	#######################################################

	SAR = Seasonal_Arima(CT)
	SAR.fit()
	SAR.forecast()
	SAR.forecast_results.ix[-24:].plot(linewidth=3)
	plt.ylabel('Monthly Incidents', fontsize=13)
	title = 'Future monthly ' + crime_type +\
		' rates in Precinct ' + str(precinct)
	plt.title(title,fontsize=13)
	# Have to save the image this way so that the program can be run on AWS
	io2 = StringIO()
	fig2.savefig(io2, format='png')
	future = base64.encodestring(io2.getvalue())
	future = urllib.quote(future.rstrip('\n'))

	

	return render_template("future.html", 
				crime_info = crime_info,
				precinct_info=precinct_info,
				precinct_map=precinct_map,
				future=future)
	
	
def historical(CT, prec, crime_type):
	"""
	Make the historical plots based of the data and pass them
	off to the html file.
	"""
	# Now make the map of the police precincts and color in the one
	# that includes the address the user suppslied.
	precinct = int(CT.get_precinct())
	cm = plt.get_cmap('RdBu')
	num_colours = len(prec)
 
	fig = plt.figure(figsize=(7, 6))
	ax = fig.add_subplot(111)
	CT.geo_df.plot(ax=ax, color='white')

	plt.clf()
	title = 'Seasonality Of Crimes Involving ' + crime_type +\
		' in Precinct ' + str(precinct)
	decomp_crime = seasonal_decompose(CT.ts,freq=12)
	season_crime = decomp_crime.seasonal
	plt.plot(season_crime, label='Seasonality', linewidth=3)
	plt.title(title,fontsize=13)
	plt.xlabel('Year', fontsize=13)
	#plt.xlim([2011,2013])
	#plt.legend(fontsize=13)
	
	# Have to save the image this way so that the program can be run on AWS
	io = StringIO()
	fig.savefig(io, format='png')
	trend = base64.encodestring(io.getvalue())
	trend = urllib.quote(trend.rstrip('\n'))

	# Make the image of the seasonal decomposition of crimes in this police precinct.
	plt.clf()
	trend_crime = decomp_crime.trend

	y_max = float(CT.ts.max())
	#print y_min
	title = 'Decomposition Of Crimes Involving ' +crime_type +\
		' in Precinct ' + str(precinct)

	fig = plt.figure(figsize=(7, 6))
	plt.title(title , fontsize=13)	
	plt.plot(CT.ts, 'b-', label='Monthly Incident Data', linewidth=3)
	plt.plot(trend_crime, 'r-', label='Trend', linewidth=3)
	plt.ylim([0,(1.5)*y_max])
	plt.xlabel('Year', fontsize=13)
	plt.ylabel('Monthly Incidents', fontsize=13)
	plt.legend(fontsize=13)
	
	# Have to save the image this way so that the program can be run on AWS
	io2 = StringIO()
	fig.savefig(io2, format='png')
	decompose = base64.encodestring(io2.getvalue())
	decompose = urllib.quote(decompose.rstrip('\n'))


	# Make the plot for the crimes which occur on the different days of the week
	plt.clf()
	CT.percent_per_day()
	title = 'Percentage of ' +\
		crime_type +' in Precinct ' +\
		str(precinct) + ' by day of week' 
        
	fig = plt.figure(figsize=(9, 8))
        
 	CT.DAYS_OF_CRIME.plot(kind='bar')
      
	plt.title(title,fontsize=16)
	plt.yticks(size=14)
 	plt.xticks(rotation=30,size=14)
	plt.ylabel('Percent of crimes', fontsize=16)

	# Have to save the image this way so that the program can be run on AWS
	io3 = StringIO()
	fig.savefig(io3, format='png')
	days = base64.encodestring(io3.getvalue())
	days = urllib.quote(days.rstrip('\n'))

	# Make the plot for the crimes which occur on the different hours of the day
	plt.clf()
	CT.percent_per_hour()
	title = 'Percentage of ' +crime_type +\
		' in Precinct ' + str(precinct) +\
		' by time of day' 

	fig = plt.figure(figsize=(8, 8))
	CT.CRIME_HOURS.plot(kind='bar')
	plt.title(title,fontsize=15)
	plt.yticks(size=14)
	plt.xticks(rotation=45,size=16)
	plt.xlabel('Hour In Day', fontsize=14)
	plt.ylabel('Pecent of crimes', fontsize=16)

	# Have to save the image this way so that the program can be run on AWS
	io4 = StringIO()
	fig.savefig(io4, format='png')
	hours = base64.encodestring(io4.getvalue())
	hours = urllib.quote(hours.rstrip('\n'))

		
	address = CT.get_address()
	crime_info = {}
	crime_info['crime_type'] = crime_type
	crime_info['address'] = address
	crime_info['precinct'] = precinct

	# push the produced images to the output website page
	return render_template("historical.html", 
				crime_info = crime_info,
				trend=trend,
				decomp=decompose,
				day=days,
				hour=hours)
		
