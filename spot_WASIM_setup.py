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
from distutils.dir_util import copy_tree
# only needed when using parallel computing
#from mpi4py import MPI  


"""
Definition of the SPTOPY class
default settings are:
        Daily timestep ("D")
        sequential processing ("seq")
    ATTENTION:  for modification of the standard settings call the spot_setup with 
                with arguments eg. spot_setup(tstep = "H", r_mode = "mpi")
"""    
class spot_setup(object):
    
    """
    Initialisation function, which will only be run once
    """
    def __init__(self, tstep = "D", r_mode = "seq"):
        
        self.par_def = fun.read_parameters('parameter_ranges.txt')
        self.params = self.par_def[0]
        self.parnames = self.par_def[1]

        # TODO: Set the name of the WaSiM control file
        self.ctrl_name = "windows_fundus_25_d.ctrl"
        #TODO: Set the name of the executable
        self.exe = "wasimvc64.exe"
        
        # TODO: set the path and file name for the observation data
        self.WASIM_obs_file = "wasim_mod"+os.sep + "input"+os.sep+"hydro"+os.sep+"fundus-qh_all.txt"

        # identify model_time
        # TODO set timestep size ("D" for daily, "H" for hourly)
        self.time_range = fun.model_time("wasim_mod"+os.sep+self.ctrl_name, tstep)

        # Reading Observation data for specified gauges
        # TODO: define the gauges used for evalution (objective function calculation)
        #       and the corresponding subbasins
        self.gauge = "Fundus 1989"
                                   

        # generate pandas data frame with valid observation data and time steps at
        # sprcified gauge
        self.obs = fun.read_wasim_qobs(self.WASIM_obs_file, 
                                       self.gauge, 
                                       self.time_range, tstep)
        # generate np.array of full observation data for e.g. plot of best model run
        self.full_observation = self.obs[self.gauge].values.flatten()
        
        # definition of subbasin identifier for evaluation
        self.sb_eval = "2"

        # Set to false to reduce command line print outs
        self.verbose = True

        # further mpi settings
        self.parallel = r_mode
        self.curdir = os.getcwd()
        self.wasim_path = self.curdir + os.sep + "wasim_mod"

    """
    SPTOPY parameter function to generate parameter sets for each run based on
    predefined parameter ranges
    """
    def parameters(self):
        return spotpy.parameter.generate(self.params)

    """
    SPOTPY simulation function to run each single simlutaion with according
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
            # And generate a new folder with all underlying files
            # to prevent reading/writing interference if it doesn't exist already
            if os.path.exists(self.wasim_path + "core" +  call) == False:
                try: 
                    copy_tree(self.wasim_path, self.wasim_path + "core" + call)
                    print("copy succesfull")
                except :
                    print("Error: some error has occured during copy process")          
                    
            # change the working directory to the copied model folder for execution
            os.chdir(self.wasim_path + "core" + call)
        
        else:
            # change working directory to the original model folder for execution
            os.chdir(self.wasim_path)

        # Open WASIM control file
        ctrl = fun.open_wasim_ctrl(self.ctrl_name)

        # Change WaSiM Parameters
        for par_name, par_value in zip(self.parnames, parset):
            ctrl = fun.change_wasim_parameter(par_name, par_value, ctrl)

        # Write Parameter Values into control file
        fun.write_wasim_ctrl(self.ctrl_name, ctrl)

        # WaSiM run command
        run_command =[ "./" + self.exe ,  "./" + self.ctrl_name, " -diaglevel=INFO"]

        print("run follows")

        process = subprocess.run(run_command, stdout = subprocess.DEVNULL)

        print("run finished")

        # load the simulation results of the routing routine
        simulation = fun.read_wasim_results("routing"+os.sep+"qgko.stat", self.sb_eval)

        # check if the simulation results cover to whole time range or weather there
        # if not set whole time series to NA to account for invalid simulation
        if len(simulation[0]) < len(self.time_range):
            for i in range(0, len(simulation)):
                simulation[i] = np.full((len(self.time_range)), -9999)
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

        return self.obs
    
    """
    SPOTPY function to calculate objective functions or evaluation criteria
    I: simulation [np.array] and evaluation data [pd.df]
    """    
    def objectivefunction(self, simulation, evaluation):
        
        # select only valid observation data
        evaluation = evaluation.dropna() 
        
        # create pandas df from simulation data, and include time column
        sim = pd.DataFrame({'time': self.time_range, 
                            "sim" : simulation}).set_index("time")
        
        # merge observation data and simulation data by valid observation time
        # stepts to have same length of time series
        data = evaluation.merge(sim, how= "left")
        
        # calculate SPOTPY objective function whcih requires numpy arrays
        # therefore extraction from pandas df
        kge = spotpy.objectivefunctions.kge(data[self.gauge].values.flatten(),
                                            data["sim"].values.flatten())

        # return objective function value
        return kge