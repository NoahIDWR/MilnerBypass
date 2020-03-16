# Capacity Analysis

As part of the ongoing discussions between IWRB and stakeholders, the concept of a bypass flow at Milner has been brought up multiple times. These analyses are all designed to look at the best ways to determine what an appropriate bypass might be. The main goals of these analyses are to answer three primary questions:
> * What is the current long-term capacity?
> * What additional capacity does the program require?
> * What opportunities are available for recharge?




## Dependencies

All code was developed in Python 3.6
The following packages are required to run all the analyses

* Matplotlib
* NumPy
* Pandas
* Seaborn
* Sklearn
* Statsmodels




## Input Files

The inputs for all these programs are excel files, which can be easily edited by any other user.

### WaterRightsV2.xlsx
This file is where the water availability is determined. Adapted from previous work done and is now used as the input file to most of the other programs. 

If you want to modify this with your own recharge availability create a new excel file labeled "WaterRightsV2.xlsx" with a tab labeled "RechargeReductions". In this tab, create columns with daily date as in the first column and two columns additional columns: 1) [Milner] Flow at Milner and 2) [TotalUpperRecharge] Available recharge above Minidoka


### RechargeCells.xlsx
The file contains several tabs, which are used in various programs.
* RechargeCells - The position on the ESPAM grid where each recharge area is located. Not used here, but is used in other programs.
* RechargeCaps_2 - The seasonal recharge capacity at each site
* Uptime - Equations represented how downtime is calculated at each site
* UptimeAssumptions - What assumptions are made for each type of uptime

### Inputs.xlsx
This file is used in the NOAA forecast and is mostly collected from USBR HydroMet

## Analyses
There are some programs in this folder that I will not go into detail about. They are either old versions of existing programs or abandoned analyses. The listed programs are the programs of most interest. At some point, I will likely clean things up and make this into a cleaner design. 


### Modules
These are repeatedly used in many of the analyses
* HistoricRechargeDistribution.py -  Generates a series of random historical recharge scenarios
* NOAAPrediction.py - Grabs data from the NOAA website
* SetFonts.py - Used for plotting purposes


### Plots
These scripts generate the figures shown in the presentations 
* CFSRainbow.py - Generates the required capacity under different confidence and Milner bypass scenarios. Takes a while to generate.
* NOAA_Predictions\NOAAForecast.py - Calculates the regressions for forecasting recharge using NOAA 120 day forecasts
* BypassRainbow.py - Generates the rainbow chart used to determine how much flow should go past Milner
