# -*- coding: utf-8 -*-
"""
Created on Thu Dec  7 12:16:15 2023

This file is part of the Statisitcal Parameter Estimation tool SPOTPY
Tobias Houska 2015

This file contains all function used in the setup script (spot_setup_WASIM.py)
used to couple the WaSiM-ETH model with SPOTPY

@author: Anna Herzog 
"""

import pandas as pd
import spotpy
import os
import numpy as np
from datetime import datetime as dt

"""
Function to get parameter boundries 
I:  file name of parameter definitions [str]
        ATTENTION:  Text file with three columns ("par" = parameter name (as in Control file!),
                                                 "min" = lower boundry, 
                                                 "max" = upper boundry), 
                    with header, sperated by ";"
O:  List with two entries   1. : List with SPOTPY Parameter definitions
                            2. : List with corresponding Parameter names [str]
"""
def read_parameters(parfile):
    # read file as pandas DataFrame
    file = pd.read_csv(parfile, sep = ";")
    
    # create list of parameters (after SPOTPY parameter definition)
    params = []
    for index in range(len(file)):
        params.append(spotpy.parameter.Uniform(name = file.iloc[index].iloc[0],
                                               low= file.iloc[index].iloc[1],
    
                                               high=file.iloc[index].iloc[2]))
    # extract parameter names
    parnames = list(file['par'])
        
    return [params, parnames]

"""
Function to open the WaSiM Control file
I:  control file name [str]
O:  list of line contents in control file [str]
"""
def open_wasim_ctrl(ctrl_name):
    with open(ctrl_name, 'r') as file:
        ctrl = file.readlines()
    return ctrl


"""
function to change the WaSiM Parameters
I:  parameter name [str], 
    parameter value [numeric], 
    control file [np.file?]
O: control file [np.file?]        
"""
def change_wasim_parameter(parameter_name, parameter_value, ctrl):
    for index in range(len(ctrl)):
        if "$set $"+parameter_name in ctrl[index]:
            ctrl[index] = "$set $" + parameter_name + " = " + str(parameter_value) + " \n"
            break
    return ctrl

"""
function to overwrite the Control-file
I:  name of control file [str], 
    control file [np.file?]
"""
def write_wasim_ctrl(ctrl_name, ctrl):
    with open(ctrl_name, "wt") as file:
        file.writelines(ctrl) 

"""
function to idendify the modelled time period
I:  name of control file [str], 
    timestep ("D" or "H") [str]
O:  time range [DatetimeIndex (pandas)]
"""
def model_time(ctrl_name, tstep):   
    ctrl = open_wasim_ctrl(ctrl_name)
    # read time parameters from Control file
    tvalues = ["$set $time",
               "$set $startyear", "$set $startmonth", "$set $startday", "$set $starthour", "$set $startminute",
                "$set $endyear", "$set $endmonth", "$set $endday", "$set $endhour", "$set $endminute"]
    t_res = []
    for tvalue in tvalues:
         for index in range(len(ctrl)):    
             if tvalue in ctrl[index]:
                 val = str(int(''.join(filter(str.isdigit, ctrl[index])))).zfill(2)
                 t_res.append([tvalue, val])
                 break
    # start date
    start = t_res[1][1]+"/"+ t_res[2][1]+"/"+ t_res[3][1] +" "+ t_res[4][1]+":"+ t_res[5][1]
    start = dt.strptime(start, '%Y/%m/%d %H:%M')
    # end date
    end = t_res[6][1]+"/"+ t_res[7][1]+"/"+ t_res[8][1] +" "+ t_res[9][1]+":"+ t_res[10][1]
    end = dt.strptime(end, '%Y/%m/%d %H:%M') 
    # definition of time range according to model setup 
    time_range = pd.date_range(start, end, freq=tstep, tz = None)
        
    return time_range
        
"""
function to read observation data (eg. flow data)
I:  file+path name [str],
        ATTENTION:  current setup expects File is in WaSiM Format and only 
                    accounts for single gauge
    gauge name [str]
    time range [pd.date_range], 
    time step ("D" or "H") [str]
O:  list of numpy arrays with 
        1. (valid) observation data at specified gauge [num]
        2. time stamps of valid observations [np.datetime]
"""
def read_wasim_qobs(pathname, gauge, time_range, tstep):
    # read file
    data = pd.read_csv(pathname, 
                       sep = "\t", 
                       na_values = '-9999.000', 
                       skiprows = 4, 
                       dtype={'YYYY': str, 'MM': str, 'DD':str, 'HH':str,  'value':np.float64})
    
    # generate time seris 
    time = pd.to_datetime(pd.DataFrame({'year': data["YYYY"],
                                         'month': data["MM"],
                                         'day': data["DD"],
                                         'hour': data["HH"]}))
    
    # create pandas data frame with timestamps and observation data at gauge
    q_obs = pd.DataFrame({'time': time}).reset_index(drop=True).join(data[gauge])
    # filter observation to only data within the modelled time period
    q_obs = q_obs.loc[q_obs['time'].isin(time_range)]



    return q_obs


"""
function to read WaSiM simulation output
I:  name of the simulation file [str]
    subbasin identifier [char]
O:  np.array of simulation data for specified subbasin (full time series) 
"""
def read_wasim_results(filename, sb):
    data = pd.read_csv("output"+os.sep+ "STAT" +os.sep+ filename, 
                       sep = "\t", 
                       na_values = '-9999', 
                       skiprows = range(1,3),
                       low_memory = False)
    
    if ("rout" in filename):
        years = pd.Series(data["YY"], dtype=str)
        maxid = np.where(years.str.contains("-"))[0][0]
        data = data[0:maxid]
    
    # create pandas data frame with timestamps and observation data
    sim = data[sb].values.flatten()  
        
    return sim


