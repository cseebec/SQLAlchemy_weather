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
        f"/api/v1.0/EnterStartDateHere.Example:2016-8-23<br/>"
        f"/api/v1.0/EnterStartDateHere/EnterEndDateHere"
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

    #Close Session
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

    #Close Session
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

    #Close Session
    session.close()

    recent_year_tobs = []
    for date, tobs in results_tobs:
        date_dict = {}
        date_dict[date] = tobs
        recent_year_tobs.append(date_dict)
    
    return jsonify(recent_year_tobs)


# Start Date 
@app.route("/api/v1.0/<StartDate>")
def user_start_date(StartDate):
    """Return a JSON list of the minimum temperature, the average temperature, and the max temperature for a user inputted start date"""
    try:
        #Convert user date from string to date type
        user_date = datetime.strptime(StartDate,'%Y-%m-%d')
    except ValueError:
        return("The value you entered does not follow the form year-month-day. An example is 2016-8-23. Make sure your date follows this form")
    else:
        #Start session
        session = Session(engine)
        # Find the latest date in dataframe 
        most_recent_date = session.query(measurement).order_by(measurement.date.desc()).first()
        most_rec_date = datetime.strptime(most_recent_date.date, '%Y-%m-%d')
        
        #Check if the date the user entered is within the dataframe
        if user_date>most_rec_date:
            #If the date the user ended is outside the dataframe dates let the user known
            return f"The latest date in the dataset is {most_rec_date} you entered {user_date} which is later than this date. Please enter an earlier date"
        else:
            session = Session(engine)
            #Query data and gather temperatures in dataset after user inputted start date
            temps_from_start_date= session.query(measurement.tobs).filter(measurement.date>=user_date).all()
            temp_from_user_date = []
            # Convert query results into a list
            for i in range(0,len(temps_from_start_date)):
                temp_from_user_date.append(temps_from_start_date[i].tobs)
            
            #Close Session
            session.close()

            #Print minimum, maximum and average temperatures.
            return (
                f"You entered a start date of {user_date}.<br/>"
                f"The mimimum temperature after this date is {min(temp_from_user_date)}<br/>"
                f"The maximum temperature after this date is {max(temp_from_user_date)}<br/>"
                f"The average temperature after this date is {sum(temp_from_user_date) / len(temp_from_user_date)}"
            )

#Enter Start Date and End Date
@app.route("/api/v1.0/<StartDate>/<EndDate>")
def user_dates(StartDate, EndDate):
    """Return a JSON list of the minimum temperature, the average temperature, and the max temperature for a user inputted start and end date"""
    try:
        #Convert user date from string to date type
        StartDate = datetime.strptime(StartDate,'%Y-%m-%d')
        EndDate = datetime.strptime(EndDate,'%Y-%m-%d')
    except ValueError:
        return (
            f"One of the dates you entered does not follow the form year-month-day .<br>" 
            f"An example is 2016-8-23. Make sure both your dates follow this form")
    else:
        #Start session
        session = Session(engine)
        # Find the latest date in dataframe 
        most_recent_date = session.query(measurement).order_by(measurement.date.desc()).first()
        most_rec_date = datetime.strptime(most_recent_date.date, '%Y-%m-%d')
        earliest_date = session.query(measurement).order_by(measurement.date).first()
        earliest_date = datetime.strptime(earliest_date.date, '%Y-%m-%d')
        # Check if the end date is after the start date 
        if EndDate<StartDate:
            return (
                f"You entered a start date of  {StartDate}.<br/>"
                f"This is after the end date you entered  {EndDate}.<br/>"
                f"Please enter a start date that is before the end date."
            )

        #Check if the start date the user entered is within the dataframe
        if StartDate>most_rec_date:
            #If the start date the user entered is outside the dataframe dates let the user known
            return (
                f"The latest date in the dataset is {most_rec_date}.<br/>"
                f"You entered a date of {StartDate}. This means your date range is outside of the dataset<br/>"
                f"Please enter an earlier start date and end date as well."
            )

        #Check if the end date the user entered is within the dataframe
        if EndDate<earliest_date:
            #If the end date the user entered is outside the dataframe dates let the user known
            return (
                f"The earliest date in the dataset is {earliest_date}.<br/>"
                f"You entered an end date of {EndDate}. This means your date range is outside of the dataset<br/>"
                f"Please enter a later end date and push the start date up as well."
            )
        else:
            #Query data and gather temperatures in between the user inputted dates
            temps_user= session.query(measurement.tobs).filter(measurement.date>=StartDate).\
                filter(measurement.date<=EndDate).all()
            temp_from_user_date = []
            # Convert query results into a list
            for i in range(0,len(temps_user)):
                temp_from_user_date.append(temps_user[i].tobs)
            
            #Close Session
            session.close()

            #Print minimum, maximum and average temperatures.
            return (
                f"You entered a start date of {StartDate} and an end date {EndDate}.<br/>"
                f"The mimimum temperature between these dates is {min(temp_from_user_date)}<br/>"
                f"The maximum temperature between these dates is {max(temp_from_user_date)}<br/>"
                f"The average temperature between these dates is {sum(temp_from_user_date) / len(temp_from_user_date)}"
            )
                 
# Define main behavior
if __name__ == '__main__':
    app.run(debug=True)
