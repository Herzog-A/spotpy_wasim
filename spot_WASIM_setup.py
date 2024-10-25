# -*- coding: utf-8 -*-
"""
Created on Wed Nov 23 14:25:19 2022

This file is part of the Statisitcal Parameter Estimation tool SPOTPY
Tobias Houska 2015

This file couples the WaSiM-ETH model with the SPTOPY structure

@author: Anna Herzog 
"""
import spot_WASIM_functions as fun
import pandas as pd
import spotpy
import os
import subprocess
import numpy as np
from distutils.dir_util import copy_tree, remove_tree
from datetime import datetime as dt
# only needed when using parallel computing
from mpi4py import MPI  


"""
Definition of the SPTOPY class
default settings are:
        Daily timestep ("D")
        sequential processing ("seq")
        windoes opperating system ("win")
    ATTENTION:  for modification of the standard settings call the spot_setup with 
                with arguments eg. spot_setup(tstep = "H", r_mode = "mpi", sys = "linux")
"""    
class spot_setup(object):
    
    """
    Initialisation function, which will only be run once
    """
    def __init__(self, tstep = "D", r_mode = "seq", sys = "win"):
        
        self.sys = sys 
        self.tstep = tstep
        self.par_def = fun.read_parameters('parameter_ranges.txt')
        self.params = self.par_def[0]
        self.parnames = self.par_def[1]

        # TODO: Set the path to the WASIM Project Folder
        self.mod_dict = "wasim_mod"

        # TODO: Set the name of the WaSiM control file
        self.ctrl_name = "fundus_25.ctrl"
        
        # TODO: set the path and file name for the observation data
        self.WASIM_obs_file = self.mod_dict+os.sep + "input"+os.sep+"hydro"+os.sep+"fundus-qh_all.txt"

        # identify model_time
        # TODO set timestep size ("D" for daily, "H" for hourly)
        self.time_range = fun.model_time(self.mod_dict + os.sep + self.ctrl_name, tstep)

        # TODO definition of calibration periods
        self.calibration_range =pd.date_range(start = dt.strptime("2018/01/01 00:00", '%Y/%m/%d %H:%M'),
                                              end = dt.strptime("2018/01/09 23:00", '%Y/%m/%d %H:%M'),
                                              freq = tstep,
                                              tz= None)

        # Reading Observation data for specified gauges
        # TODO: define the gauges used for evaluation (objective function calculation)
        #       and the corresponding sub basins
        self.gauge_file = "input" + os.sep + "hydro" + os.sep + "fundus-qh_all.txt"
        self.gauge = "Fundus 1989"
        # TODO definition of subbasin identifier for evaluation
        self.sb_eval = "2"                          

        # generate pandas data frame with valid observation data and time steps at
        # specified gauge
        self.obs = fun.read_wasim_qobs(self.mod_dict + os.sep + self.gauge_file,
                                            self.gauge,
                                            self.time_range,
                                            tstep)
        # generate np.array of full observation data for e.g. plot of best model run
        self.full_observation = self.obs[self.gauge].values.flatten()

        # Set to false to reduce command line print outs
        self.verbose = True

        # further mpi settings
        self.parallel = r_mode
        print("run mode: " + self.parallel)
        self.curdir = os.getcwd()
        self.wasim_path = self.curdir + os.sep + self.mod_dict
      
        if sys == "win" :
            self.seperator = chr(92)
        elif sys == "linux":
            self.seperator = "/"

    """
    SPOTPY parameter function to generate parameter sets for each run based on
    predefined parameter ranges
    """
    def parameters(self):
        return spotpy.parameter.generate(self.params)

    """
    SPOTPY simulation function to run each single simulation with according
    parameter sets
    I: Parameterset
    O: Simulation results as numpy array
        ATTENTION:  in this version only one simulation output (discharge volumne
                    at specified gauge) is regarded for evaluation! This is possible
                    to extend, but only along the with observation data. 
    """
    def simulation(self, parset):
        
        # check for parallel processing
        if self.parallel == "mpi":
            # if so, check the id of the current computation core
            call = str(MPI.COMM_WORLD.Get_rank())
            run_path = self.wasim_path + "core" + call

        else:
            run_path = self.wasim_path +"_seq"

        # Generate a new folder with all underlying files
        # to prevent reading/writing interference if it doesn't exist already
        if os.path.exists(run_path) == True:
            remove_tree(run_path)
            print("old run removed")

        if os.path.exists(run_path) == False:
            try:
                copy_tree(self.wasim_path, run_path)
                print("copy run folder successful")
            except:
                print("Error: some error has occured during copy process")
                    
        # change the working directory to the copied model folder for execution
        os.chdir(run_path)

        # Open WASIM control file
        ctrl = fun.open_wasim_ctrl(self.ctrl_name)
            
        # modify seperator to match os
        ctrl = fun.change_wasim_parameter("sep", self.seperator, ctrl)

        # Change WaSiM Parameters
        for par_name, par_value in zip(self.parnames, parset):
            ctrl = fun.change_wasim_parameter(par_name, par_value, ctrl)

        # Write Parameter Values into control file
        fun.write_wasim_ctrl(self.ctrl_name, ctrl)

        # initialize the soil storage parameters in .fsz file for seamless parameter adaption
        fun.initilize_soilstorage(self, ctrl)

        # run the model
        try:
            print("run WaSiM")
            fun.run_model("wasim", self.ctrl_name, self.sys)
        except Exception:
            print("wasim took longer than expected - timeout")


        # TODO chose which simulation results shall be used for calibration/analysis
        # load the simulation results of the routing routine
        simulation = fun.read_wasim_results("routing"+os.sep+"qgko.stat", self.sb_eval)

        # check if the simulation results cover to whole time range or weather there
        # if not set whole time series to NA to account for invalid simulation
        if simulation.shape[0] < len(self.time_range):
            for i in range(0, simulation.shape[0]):
                simulation = np.full((len(self.time_range)), -9999)
            print("simulation results NOT VALID")
        else: print("simulation results valid")
        
        # change work directory back to inital directory
        os.chdir(self.curdir)

        # returns list of results as np array
        return simulation
    
    """
    SPOTPY function to return evaluation data [pd.data frame with time and gauge]
    """
    def evaluation(self):

        evaluation = self.obs[self.obs['time'].isin(self.calibration_range)]
        return evaluation
    
    """
    SPOTPY function to calculate objective functions or evaluation criteria
    I: simulation [np.array] and evaluation data [pd.df]
    O: objective function value as single value or list []
    """    
    def objectivefunction(self, simulation, evaluation):
        
        # select only valid observation data
        evaluation = evaluation.dropna() 
        
        # create pandas df from simulation data, and include time column
        sim = pd.DataFrame({'time': self.time_range, 
                            "sim" : simulation})
        
        # merge observation data and simulation data by valid observation time
        # steps to have same length of time series
        data = evaluation.merge(sim, how= "left")
        
        # calculate SPOTPY objective function whcih requires numpy arrays
        # therefore extraction from pandas df
        # TODO select objective function you want to use
        kge = spotpy.objectivefunctions.kge(data[self.gauge].values.flatten(),
                                            data["sim"].values.flatten())

        # return objective function value
        return kge
