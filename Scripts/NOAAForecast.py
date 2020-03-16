# -*- coding: utf-8 -*-
"""
Created on Wed Dec  4 15:26:31 2019

@author: NStewart-maddox
"""

import pandas as pd
import numpy as np
from datetime import datetime
import calendar
import matplotlib.pyplot as plt
import sys
sys.path.append('../')
from Modules.HistoricRecharge import HistoricRecharge
from Modules.SetFonts import SetFonts
from Modules.HistoricRechargeDistribution import RandParams
import os
import statsmodels.api as sm
from sklearn.metrics import r2_score
import matplotlib.dates as mdates


#Currently there is an issue with numpy and python https://stackoverflow.com/questions/40659212/futurewarning-elementwise-comparison-failed-returning-scalar-but-in-the-futur
#Supressing future warnings, so I don't get a bunch of warning messages
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)


def NOAAReg(PredictionMonth, PredictionDay, StopMonth=0):
    if StopMonth == 0:
        StopMonth = PredictionMonth + 4
    #Find all the first forecasts for the given month in each year
    AllFiles = os.listdir('..//Data//120 Day Outlook/')
    #Search index
    AllFiles = [file for file in AllFiles if '.csv' in file]
    AllFilesIdx = [int(file[:4])*365+int(file[4:6])*30+int(file[6:8]) for file in AllFiles]
    files = []
    for year in np.arange(2003, 2020):
        FileMatch = year*365+PredictionMonth*30+PredictionDay
        FileIdx = abs(np.array(AllFilesIdx)-FileMatch).argmin()
        if AllFilesIdx[FileIdx]-FileMatch <= 7:
            files.append(AllFiles[FileIdx])


    #Load files and determine how much historic recharge could have occurred
    RechargePot_Master = pd.read_excel('..//Data//WaterRightsV2.xlsx', sheet_name='RechargeReductions')
    RechargePot_Master.index = pd.to_datetime(RechargePot_Master.Date)

    RechargeCaps_Master = pd.read_excel('..//Data//RechargeCells.xlsx', sheet_name='RechargeCaps_2')
    RechargeCaps_Master.index = RechargeCaps_Master['Site']

    Params = pd.read_excel('..//Data//RechargeCells.xlsx', sheet_name='UptimeAssumptions')
    
    Uptime = pd.read_excel('..//Data//RechargeCells.xlsx', sheet_name='Uptime')

    

    UptimeCalc = RandParams(Params, Uptime)
    

    RechargeCaps_Master.loc['MP29',  ['Deep Winter', 'Winter-Spring', 'Spring', 'Fall', 'Fall-Winter']] += 500
    RechargeCaps_Master.loc['WLSNCYN', ['Deep Winter', 'Winter-Spring', 'Spring', 'Irrigation', 'DeepIrrigation', 'Fall', 'Fall-Winter']] += 100
    RechargeCaps_Master.loc['NSCC', ['Spring','Fall']] += 300

    
    Recharge = HistoricRecharge(RechargePot_Master, RechargeCaps_Master, [0], UptimeCalc, 
                                datetime(1992,11,1), datetime(2019,7,1), '', 1).sum(axis=1)
    



    #Setup data storage format
    Acc = pd.DataFrame(index=np.arange(2004, 2021), columns=['MAFF'], dtype=np.float64)



    for file in files:
        date = datetime.strptime(file[:-4], '%Y%m%d')

        #Recharge season it typically defined as starting in August, but the recharge year is defined as the next year
        if date.month > 7:
            year = date.year+1
        else:
            year = date.year

        #Import predictions and clean up data
        Prediction = pd.read_csv('..//Data//120 Day Outlook//{}'.format(file), index_col=0, parse_dates=True)
        Prediction.columns = [col.strip() for col in Prediction.columns]

        #Remove leap days, they cause a bunch of issues further down the line
        if calendar.isleap(year):
            Prediction = Prediction[Prediction.index != datetime(year, 2, 29)]

        #This gives us the actual historical American Falls fill
        Inputs = pd.read_excel('..//Data//Inputs.xlsx', index_col=0, parse_dates=True, sheet_name='Flows')
        Inputs = Inputs.fillna(0)


        #Find the American Falls prediction. They changed the naming scheme a couple of times
        col = [col for col in Prediction.columns if 'AMERICAN FALLS' in col]
        UVPrediction = Prediction[col]
        UVPrediction = UVPrediction[UVPrediction[col] != ' ']
        
        UVPrediction = UVPrediction.astype(float)

        #Earlier predictions are less than 120 days, need to scale up to 120 days of newer predictions
        if len(UVPrediction) < 120:
            UVPrediction *= 120/len(UVPrediction)


        #Take the fill rate in CFS and convert to Acre-ft and add to the current reservoir capacity. Lastly convert to a % fill
        AmfFill = ((UVPrediction.cumsum()*1.98+Inputs.loc[date, 'amf_af'])/1672590*100)

        #Pick the month you want to stop the forecast at. I picked March for the October forecast and May for the Feb forecast
        AmfFill = AmfFill[(AmfFill.index.month < StopMonth) | (AmfFill.index.year != year)]

        #The last fill % is used in the later regressions
        Acc.loc[year, 'MAFF'] = AmfFill.iloc[-1].values[0]


        #Determine how much recharge occured before the forecast date
        Acc.loc[year, 'Previous Recharge'] = Recharge.loc[(Recharge.index < date) &
               (Recharge.index > datetime(year-1, 8,1))].sum().sum()*1.98


        #Total recharge for the season
        Acc.loc[year, 'Total Recharge'] = Recharge.loc[(Recharge.index>datetime(year-1, 8,1)) & (Recharge.index<datetime(year, 8,1))].sum().sum()*1.98


    Acc = Acc.astype(float)
    return Acc

if __name__ == '__main__':
    Year = 'SingleRegression'
    
    if Year == 'SingleRegression':
        month = 3
        day = 9
        Acc = NOAAReg(month, day, 5)
        
        Reg = Acc[:-1].dropna()
        
        fig, ax = plt.subplots()
        
        #Use regression to relate AMF to recharge for rest of season. Then add to recharge that has already occurred to predict total annual recharge
        X = sm.add_constant(Reg['MAFF'].values)
        lm = sm.OLS(Reg['Total Recharge']-Reg['Previous Recharge'], X)
        model = lm.fit()
        Reg['Prediction'] = Reg['Previous Recharge'] + model.fittedvalues
        ax.scatter(Reg['Total Recharge'], Reg['Prediction'])
        
        for year in Reg.index:
            ax.text(Reg['Total Recharge'].loc[year], Reg['Prediction'].loc[year], str(year))
         
        ax.set_xlabel('Total Theoretical Recharge (Acre-ft)')
        ax.set_ylabel('Predicted Total Theoretical Recharge (Acre-ft)')
        xax = ax.get_xlim()
        yax = ax.get_ylim()
        plt.title('Prediction for '+str(month)+'/'+str(day))
        plt.plot([xax[0], xax[1]], [yax[0], yax[1]])
        ax.text(75000, 500000, 'Recharge = [Previous Recharge] + {} * [Final American Falls Fill] + {}'.format(int(model.params['x1']), int(model.params['const'])))
        ax.text(75000, 470000, 'R$^2$ = '+str(np.round(r2_score(Reg['Total Recharge'], Reg['Prediction']),2)))
        print('Recharge = [Previous Recharge] + {} * [Final American Falls Fill] + {}'.format(int(model.params['x1']), int(model.params['const'])))
        print('R^2 = '+str(np.round(r2_score(Reg['Total Recharge'], Reg['Prediction']),2)))
    elif Year == 'FullRegression':
        Scores = []
        for month in [10, 11, 12, 1, 2, 3, 4]:
            for day in np.arange(1,30,7):
                Acc = NOAAReg(month, day, 5)
                Reg = Acc[:-1].dropna()
                X = sm.add_constant(Reg['MAFF'].values)
                lm = sm.OLS(Reg['Total Recharge']-Reg['Previous Recharge'], X)
                model = lm.fit()
                Reg['Prediction'] = Reg['Previous Recharge'] + model.fittedvalues
                score = np.round(r2_score(Reg['Total Recharge'], Reg['Prediction']),2)
                print([month, day, score])
                Scores.append([month, day, score, model.params['x1'], model.params['const']])
        
        Scores = np.array(Scores)
        SetFonts()
        fig, ax = plt.subplots()
        Year = [1999 if month>8 else 2000 for month in Scores[:,0]]
        Dates = [datetime(year, int(month), int(day)) for year, month, day in zip(Year, Scores[:,0], Scores[:,1])]
        ax.plot(Dates, Scores[:,2])
        myFmt = mdates.DateFormatter('%b-%d')
        ax.xaxis.set_major_formatter(myFmt)
        ax.set_ylabel('R$^2$ Score')
