"""
Views module contains the Flask methods to be called on the front end and
makes request to the various backend modules.
"""

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
# from io import StringIO

import matplotlib.pyplot as plt
from matplotlib.collections import PatchCollection
# from mpl_toolkits.basemap import Basemap
from io import BytesIO
import base64
# import io
# from io import BytesIO 
# import urllib

from shapely.geometry import Point, MultiPoint, MultiPolygon
from descartes import PolygonPatch

from statsmodels.tsa.seasonal import seasonal_decompose

import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../backend/")
from CrimeMapper import CrimeMapper
from Forecasting import Seasonal_ARIMA
from PrecinctFinder import PrecinctFinder


@app.route('/')
@app.route('/input')
def crime_time_input():
	"""
	Forwards the input.html page for the website.

	:returns: input.html
	:rtype: html
	"""
	return render_template("input.html")

@app.route('/contact')
def contact():
	"""
	Forwards the contact.html page for the website.
	
	:returns: contact.html
	:rtype: html
	"""
	return render_template("contact.html")

@app.route('/blogpost')
def blogpost():
	"""
	Forwards the BlogPost.html page for the website..

	:returns: BlogPost.html
	:rtype: html
	"""
	return render_template("BlogPost.html")


@app.route('/about')
def about():
	"""
	Forwards the about.html page for the website.

	:returns: about.html
	:rtype: html
	"""
	return render_template("about.html")


@app.route('/output')
def crime_time_output():
	"""
	This function drives the output for the website. It takes in the address supplied by
	the user and calls either of the methods,		

	* frontend.all_crimes(...)
	* frontend.historical(...)
	* frontend.future(...)

	Each of the above methods will then forward their results to a resulting html page.	
	
	:rtype: html
	"""
	## Crime type: Larceny, Robbery, Burglary, Assault
	crime_type = str(request.args.get('crime_type'))
	## The address entered by the user.
	street     = str(request.args.get('nyc_address'))
	borough    = str(request.args.get('borough'))
	address    = street + ' ' + borough
	timeline   = str(request.args.get('timeline'))


	# helper     = PrecinctFinder()

	# helper.find_precinct(address)

	# print(helper.get_address())
	# print(helper.get_precinct())

	CT = CrimeMapper(True)
	# CT.set_address_precinct(helper.get_address(),
	# 	                    helper.get_precinct())
	
	#return all_crimes(CT, borough)
	if CT.find_precinct(address) == False:
		return render_template("error.html")
	else:
		if crime_type == "All Crimes":
			return all_crimes(CT, CT.get_precinct())# helper.get_precint())
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
	Makes the map of the precinct and historical crime rates 
	for that all the different 
	crimes and send the images off to the html file.

	:Parameters:
		**CT** (:class:`backend.CrimeMapper`): 
			CrimeMapper object for which to store the address and crime data.

		**borough** (str): 
			Input string that contains the address, just number and street. 

	:returns: AllCrimes.html
	
	:rtype: html

	"""
	# get the address, crime stats and precinct info
	crime_info               = {}
	crime_info['address']    = CT.get_address()
	crime_info['precinct']   = CT.get_precinct()

	CT.get_all_crime_data()
	
	precinct_info            =  CT.get_precinct_info()
	precinct_info['borough'] = borough

	#######################################################
	# make map
	#######################################################

	precinct              = int(CT.get_precinct())
	CT.geo_df['precinct'] = CT.geo_df['precinct'].astype(int)
	prec_index            = CT.geo_df[CT.geo_df.precinct==precinct].index
	prec                  = CT.geo_df['geometry'][prec_index[0]]

	# Now make the map of the police precincts and color in the one
	# that includes the address the user suppslied.
	cm          = plt.get_cmap('RdBu')
	num_colours = len(prec)
 
	fig = plt.figure(figsize=(5, 4))
	ax  = fig.add_subplot(111)
	CT.geo_df.plot(ax=ax, color='white', edgecolor='black')

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

	#fig.savefig("test.png", format="png")

	#Have to save the image this way so that the program can be run on AWS
	img = BytesIO()
	fig.savefig(img, format='png')
	img.seek(0)
    #plt.close()
	precinct_map = base64.b64encode(img.read()).decode("UTF-8")
	#precinct_map = urllib.quote(precinct_map.rstrip('\n'))

# 	#######################################################
# 	# make breakdown of stuff
# 	#######################################################

	y_max = 1.5 * float(CT.larceny_ts.max())
	y_min = 0

	plt.clf()
	fig = plt.figure(figsize=(6, 5))
	plt.ylim([y_min,y_max])
	plt.plot(CT.larceny_ts,  label='Larceny',  linewidth=3)
	plt.plot(CT.assault_ts,  label='Assault',  linewidth=3)
	plt.plot(CT.robbery_ts,  label='Robbery',  linewidth=3)
	plt.plot(CT.burglary_ts, label='Burglary', linewidth=3)
	plt.plot(CT.car_ts,      label='Car Theft',linewidth=3)

	plt.xlabel('Year', fontsize=13)
	plt.ylabel('Monthly Incidents', fontsize=13)
	plt.legend(fontsize=13, ncol=2)
	plt.title("Monthly Crime Trends",fontsize=13)
	
	# Have to save the image this way so that the program can be run on AWS
	img2 = BytesIO()
	fig.savefig(img2, format='png')
	img2.seek(0)
    #plt.close()
	trends = base64.b64encode(img2.read()).decode("UTF-8")
	#trends = urllib.quote(trends.rstrip('\n'))

	return render_template("AllCrimes.html",
							precinct_map=precinct_map,
							trends=trends,
							crime_info = crime_info,
							precinct_info=precinct_info)


def future(CT, crime_type, borough):
	"""
	Makes the map of the precinct and forecasted crime rate 
	plot based of the seasonal arima model for that specific
	crime and send the images off to the html file.

	:Parameters:
		**CT** (:class:`backend.CrimeMapper`): 
			CrimeMapper object for which to store the address and crime data.

		**crime_type** (str): 
			The specific user selected type of crime, i.e. 'Assualt'.

		**borough** (str): 
			Input string that contains the address, just number and street. 

	:returns: future.html
	
	:rtype: html
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
	ax  = fig.add_subplot(111)
	CT.geo_df.plot(ax=ax, color='white',edgecolor='black')

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
	img = BytesIO()
	fig.savefig(img, format='png')
	img.seek(0)
	precinct_map = base64.b64encode(img.read()).decode("UTF-8")

	plt.clf()
	fig2 = plt.figure(figsize=(7, 6))


	#######################################################
	# Make the forecasted crime rates
	#######################################################

	SAR = Seasonal_ARIMA(CT)
	SAR.fit()
	SAR.forecast()
	#plt.plot(SAR.forecast_results.ix[-24:] - SAR.test_error, 'r-')
	#plt.plot(SAR.forecast_results.ix[-24:] + SAR.test_error, 'r-')
	SAR.forecast_results.ix[-24:].plot(linewidth=2.5)

	plt.ylabel('Monthly Incidents', fontsize=13)
	title = 'Future monthly ' + crime_type +\
		    ' rates in Precinct ' + str(precinct)
	plt.title(title,fontsize=13)
	# Have to save the image this way so that the program can be run on AWS
	img2 = BytesIO()
	fig2.savefig(img2, format='png')
	img2.seek(0)
	future = base64.b64encode(img2.read()).decode("UTF-8")


	return render_template("future.html", 
							crime_info = crime_info,
							precinct_info=precinct_info,
							precinct_map=precinct_map,
							future=future)
	
	
def historical(CT, prec, crime_type):
	"""
	Makes the historical plots based of the data and pass them
	off to the html file.
	
	:Parameters:
		**CT** (:class:`backend.CrimeMapper`): 
		CrimeMapper object for which to store the address and crime data.

		**prec** (int):
			The police precinct of user supplied address.

		**crime_type** (str): 
			The specific user selected type of crime, i.e. 'Assualt'.

	:returns: historical.html
	
	:rtype: html
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
	season_crime = decomp_crime.seasonal[0:12]
	plt.plot(season_crime, label='Seasonality', linewidth=3)
	plt.title(title,fontsize=13)
	plt.xlabel('Year', fontsize=13)
	labels = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct',\
			  'Nov','Dec']
	plt.xticks(season_crime.index,labels)
	
	# Have to save the image this way so that the program can be run on AWS
	img = BytesIO()
	fig.savefig(img, format='png')
	img.seek(0)
	trend = base64.b64encode(img.read()).decode("UTF-8")

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
	img2 = BytesIO()
	fig.savefig(img2, format='png')
	img2.seek(0)
	decompose = base64.b64encode(img2.read()).decode("UTF-8")


	# Make the plot for the crimes which occur on the different days of the week
	plt.clf()
	CT.percent_per_day()
	title = 'Percentage of ' +\
		crime_type +' in Precinct ' +\
		str(precinct) + ' by day of week' 
        
	fig = plt.figure(figsize=(9, 8))
        
	CT.DAYS_OF_CRIME.plot(kind='bar', color='blue')
      
	plt.title(title,fontsize=16)
	plt.yticks(size=14)
	plt.xticks(rotation=30,size=14)
	plt.ylabel('Percent of crimes', fontsize=16)

	# Have to save the image this way so that the program can be run on AWS
	img3 = BytesIO()
	fig.savefig(img3, format='png')
	img3.seek(0)
	days = base64.b64encode(img3.read()).decode("UTF-8")

	# Make the plot for the crimes which occur on the different hours of the day
	plt.clf()
	CT.percent_per_hour()
	title = 'Percentage of ' +crime_type +\
		' in Precinct ' + str(precinct) +\
		' by time of day' 

	fig = plt.figure(figsize=(8, 8))
	CT.CRIME_HOURS.plot(kind='bar',color='blue')
	plt.title(title,fontsize=15)
	plt.yticks(size=14)
	plt.xticks(rotation=45,size=16)
	plt.xlabel('Hour In Day', fontsize=14)
	plt.ylabel('Pecent of crimes', fontsize=16)

	# Have to save the image this way so that the program can be run on AWS
	img4 = BytesIO()
	fig.savefig(img4, format='png')
	img4.seek(0)
	hours = base64.b64encode(img4.read()).decode("UTF-8")

		
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
		
