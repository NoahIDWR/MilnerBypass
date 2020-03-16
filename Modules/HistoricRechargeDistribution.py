import numpy as np
import sys
sys.path.append('../')
from Modules.HistoricRecharge import HistoricRecharge
from datetime import datetime

def SelectStr(Site):
    return 'Params.loc[Params.Parameter=="{}", "Uptime"].values[0]'.format(Site)


def find_all(a_str, sub):
    start = 0
    while True:
        start = a_str.find(sub, start)
        if start == -1: return
        yield start
        start += len(sub) 


#Generates a random set of paramters by altering the input parameters by +/- 20%
def RandParams(Params_Master, Uptime):

    Params = Params_Master.copy(deep=True)
    
    Params.loc[:, 'Uptime'] += np.random.rand(len(Params))/2.5-0.2
    
    
    UptimeCalc = Uptime.copy(deep=True)
    
    for i in range(Uptime.shape[0]):
        for j in np.arange(2, Uptime.shape[1]):
            CalcStr = Uptime.iloc[i, j]
            Stars = list(find_all(CalcStr, '*'))
            #I know this is ugly hardcoding, but I was struggling to implement this correctly
            if len(Stars)==0:
                Calc = SelectStr(CalcStr)
            elif len(Stars)==1:
                Calc = SelectStr(CalcStr[:Stars[0]])
                Calc += '*' + SelectStr(CalcStr[Stars[0]+1:])
            elif len(Stars)==2:
                Calc = SelectStr(CalcStr[:Stars[0]])
                Calc += '*' + SelectStr(CalcStr[Stars[0]+1:Stars[1]])
                Calc += '*' + SelectStr(CalcStr[Stars[1]+1:])
            
            UptimeCalc.iloc[i, j] = eval(Calc)
        
    return UptimeCalc


#Inputs
    #RechargePot_Master - Recharge Potential from WaterRightsV2.xlsx
    #RechargeCaps_Master - Recharge capacity from RechargeCells.xlsx
    #Uptime - Uptime calculations from RechargeCells.xlsx
    #Params - Assumed uptime parameters
    #Bypass - How much should flow past Milner
    #n - Number of times the analyses should be performed. 
        #I've found 100 runs seems to work reasonably well. However, for some analysis more runs may be required.
def RechargeDistribution(RechargePot_Master, RechargeCaps_Master, Uptime, Params, Bypass, n):
    
    MeanRecharge = []
    for i in range(n):
        UptimeCalc = RandParams(Params, Uptime)
        Recharge = HistoricRecharge(RechargePot_Master, RechargeCaps_Master, Bypass, UptimeCalc, datetime(1991,11,1), datetime(2019,7,1), 'Y', 1)
        MeanRecharge.append(Recharge)
    
    return MeanRecharge