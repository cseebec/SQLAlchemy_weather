import numpy as np
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func

from flask import Flask, jsonify


#################################################
# Database Setup
#################################################
engine = create_engine("sqlite:///hawaii.sqlite")

# reflect an existing database into a new model
Base = automap_base()
# reflect the tables
Base.prepare(engine, reflect=True)

# Save reference to the table
measurement = Base.classes.measurement
station = Base.classes.station

#################################################
# Flask Setup
#################################################
app = Flask(__name__)


#################################################
# Flask Routes
#################################################

# Home Page
@app.route("/")
def welcome():
    """List all available api routes."""
    return (
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/<StartDate>"
    )

#Precipitation Route
@app.route("/api/v1.0/precipitation")
def precipitation():
    # Create our session (link) from Python to the DB
    session = Session(engine)

    """Return the JSON list of all dates and precipitation amounts over the last year"""
    # First Find the most recent date in the dataset
    most_recent_date = session.query(measurement).order_by(measurement.date.desc()).first()
    # Next convert this result to a date type
    most_rec_date = datetime.strptime(most_recent_date.date, '%Y-%m-%d')
    # Find one year ago from this date
    year_ago_most_rec_date = most_rec_date - relativedelta(years=1)
    # I have to go back an extra day or else the last date in a full year back is not included
    year_ago_most_rec_date = year_ago_most_rec_date - relativedelta(days=1)
    
    #Query the last 12 months of the measurement data getting the date and prcp. In order of ascending dates
    results_prcp = session.query(measurement.date, measurement.prcp).filter(measurement.date>=year_ago_most_rec_date).\
        filter(measurement.date<most_rec_date).order_by(measurement.date).all()

    session.close()
    
    recent_year_prcp = []
    for date, prcp in results_prcp:
        date_dict = {}
        date_dict[date] = prcp
        recent_year_prcp.append(date_dict)
    
    return jsonify(recent_year_prcp)


#Stations Route
@app.route("/api/v1.0/stations")
def stations():
    # Create our session (link) from Python to the DB
    session = Session(engine)

    """Return a list of stations in descending order of appearances in dataset"""
    #Query the dataset to get a list of stations and a count of many times each one appeared in the dataset
    results = session.query(measurement.station).group_by(measurement.station).\
        order_by(func.count(measurement.station).desc()).all()

    session.close()

    all_stations = list(np.ravel(results))
    return jsonify(all_stations)



#Tobs
@app.route("/api/v1.0/tobs")
def tobs():
    # Create our session (link) from Python to the DB
    session = Session(engine)

    """Return a JSON list of temperature observations (TOBS) for the previous year for the most active station"""
    #Find the station that appears in the dataset the most 
    most_active_station = session.query(measurement.station).group_by(measurement.station).\
        order_by(func.count(measurement.station).desc()).first()

    # Find dates for most recent year in the dataset. Same code used in precipitation route
    most_recent_date = session.query(measurement).order_by(measurement.date.desc()).first()
    most_rec_date = datetime.strptime(most_recent_date.date, '%Y-%m-%d')
    year_ago_most_rec_date = most_rec_date - relativedelta(years=1)
    year_ago_most_rec_date = year_ago_most_rec_date - relativedelta(days=1)

    # Use the dates found and the most active station and query the data for the temperatures over the course of the year for this station
    results_tobs = session.query(measurement.date, measurement.tobs).filter(measurement.station == most_active_station.station).\
    filter(measurement.date>=year_ago_most_rec_date).filter(measurement.date<most_rec_date).all()

    session.close()

    recent_year_tobs = []
    for date, tobs in results_tobs:
        date_dict = {}
        date_dict[date] = tobs
        recent_year_tobs.append(date_dict)
    
    return jsonify(recent_year_tobs)


# Start Date 
@app.route("/api/v1.0/<StartDate>s")
def user_start_date(StartDate):
    """Return a JSON list of the minimum temperature, the average temperature, and the max temperature for a user inputted start date"""
    user_date = datetime.strptime(StartDate, '%Y-%m-%d')
    
    return f"You entered the date {user_date}"

# Define main behavior
if __name__ == '__main__':
    app.run(debug=True)
