import matplotlib.pyplot as plt
from matplotlib.collections import PatchCollection

from descartes import PolygonPatch

from io import BytesIO
import base64

from statsmodels.tsa.seasonal import seasonal_decompose

from flask import render_template

import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../backend/")

from CrimeMapper import CrimeMapper
from Forecasting import Seasonal_ARIMA


def all_crimes(CT : CrimeMapper, borough : str) -> render_template:
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

	prec = CT.get_precinct_shape()

	# Now make the map of the police precincts and color in the one
	# that includes the address the user suppslied.
	cm          = plt.get_cmap('RdBu')
	num_colours = len(prec)
 
	fig = plt.figure(figsize=(5, 4))
	ax  = fig.add_subplot(111)
	CT.precinct_helper.geo_df.plot(ax=ax, color='white', edgecolor='black')

	patches = []
	for idx, p in enumerate(prec):
		colour = cm(1. * idx / num_colours)
		patches.append(PolygonPatch(p, fc='#cc00cc', ec='#555555',
      		                          lw=0.2, alpha=1., zorder=4))
	ax.add_collection(PatchCollection(patches, match_original=True))
	# ax.set_xticks([])
	# ax.set_yticks([])
	plt.tight_layout()


	#Have to save the image this way so that the program can be run on AWS
	img = BytesIO()
	fig.savefig(img, format='png')
	img.seek(0)
	precinct_map = base64.b64encode(img.read()).decode("UTF-8")


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

	plt.xlabel('Year', fontsize=13)
	plt.ylabel('Monthly Incidents', fontsize=13)
	plt.legend(fontsize=13, ncol=2)
	plt.title("Monthly Crime Trends",fontsize=13)
	
	# Have to save the image this way so that the program can be run on AWS
	img2 = BytesIO()
	fig.savefig(img2, format='png')
	img2.seek(0)
    
	trends = base64.b64encode(img2.read()).decode("UTF-8")

	return render_template("AllCrimes.html",
							precinct_map  = precinct_map,
							trends        = trends,
							crime_info    = crime_info,
							precinct_info = precinct_info)


def future(CT : CrimeMapper, crime_type: str, borough : str) -> render_template:
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
	crime_info['address']    = CT.get_address()
	crime_info['precinct']   = CT.get_precinct()
	crime_info['crime_type'] = crime_type
	
	precinct_info            = CT.get_precinct_info()
	precinct_info['borough'] = borough

	#######################################################
	# make map
	#######################################################

	prec = CT.get_precinct_shape()

	# Now make the map of the police precincts and color in the one
	# that includes the address the user suppslied.
	cm          = plt.get_cmap('RdBu')
	num_colours = len(prec)
 
	fig = plt.figure(figsize=(5, 4))
	ax  = fig.add_subplot(111)
	CT.precinct_helper.geo_df.plot(ax        = ax,
								   color     = 'white',
								   edgecolor = 'black')

	patches = []
	for idx, p in enumerate(prec):
		colour = cm(1. * idx / num_colours)
		patches.append(PolygonPatch(p, fc='#cc00cc', ec='#555555', 
      		                           lw=0.2, alpha=1., zorder=4))
	ax.add_collection(PatchCollection(patches, match_original=True))
	ax.set_xticks([])
	ax.set_yticks([])

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
	SAR.forecast_results.ix[-24:].plot(linewidth=2.5, color="blue")

	plt.ylabel('Monthly Incidents', fontsize=13)
	title = "Future monthly {crime_type} rates in Precinct {precinct}"\
				.format(crime_type = crime_info['crime_type'],
					    precinct   = crime_info['precinct'])

	plt.title(title,fontsize=13)
	# Have to save the image this way so that the program can be run on AWS
	img2 = BytesIO()
	fig2.savefig(img2, format='png')
	img2.seek(0)
	future = base64.b64encode(img2.read()).decode("UTF-8")


	return render_template("future.html", 
							crime_info    = crime_info,
							precinct_info = precinct_info,
							precinct_map  = precinct_map,
							future        = future)
	
	
def historical(CT : CrimeMapper, crime_type: str) -> render_template:
	"""
	Makes the historical plots based of the data and pass them
	off to the html file.
	
	:Parameters:
		**CT** (:class:`backend.CrimeMapper`): 
		CrimeMapper object for which to store the address and crime data.

		**crime_type** (str): 
			The specific user selected type of crime, i.e. 'Assualt'.

	:returns: historical.html
	
	:rtype: html
	"""
	# Now make the map of the police precincts and color in the one
	# that includes the address the user suppslied.

	crime_info               = {}
	crime_info['crime_type'] = crime_type
	crime_info['address']    = CT.get_address()
	crime_info['precinct']   = CT.get_precinct()

	fig = plt.figure(figsize=(7, 6))
	ax = fig.add_subplot(111)
	plt.clf()

	title = "Seasonality Of Crimes Involving {crime_type} in Precinct {precinct}"\
				.format(crime_type = crime_info['crime_type'],
					    precinct   = crime_info['precinct'])

	decomp_crime = seasonal_decompose(CT.ts, freq=12)
	season_crime = decomp_crime.seasonal[0:12]
	plt.plot(season_crime, color='blue', label='Seasonality', linewidth=3)
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
	title = "Decomposition Of Crimes Involving {crime_type} rates in Precinct {precinct}"\
				.format(crime_type = crime_info['crime_type'],
					    precinct   = crime_info['precinct'])

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
	title = "Percentage of {crime_type} rates in Precinct {precinct} by day of week"\
				.format(crime_type = crime_info['crime_type'],
					    precinct   = crime_info['precinct'])
        
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
	title = "Percentage of {crime_type} rates in Precinct {precinct} by time of day"\
				.format(crime_type = crime_info['crime_type'],
					    precinct   = crime_info['precinct'])


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


	# push the produced images to the output website page
	return render_template("historical.html", 
							crime_info = crime_info,
							trend      = trend,
							decomp     = decompose,
							day        = days,
							hour       = hours)
		
