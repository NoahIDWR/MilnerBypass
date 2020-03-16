# -*- coding: utf-8 -*-
"""

Parameters: 
    WRSheet - Dataframe containing WR availibility information. Daily date as index and two columns:
    1) [Milner] Flow at Milner and 2) [TotalUpperRecharge] Available recharge above Minidoka
    
"""


from datetime import datetime
from datetime import timedelta
import pandas as pd
import numpy as np




def HistoricRecharge(RechargePot, RechargeCaps, MilnerCap, Downtime, StartDate, EndDate, freq, n):
    
 
    RechargePot = RechargePot[(RechargePot.index >= StartDate) & (RechargePot.index <= EndDate)]
    
    
    #If MilnerCap is one value use as constant, otherwise use time series of Milner Bypass
    if len(MilnerCap)>1:
        RechargePot.loc[:, 'Milner'] = [max(flow-cap, 0) for flow, cap in zip(RechargePot['Milner'], MilnerCap)]
    else:
        RechargePot.loc[:, 'Milner'] = [max(flow-MilnerCap[0], 0) for flow in RechargePot['Milner']]
    
          
    

    
    
    #Define the date periods
    DateCode = RechargePot.index.month.values+RechargePot.index.day.values/100
    DeepWinter = (DateCode <= 1.31) | (DateCode >= 12.15)
    WinterSpring = (DateCode >= 2.01) & (DateCode < 3.01)
    Spring = (DateCode >= 3.01) & (DateCode <= 4.15)
    Irrigation = (DateCode >= 4.16) & (DateCode <= 6.30)
    DeepIrrigation = (DateCode >= 7.01) & (DateCode <= 9.30)
    Fall = (DateCode >= 10.01) & (DateCode <= 10.31)
    FallWinter = (DateCode >= 11.01) & (DateCode <= 12.14)
    
    
    RechargeCapsDaily = pd.DataFrame(columns=RechargeCaps.index, index=pd.date_range(StartDate, EndDate))
    RechargeCapsDaily.loc[DeepWinter,:]=np.tile(RechargeCaps['Deep Winter'], (len(RechargeCapsDaily.loc[DeepWinter,:]), 1))
    RechargeCapsDaily.loc[WinterSpring,:]=np.tile(RechargeCaps['Winter-Spring'], (len(RechargeCapsDaily.loc[WinterSpring,:]), 1))
    RechargeCapsDaily.loc[Spring,:]=np.tile(RechargeCaps['Spring'], (len(RechargeCapsDaily.loc[Spring,:]), 1))
    RechargeCapsDaily.loc[Irrigation,:]=np.tile(RechargeCaps['Irrigation'], (len(RechargeCapsDaily.loc[Irrigation,:]), 1))
    RechargeCapsDaily.loc[DeepIrrigation,:]=np.tile(RechargeCaps['DeepIrrigation'], (len(RechargeCapsDaily.loc[DeepIrrigation,:]), 1))
    RechargeCapsDaily.loc[Fall,:]=np.tile(RechargeCaps['Fall'], (len(RechargeCapsDaily.loc[Fall,:]), 1))
    RechargeCapsDaily.loc[FallWinter,:]=np.tile(RechargeCaps['Fall-Winter'], (len(RechargeCapsDaily.loc[FallWinter,:]), 1))
    
    

    RechargeCapUptime = pd.DataFrame(columns=RechargeCaps.index, index=pd.date_range(StartDate, EndDate))
    RechargeCapUptime.loc[DeepWinter,:]=np.tile(Downtime['Deep Winter'], (len(RechargeCapsDaily.loc[DeepWinter,:]), 1))
    RechargeCapUptime.loc[WinterSpring,:]=np.tile(Downtime['Winter-Spring'], (len(RechargeCapsDaily.loc[WinterSpring,:]), 1))
    RechargeCapUptime.loc[Spring,:]=np.tile(Downtime['Spring'], (len(RechargeCapsDaily.loc[Spring,:]), 1))
    RechargeCapUptime.loc[Irrigation,:]=np.tile(Downtime['Irrigation'], (len(RechargeCapsDaily.loc[Irrigation,:]), 1))
    RechargeCapUptime.loc[DeepIrrigation,:]=np.tile(Downtime['DeepIrrigation'], (len(RechargeCapsDaily.loc[DeepIrrigation,:]), 1))
    RechargeCapUptime.loc[Fall,:]=np.tile(Downtime['Fall'], (len(RechargeCapsDaily.loc[Fall,:]), 1))
    RechargeCapUptime.loc[FallWinter,:]=np.tile(Downtime['Fall-Winter'], (len(RechargeCapsDaily.loc[FallWinter,:]), 1))

    RechargeCapsRand = RechargeCapsDaily.copy(deep=True)

    RechargeSum = pd.DataFrame(index=RechargePot.index, columns = RechargeCaps['Site'])

    for i in range(n):
        #Randomly turn off canals based on uptimes
        Recharge = pd.DataFrame(index=RechargePot.index, columns = RechargeCaps['Site'])
        Uptime = np.random.random(RechargeCapUptime.shape)>RechargeCapUptime
        RechargeCapsRand = RechargeCapsDaily.copy(deep=True)
        RechargePotRand = RechargePot.copy(deep=True)
        RechargeCapsRand[Uptime] = 0
    
        #Go through each site and subtract that site from the total potential recharge for the Upper and Lower Valley for each time period 
        for site,valley in zip(RechargeCaps['Site'],RechargeCaps['Valley']):
            if valley=='Upper':
                #For each time period, take the available flow that is below the site capacity and add that to the recharge done
                Recharge.loc[:, site] = pd.concat([RechargePotRand['TotalUpperRecharge'], RechargeCapsRand[site]], axis=1).min(axis=1)            
                RechargePotRand.loc[:,'TotalUpperRecharge'] -= Recharge[site].values
                #Need to also subtract Upper Valley reductions from Lower Valley
                RechargePotRand.loc[:,'Milner'] -= Recharge[site].values
                
                
        for site,valley in zip(RechargeCaps['Site'],RechargeCaps['Valley']):
            if valley=='Lower':
                #Same as above, but for Lower Valley
                Recharge.loc[:, site] = pd.concat([RechargePotRand['Milner'], RechargeCapsRand[site]], axis=1).min(axis=1)
                
                #Subtract this site's recharge from the total potential recharge
                RechargePotRand.loc[:,'Milner'] -= Recharge[site]

        RechargeSum = pd.concat([RechargeSum, Recharge], axis=1)
        
        
    Recharge = RechargeSum.groupby(RechargeSum.columns, axis=1).sum()/n
     
     
    #If flag active, recharge will be returned as the annual recharge in Acre-ft for each water year
    if freq == 'Y':
        Recharge.index = Recharge.index+timedelta(days=61)
        Recharge = Recharge.resample('1Y').sum().sum(axis=1)*1.98
    
    return Recharge


if __name__ == '__main__':
    #For testing purposes

    #Pull recharge availability and capacity information from spreadsheets
    RechargePot_Master = pd.read_excel('..//WaterRightsV2.xlsx', sheet_name='RechargeReductions')
    RechargePot_Master.index = pd.to_datetime(RechargePot_Master.Date)
    
    RechargeCaps_Master = pd.read_excel('..//RechargeCells.xlsx',sheet_name='RechargeCaps_2')
    RechargeCaps_Master.index = RechargeCaps_Master['Site']
    
    Downtime_Master = pd.read_excel('..//RechargeCells.xlsx',sheet_name='Uptime')
    Downtime_Master.index = Downtime_Master['Site']
    
    Uptime = pd.read_excel('..//RechargeCells.xlsx', sheet_name='Uptime')
    
    Params = pd.read_excel('..//RechargeCells.xlsx', sheet_name='UptimeAssumptions')
    
    
    UptimeCalc = RandParams(Params, Uptime)
    
    Recharge = HistoricRecharge(RechargePot_Master, RechargeCaps_Master, [0], UptimeCalc, datetime(1992,11,1), datetime(2019,7,1), '', 5)
    MeanRecharge = Recharge[-20:].mean()