# SPOTPY+ WaSiM
# Integrating WaSiM-ETH into the SPOTPY framework 

All scripts are based on the original SPOTPY integration stucture developed and provided by Tobias Houska (2015).

In order to run the calibration a specific environment setup, folder sturucture and files are necessary.

## WaSiM setup structure
The WaSiM model itself has to be stored in a subfolder named 'wasim_mod'. Within this subfolder all usual setup files must be contained, including the input and output folders as well as the control file and executables. For a detailes description of the WaSiM model setup see Schulla 2021. 
In order for the integration to work, a few adaptions have to made to the control file. 
**All Parameters used during the analysis have to be defined as variables using the common style of `$set $<parameter> = <value>`. The value will be modified automatically by the SPOTPY-Algorithm for each model run.**
Also the model time should be defined as parameters using 

    ```
    $set $time         (length of one timestep in min)
    $set $startyear 
    $set $startmonth
    $set $startday
    $set $starthour
    $set $startminute
    $set $endyear
    $set $endmonth
    $set $endday
    $set $endhour
    $set $endminute
    ```
If you want to evaluate the routed discharge, the name of the output file should countain the character sequence "rout". 

## SPOTPY structure
The SPOTPY framework is sturctured in 3 different scripts. 
The <spot_WASIM_setup.py> script is the central part of the coupling. In this scirpt some variables must be defined for the coupling to work. This includes 

-- the control file name
-- the executalble name
-- the name and location of the file containing observation data
-- the gauge used for evaluation (column name in obs file)
-- the subbasin used for evaluation

The <spot_WASIM_function.py> script includes all functions required by the <spot_WASIM_setup.py> script. It must be located in the same folder.

In order to start a SPOTPY analysis the <spot_WASIM_run.py> script has be executed. Again a few adaptions have to be made.

-- parallel : define whether to run in sequential ("seq") order or parallel ("mpi")
-- dbname:    define the name of the output data base
-- rep:       define the number of repetitions 

within the <spot_setup()> function define the timestep as "D" for daily or "H" for hourly. If no timestep or run mode is provided, the algorithm assums daily timesteps and sequential running. 

# Additional files
    
## Parameter Range definition
Within the current folder a `parameter_ranges.txt` has to be present, in which all parameters and thier range boundries are defined. 
The file has to include a header with ["par"; "min"; "max"] where in the first columns the parameter name is defined as it is in the correstponding control file of WaSiM, min represents the lower boundry of the sampled parameter range and max the upper boundry. All entries must be ";" seperated. 

## Observation data
In order to calculate the objetive function observation data for comparison has to be provided. At the current stage, only discharge data has been tested but this might get extended in futre. 
The Data has to be provided in the WaSiM typical statistical data format. (1st row buffered for header, line 6 used as header with name definition of subbasin / evaluation points, values in the following rows; columns: YYYY, MM, DD, HH, [gauguing stations...]).
The timeseris must be at least as long as the simuluation period, the overlapping period is selected automatically. Non valid observations must be formatted as -9999.
The location of the file has to be defined in the `__init__()` section of the setup script.

# environment configuration
The spotpy_environment.yml contains the conda environment used at the linux cluster. Additionally to that modules for netCDF, OpenMPI and Conda have to be loaded (see <spotpy.job> file).
 