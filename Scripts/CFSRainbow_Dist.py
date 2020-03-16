# -*- coding: utf-8 -*-
"""
Created on Tue Jun 25 10:36:26 2019

@author: NStewart-maddox
"""


import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
import seaborn as sns
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Rectangle
import sys
sys.path.append('../')
from Modules.HistoricRechargeDistribution import RechargeDistribution
    


def RechargeCapacity(Valley, DecJanMask):
    #Pull recharge availability and capacity information from spreadsheets
    RechargePot_Master = pd.read_excel('..//Data//WaterRightsV2.xlsx', sheet_name='RechargeReductions')
    RechargePot_Master.index = pd.to_datetime(RechargePot_Master.Date)
    
    RechargeCaps_Master = pd.read_excel('..//Data//RechargeCells.xlsx',sheet_name='RechargeCaps_2')
    RechargeCaps_Master.index = RechargeCaps_Master['Site']
    
    Params = pd.read_excel('..//Data//RechargeCells.xlsx', sheet_name='UptimeAssumptions')
    
    Uptime = pd.read_excel('..//Data//RechargeCells.xlsx', sheet_name='Uptime')
    
    
    
    #Create matrix that will store additional required capacity
    CapacityMatrix = np.zeros((6,6))
    
    
    for i, MilnerCap in enumerate(np.arange(0,600,100)):
        MeanDist = []
        for j, Confidence in enumerate(np.arange(0.7,0.2,-0.1)):
            CapInc = 0
            Exceedence = 0
            #Keep increasing the additional capacity until either the average hits 250 KAF or the capacity increase is more than 1000 CFS
            while (Exceedence<Confidence) and (CapInc<1000):
                
                #First run needs to generate all the possible probability distributions for a given bypass
                if Confidence == 0.7:
                    #Optional argument if you only want to apply Milner Bypass to Dec/Jan 
                    if DecJanMask:
                        DateCode = RechargePot_Master.index.month.values+RechargePot_Master.index.day.values/100
                        mask = (DateCode <= 2.15) | (DateCode >= 12.01)
                        MilnerCapSeries = pd.Series(index=RechargePot_Master.index)
                        MilnerCapSeries[mask] = MilnerCap
                        MilnerCapSeries[~mask] = 0
                    else:
                        MilnerCapSeries = [MilnerCap]
                    
                    
                    #Make a copy of the recharge capacity for later modification
                    RechargeCaps = RechargeCaps_Master.copy(deep=True)
                    
                    
#                    RechargeCaps.loc['MP29',  ['Deep Winter', 'Winter-Spring', 'Spring', 'Fall', 'Fall-Winter']] += 200
                    
                    #Add extra capacity to the Upper or Lower Valley. I used AB and MP29, because they were already at zero
                    if Valley=='Upper':
                        RechargeCaps.loc['ASCC',  ['Deep Winter', 'Winter-Spring', 'Spring', 'Irrigation', 'DeepIrrigation', 'Fall', 'Fall-Winter']] += CapInc
                    elif Valley=='Lower': 
                        RechargeCaps.loc['AB', ['Deep Winter', 'Winter-Spring', 'Spring', 'Irrigation', 'DeepIrrigation', 'Fall', 'Fall-Winter']] += CapInc
                    
                    #Determine the distribution of historical recharge amounts
                    Recharge = RechargeDistribution(RechargePot_Master, RechargeCaps, Uptime, Params, MilnerCapSeries, 25)
                    RechargeMean = np.array([r[-20:].mean() for r in Recharge])
                    MeanDist.append(RechargeMean)
                else:
                    RechargeMean = MeanDist[int(CapInc/50)]
                
                Exceedence = len(RechargeMean[RechargeMean>250000])/len(RechargeMean)

                
                #If average still below 250KAF add an extra 50 CFS to the capacity
                if Exceedence<Confidence:
                    CapInc += 50
                    
            #Write required additional capacity to matrix
            CapacityMatrix[j,i] = CapInc
            
    return CapacityMatrix

#Determine how much additional capacity is required in the Upper and Lower Valley under different bypass and uptime scenarios
LVCap = RechargeCapacity('Lower', True)


UVCap = RechargeCapacity('Upper', True)

LVCap = LVCap[:5,:]
UVCap = UVCap[:5,:]

plt.style.use('fivethirtyeight')


#Formatting uptime labels
UsableLabels = ['{}%'.format(int(np.round(100-Downtime*100,0))) for Downtime in np.arange(0.3,0.8,0.1)]

#Create Dataframe for use with sns.heatmap
LVCap = pd.DataFrame(data = LVCap, columns = np.arange(0,600,100), index = UsableLabels)


norm=plt.Normalize(0,1000)
cmap = LinearSegmentedColormap.from_list("", ["green","orange","red"])


#Plot heatmap based on LV caps
ax = sns.heatmap(LVCap.astype(np.int64), cmap=cmap, annot=True, fmt='d', cbar=False)


#Add any indivual cells you may want to remove for asthetic purposes
Cut = []

for x,t in enumerate(ax.texts):
    i = int(x/6)
    j = x % 6
    Cap = LVCap.iloc[i,j]
    if ([i,j] in Cut) or (Cap==1000) or (Cap==0):
        t.set_text('')
    else:
        ax.add_patch(Rectangle((i, j), 1, 1, fill=False, edgecolor='black', lw=1))
        
        t.set_text('{} / {}'.format(int(LVCap.iloc[i,j]),int(UVCap[i,j])))

#For some reason I was struggling hard with getting the formatting to work for the last column, so I just hardcoded it here at the end
for i in range(5):
    for j in range(6):
        ax.add_patch(Rectangle((j, i), 1, 1, fill=False, edgecolor='black', lw=1))

bottom, top = ax.get_ylim()
ax.set_ylim(bottom + 0.5, top - 0.5)
ax.set_xlabel('Milner Bypass Cap (CFS)')
ax.set_ylabel('Confidence Level %')
