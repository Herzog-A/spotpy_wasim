# SPOTPY+ WaSiM 
[![DOI](https://zenodo.org/badge/728705155.svg)](https://doi.org/10.5281/zenodo.14987399)

This Git directory has been developed as part of the publication 'Linking Parameter Sensitivities and Hydrological Process Behavior in Complex Alpine Terrain' (publishing in progress). 
It features the integration of WaSiM-ETH (Schulla 2021) into the SPOTPY Framework (Houska 2015). 

# Integrating WaSiM-ETH into the SPOTPY framework 

All scripts are based on the original SPOTPY integration stucture developed and provided by Tobias Houska (2015). A detailed documentation of SPOTPY can be found [here](https://spotpy.readthedocs.io/en/latest/).

In order to run the calibration a specific environment setup, folder sturucture and files are necessary.

## WaSiM setup structure
The WaSiM model itself has to be stored in a subfolder named 'wasim_mod'. Within this subfolder all usual setup files must be contained, including the input and output folders as well as the control file and executables. For a detailed description of the WaSiM model setup see Schulla 2021. 
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
The `spot_WASIM_setup.py` script is the central part of the coupling. In this scirpt some variables must be defined for the coupling to work. This includes 

-- the control file name
-- the executalble name
-- the name and location of the file containing observation data
-- the gauge used for evaluation (column name in obs file)
-- the subbasin used for evaluation

The `spot_WASIM_function.py` script includes all functions required by the `spot_WASIM_setup.py` script. It must be located in the same folder.

In order to start a SPOTPY analysis the `spot_WASIM_run.py` script has be executed. Again a few adaptions have to be made.

-- parallel : define whether to run in sequential ("seq") order or parallel ("mpi")
-- dbname:    define the name of the output data base
-- rep:       define the number of repetitions 

within the `spot_setup()` function define the timestep as "D" for daily or "H" for hourly. If no timestep or run mode is provided, the algorithm assums daily timesteps and sequential running. 

# Additional files
    
## Parameter Range definition
Within the current folder a `parameter_ranges.txt` has to be present, in which all parameters and thier range boundries are defined. 
The file has to include a header with ["par"; "min"; "max"] where in the first columns the parameter name is defined as it is in the correstponding control file of WaSiM, min represents the lower boundry of the sampled parameter range and max the upper boundry. All entries must be ";" seperated. 

## Observation data
In order to calculate the objetive function observation data for comparison has to be provided. In the provided basic version, only discharge data is evaluated. 
The Data has to be provided in the WaSiM typical statistical data format. (1st row buffered for header, line 6 used as header with name definition of subbasin / evaluation points, values in the following rows; columns: YYYY, MM, DD, HH, [gauguing stations...]).
The timeseris must be at least as long as the simuluation period, the overlapping period is selected automatically. Non valid observations must be formatted as -9999.
The location of the file has to be defined in the `__init__()` section of the setup script.

# Environment configuration
The spotpy_environment.yml contains the conda environment used at the linux cluster. Additionally to that modules for netCDF, OpenMPI and Conda have to be loaded (see `spotpy.job` file).

A guide on how to install and use miniconda can be found [here](https://docs.anaconda.com/miniconda/install/).

# Known Issues and Limitations
This setup is only a basic configuration of the coupeling and can be easily extended to evaluate extended amounts of output or spatial output. 

Be aware, that the parallel processing on High Performance Clusters requires HPC specific configuration of the neccessary modules. Not all WaSiM Versions require the same modules and might not be compatible with all requirements for SPOTPY. You can find infomration on the required WaSiM configuration on the WaSiM-Documentation site. 

# Data sources and availability

### WaSiM
WaSiM is used here in the 10.08th Richards Version, available from the WaSiM Web Page [www.wasim.ch](http://www.wasim.ch/en/products/wasim_richards.htm). Also a full model documentation can be found here. 

### Meteorological Data
The example setup is configured with Meteorological Data extracted from the INCA-Dataset of ZAMG of Geosphere Austria, available from the Geosphere Austria Data Hub at https://doi.org/10.60669/6akt-5p05.

### Topographical Data
The DEM is part of the GMES RDA project of the European Environmental Agency and available from https://sdi.eea.europa.eu/catalogue/copernicus/api/records/66fa7dca-8772-4a5d-9d56-2caba4ecd36a

### Landcover Data
The Land cover classes have been derived from Sentinel2 Data of the the European Union’s Copernicus Land Monitoring Service information, available at https://doi.org/10730.2909/3e2b4b7b-a460-41dd-a373-962d032795f3

### Spotpy 
SPOTPY is an open source python package available at https://github.com/thouska/spotpy used in the v1.6.2 version in this coupeling. 
(To use the eFAST algorithm used in the according Paper, SPOTPY must be used in v1.6.6).

# References
Schulla, J. (2021). Model description wasim: Water balance simulation model: Version 10.06.00. Zürich. Retrieved 24.05.2024, from http://www.wasim.ch/en/1004
products/wasim description.htm1005

Schulla, J., Jasper, K., Foerster, K., & Kopp, M. (2024). Wasim [Software]. Retrieved from http://www.wasim.ch/en/products/wasim_richards.htm

Houska, T. (2015b). Spotpy documentation [Computer software manual]. Retrieved from https://spotpy.readthedocs.io/en/latest/888

Houska, T. (2025). Spotpy [Software]. Retrieved from https://github.com/thouska/spotpy doi: 10.1371/journal.pone.0145180890

Houska, T., Kraft, P., Chamorro-Chavez, A., & Breuer, L. (2015a). Spotting model parameters using a ready-made python package. PloS one, 10 (12), e0145180. doi: 10.1371/journal.pone.0145180