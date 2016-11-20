from flask import render_template
from flask import Response
from flask import request
from frontend import app
from flask import send_file
import os.path

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
		
		CT.plot_precinct()
		CT.get_crime_data()
		CT.make_timeseries(crime_type)
		CT.decompose_crime()
		CT.percent_per_day()
		CT.percent_per_hour()
		precinct = CT.get_precinct()
		address = CT.get_address()
		crime_info = {}
		crime_info['crime_type'] = crime_type
		crime_info['address'] = address
		crime_info['precinct'] = precinct
		return render_template("output.html", 
													crime_info = crime_info,
													map="/map")


