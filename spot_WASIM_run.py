# -*- coding: utf-8 -*-
"""
Created on Tue May 23 15:22:18 2023

@author: herzo
"""


from spot_WASIM_setup import spot_setup
import spotpy
import os
from distutils.dir_util import remove_tree

def main(): 
    
    # TODO: Set to mpi if parallel running is wanted
    parallel = "seq"
    # TODO: Give a name to the spotpy database to store the csv results
    dbname = "LHS_WASIM"
    # TODO: Select number of maximum repetitions
    rep = 2
    
    # Initialization of SPOTPY setup
    # TODO default run mode (r_mode) is "seq", change to "mpi" for parallel processing
    # TODO default time step (tstep) is daily ("D"), change to "H" for hourly
    setup = spot_setup(r_mode= parallel, tstep = "D")
    
    # TODO define algorithm 
    sampler = spotpy.algorithms.lhs(
        setup, dbname=dbname, dbformat="csv", parallel =parallel)
    # start the sampler with specified number of repetitions
    sampler.sample(rep)
    
    # if SPOTPY has been run in parallel, delete all copied folders
    if parallel == "mpi":
        folders_del = [folder for folder in os.listdir() if 'core' in folder]
        for fol_del in folders_del:
            remove_tree(fol_del)
    
    # Load the results gained with the sampler, stored in csv database
    results = spotpy.analyser.load_csv_results(dbname)
    
    # plot the best modelrun
    spotpy.analyser.plot_bestmodelrun(results, setup.full_observation)   
    
    # identifiy best x percent of the model runs (based on like1)
    posterior=spotpy.analyser.get_posterior(results, percentage=20)
    # plot parameter interaction
    spotpy.analyser.plot_parameterInteraction(posterior)

if __name__ == "__main__":
    
    main()


