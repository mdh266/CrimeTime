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


import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../backend/")
from CrimeMapper import CrimeMapper

def root_dir():  # pragma: no cover
	#print os.path.realpath(__file__)
  print os.path.dirname(os.path.realpath(__file__))
  return os.path.dirname(os.path.realpath(__file__))

def get_file(filename):  # pragma: no cover
	try:
		src = os.path.join(root_dir(), filename)
		return open(src).read()
	except IOError as exc:
		return str(exc)

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

@app.route('/Hour.jpg')
def get_hour():
	mimetypes = {
  	".css": "text/css",
    ".html": "text/html",
    ".js": "application/javascript",
	}
	complete_path = os.path.join(root_dir(), '/images/Hour.jpg')
	complete_path = root_dir() + '/images/Hour.jpg'
	print complete_path
	ext = os.path.splitext('/images/Hour.jpg')[1]
	mimetype = mimetypes.get(ext, "tex")
	content = get_file(complete_path)
	return Response(content,mimetype='images/jpg')

@app.route('/Day.jpg')
def get_day():
	mimetypes = {
  	".css": "text/css",
    ".html": "text/html",
    ".js": "application/javascript",
	}
	complete_path = os.path.join(root_dir(), '/images/Day.jpg')
	complete_path = root_dir() + '/images/Day.jpg'
	print complete_path
	ext = os.path.splitext('/images/Day.jpg')[1]
	mimetype = mimetypes.get(ext, "tex")
	content = get_file(complete_path)
	return Response(content,mimetype='images/jpg')


@app.route('/Decomp.jpg')
def get_decomp():
	mimetypes = {
  	".css": "text/css",
    ".html": "text/html",
    ".js": "application/javascript",
	}
	complete_path = os.path.join(root_dir(), '/images/Decomp.jpg')
	complete_path = root_dir() + '/images/Decomp.jpg'
	print complete_path
	ext = os.path.splitext('/images/Decomp.jpg')[1]
	mimetype = mimetypes.get(ext, "tex")
	content = get_file(complete_path)
	return Response(content,mimetype='images/jpg')

#@app.route('/map')
#def get_map2():
#	return send_file('maps/map.html')

@app.route('/map.png')
def get_map():
#   return send_file('maps/map.html')
	mimetypes = {
  	".css": "text/css",
    ".html": "text/html",
    ".js": "application/javascript",
	}
	complete_path = os.path.join(root_dir(), '/images/map.png')
	complete_path = root_dir() + '/images/map.png'
	print complete_path
	ext = os.path.splitext('/images/map.png')[1]
	mimetype = mimetypes.get(ext, "tex")
	content = get_file(complete_path)
	return Response(content,mimetype='images/png')



@app.route('/output')
def crime_time_output():
	crime_type = str(request.args.get('crime_type'))
	address = str(request.args.get('nyc_address'))
	CT = CrimeMapper()
	if CT.find_precinct(address) == False:
		return render_template("error.html")
	else:
		geo_df = gpd.read_file("./data/Police_Precincts.geojson")

		#CT.plot_precinct()
		#CT.get_crime_data()
		#CT.make_timeseries(crime_type)
		#CT.decompose_crime()
		#CT.percent_per_day()
		#CT.percent_per_hour()
		precinct = int(CT.get_precinct())

		geo_df['precinct'] = geo_df['precinct'].astype(int)
		prec_index = geo_df[geo_df.precinct==precinct].index
		prec = geo_df['geometry'][prec_index[0]]
		cm = plt.get_cmap('RdBu')
		num_colours = len(prec)
 
		fig = plt.figure(figsize=(5, 4))
		ax = fig.add_subplot(111)
		geo_df.plot(ax=ax, color='white')

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
		data = base64.encodestring(io.getvalue())
		data = urllib.quote(data.rstrip('\n'))

		address = CT.get_address()
		crime_info = {}
		crime_info['crime_type'] = crime_type
		crime_info['address'] = address
		crime_info['precinct'] = precinct
		return render_template("output.html", 
													crime_info = crime_info,
													map=data)


