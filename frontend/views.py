from flask import render_template
from flask import Response
from flask import request
from frontend import app
from flask import send_file
import os.path

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


@app.route('/')
@app.route('/index')
def index():
	user = {'nickname': 'Mike'}
	return render_template("index.html",
					title = 'Home',
					user = user)

@app.route('/input')
def crime_time_input():
	return render_template("input.html")

@app.route('/contact')
def contact():
	return render_template("contact.html")


@app.route('/output')
def crime_time_output():
	crime_type = str(request.args.get('crime_type'))
	address = str(request.args.get('nyc_address'))
	CT = CrimeMapper()
	if CT.find_precinct(address) == False:
		return render_template("error.html")
	else:
		CT.get_crime_data()
		CT.make_timeseries(crime_type)

		precinct = int(CT.get_precinct())
		CT.geo_df['precinct'] = CT.geo_df['precinct'].astype(int)
		prec_index = CT.geo_df[CT.geo_df.precinct==precinct].index
		prec = CT.geo_df['geometry'][prec_index[0]]
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
		plt.tight_layout()
		io = StringIO()
		fig.savefig(io, format='png')
		map = base64.encodestring(io.getvalue())
		map = urllib.quote(map.rstrip('\n'))


		plt.clf()
		decomp_crime = seasonal_decompose(CT.ts,freq=12)
		trend_crime = decomp_crime.trend
		season_crime = decomp_crime.seasonal
		y_max = float(CT.ts.max())
		y_min = float(season_crime.min())
		#print y_min
		title = 'Decomposition Of Crimes Involving ' + CT.crime_name +\
						' in Precinct ' + str(precinct)

		fig = plt.figure(figsize=(7, 6))
		plt.title(title , fontsize=13)
		plt.plot(CT.ts, label='Monthly Incident Data', linewidth=3)
		plt.plot(season_crime, label='Seasonality', linewidth=3)
		plt.plot(trend_crime, label='Trend', linewidth=3)
		plt.ylim([(1.25)*y_min,(1.5)*y_max])
		plt.xlabel('Year', fontsize=13)
		plt.ylabel('Monthly Incidents', fontsize=13)
		plt.legend(fontsize=13)

		io2 = StringIO()
		fig.savefig(io2, format='png')
		decompose = base64.encodestring(io2.getvalue())
		decompose = urllib.quote(decompose.rstrip('\n'))


		plt.clf()
		CT.percent_per_day()
		title = 'Percentage of ' +\
						CT.crime_name +' in Precinct ' +\
						str(precinct) + ' by day of week' 
        
		fig = plt.figure(figsize=(9, 8))
        
 		CT.DAYS_OF_CRIME.plot(kind='bar')
        
		plt.title(title,fontsize=16)
		plt.yticks(size=14)
 		plt.xticks(rotation=30,size=14)
		plt.ylabel('Percent of crimes', fontsize=16)

		io3 = StringIO()
		fig.savefig(io3, format='png')
		days = base64.encodestring(io3.getvalue())
		days = urllib.quote(days.rstrip('\n'))


		plt.clf()
		CT.percent_per_hour()
		title = 'Percentage of ' + CT.crime_name +\
						' in Precinct ' + str(precinct) +\
						' by time of day' 

		fig = plt.figure(figsize=(8, 8))
		CT.CRIME_HOURS.plot(kind='bar')
		plt.title(title,fontsize=15)
		plt.yticks(size=14)
		plt.xticks(rotation=45,size=16)
		plt.xlabel('Hour In Day', fontsize=14)
		plt.ylabel('Pecent of crimes', fontsize=16)

		io4 = StringIO()
		fig.savefig(io4, format='png')
		hours = base64.encodestring(io4.getvalue())
		hours = urllib.quote(hours.rstrip('\n'))

		address = CT.get_address()
		crime_info = {}
		crime_info['crime_type'] = crime_type
		crime_info['address'] = address
		crime_info['precinct'] = precinct


		
		return render_template("output.html", 
													crime_info = crime_info,
													map=map,
													decomp=decompose,
													day=days,
													hour=hours)


