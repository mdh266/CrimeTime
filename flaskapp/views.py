"""
Views module contains the Flask methods to be called on the front end and
makes request to the various backend modules.
"""

from flask import render_template
from flask import Response
from flask import request
from flask import send_file
from flask import redirect, url_for

from flaskapp import app

from matplotlib.collections import PatchCollection

import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../backend/")
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../flaskapp/")

from CrimeMapper import CrimeMapper
from imageEngine import (all_crimes,
						 future,
						 historical)

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


	CT = CrimeMapper(True)

	if CT.find_precinct(address) == False:
		return render_template("error.html")
	else:
		if crime_type == "All Crimes":
			return all_crimes(CT, CT.get_precinct())
		else:
			CT.get_crime_data(crime_type)
			CT.make_time_series()

			if timeline == "Historical":
				return historical(CT, crime_type)
			else:
				return future(CT, crime_type, borough)


