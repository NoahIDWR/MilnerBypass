# -*- coding: utf-8 -*-
"""
Created on Thu Sep 19 09:15:24 2019
@author: NStewart-maddox
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import random
from matplotlib.colors import LinearSegmentedColormap
import seaborn as sns
import sys
sys.path.append('../')
from Modules.HistoricRechargeDistribution import RechargeDistribution
from Modules.SetFonts import SetFonts
from matplotlib.ticker import FuncFormatter
from matplotlib import gridspec

#Convert previously generated states into recharge quantities
def StateToAmount(Chain, Recharge, YearType):
    ChainVals = []
    for year in Chain:
        #Pick a random year that is of a similar type to randomly generated type
        i = np.random.randint(len(Recharge[YearType==year]))
        ChainVals.append(Recharge[YearType==year][i])
        
    return ChainVals

#Generate transitiion probabilities for different states
def MarkovProb():
    #Pull historic PDSI numbers
    df = pd.read_excel('..//Data//RechargeEstimatesActual.xlsx', index_col=0, sheet_name = 'Historic Droughts')
    
    #Hard coded transition states. Not pretty, but it works
    p_DP = 0    #Should add description
    p_DW = 0
    p_1W = 0
    p_1L = 0
    p_WP = 0
    p_WL = 0
    p_L1 = 0
    p_LD = 0
    D = 0
    W1 = 0
    WL = 0
    W = 0
    
    
    prev_state = 'Drought'
    
    #Use previous 20 years of climate data to determine transition probabilities. Need to revisit this idea
    for PDSI in df['Value'][:-20]:
        if prev_state=='Drought':
            D += 1
            if PDSI>0:
                p_DW += 1
                prev_state = '1stWet'
            else:
                p_DP += 1
                prev_state = 'Drought'
        
        elif prev_state=='1stWet':
            W1 += 1
            if PDSI<0:
                p_1L += 1
                prev_state = 'LastWet'
            else:
                p_1W += 1
                prev_state = 'Wet'
        elif prev_state == 'Wet':
            W += 1
            if PDSI<0:
                p_WL += 1
                prev_state = 'LastWet'
            else:
                p_WP += 1
                prev_state = 'Wet'
        elif prev_state == 'LastWet':
            WL += 1
            if PDSI<0:
                p_LD += 1
                prev_state = 'Drought'
            else:
                p_L1 += 1
                prev_state = '1stWet'

    
    
    p_DP /= D
    p_DW /= D
    p_1W /= W1
    p_1L /= W1
    p_WP /= W
    p_WL /= W
    p_L1 /= WL
    p_LD /= WL
    
    return [p_DP, p_DW, p_1W, p_1L, p_WP, p_WL, p_L1, p_LD]


#Recursively generate markov chain using transition probabilities
def markov_state(chain, prev_state, prob, i, thresh):
    i+=1
    p = random.random()
    [p_DP, p_DW, p_1W, p_1L, p_WP, p_WL, p_L1, p_LD] = prob
    
    if prev_state=='Drought':
        if p<p_DP:
            prev_state = 'Drought'
        else:
            prev_state = '1stWet'
    
    elif prev_state=='1stWet':
        if p<p_1L:
            prev_state = 'LastWet'
        else:
            prev_state = 'Wet'
    elif prev_state == 'Wet':
        if p<p_WL:
            prev_state = 'LastWet'
        else:
            prev_state = 'Wet'
    elif prev_state == 'LastWet':
        if p<p_LD:
            prev_state = 'Drought'
        else:
            prev_state = '1stWet'
            
    #Add determined state to existing chain        
    chain.append(prev_state)
    
    #If less than threshold, continue generating chain, otherwise return chain
    if i<thresh: 
        return markov_state(chain, prev_state, prob, i, thresh)
    else:
        return chain
    
#Visualize the chains for presentations
def plot_chain(PreRecharge, Chains):
    plt.style.use('fivethirtyeight')
    plt.figure() 
    #Create grid for plotting
    gs = gridspec.GridSpec(1, 2, width_ratios=[4, 1])
    ax1 = plt.subplot(gs[0])
    ax2 = plt.subplot(gs[1])
    #Plot historical real data
    ax1.set_xlim([2015, 2024])
    ax1.plot([2015, 2016, 2017, 2018, 2019], PreRecharge[:-1], color='dodgerblue')
    ax1.get_yaxis().set_major_formatter(FuncFormatter(lambda x, p: format(int(x), ',')))
    ax1.set_xticks(np.arange(2015, 2025))
    ax2.set_yticklabels('')
    ax2.set_xticklabels('')
    ax2.grid(False)
    ax1.set_ylabel('Annual Recharge (Acre-ft)')
    ax1.set_xlabel('Water Year')
    ax1.set_title('Natural Flow Recharge Exceedance Forecasting')
    ax1.plot([2015, 2016, 2017, 2018, 2019, 2020], PreRecharge, color='dodgerblue')
    #Plot hypothetical 2020
    ax1.scatter([2020], [PreRecharge[-1]], color='green', s=100, zorder=5)
    means = []
    #Plot first 100 traces and calculate distribution of means
    for i in range(30000):
        if i<100:
            ax1.plot([2020, 2021, 2022, 2023, 2024], np.concatenate(([PreRecharge[-1]], Chains[i])), color='gray', alpha=0.1)
        means.append(np.mean(np.concatenate((PreRecharge, Chains[i]))))

    ax1.plot([2015,2024], [250000, 250000], color='red')

    #Plot distribution of means
    ax2.hist(np.array(means), orientation="horizontal")
    ax2.set_ylim(ax1.get_ylim()[0], ax1.get_ylim()[1])
    ax2.plot([0,30000*0.25], [250000, 250000], color='red')
    ax2.text(0, 400000, 'Distribution of Possible \n 10 Year Averages in 2024', size=18)
    plt.tight_layout()
    
    #Plot exceedence graphs
    fig, ax = plt.subplots()
    exceedance = 1.-np.arange(1.,len(means) + 1.)/len(means)
    ax2 = ax.twiny()
    ax.grid(False)
    ax2.hist(np.array(means), orientation="horizontal")
    ax.plot(exceedance*100, np.sort(means), color='forestgreen')
    ax.set_zorder(1)
    ax.patch.set_visible(False)
    ax2.set_xticklabels('')
    ax.set_xlabel('Exceedence Probability %')
    ax.get_yaxis().set_major_formatter(FuncFormatter(lambda x, p: format(int(x), ',')))
    ax.set_ylabel('Possible 10 Year Average Annual Recharge (Acre-ft)')
    ax.set_xlim([0, 100])
    plt.tight_layout()

    

PreRecharge = [75475, 66897, 317714, 474901, 310133, 250000]

#Hard coded state types
YearType = pd.Series(['Drought', '1stWet', 'LastWet', 'FirstWet', 'Wet', 'Wet', 'Wet',
       'Wet', 'LastWet', 'Drought', 'Drought', 'Drought', 'Drought',
       '1stWet', 'Wet', 'LastWet', 'Drought', '1stWet', 'Wet', 'Wet',
       'LastWet', 'Drought', 'Drought', 'Drought', 'Drought', '1stWet',
       'Wet', 'Wet'])    

#Pull water availability data from excel sheet
RechargePot_Master = pd.read_excel('..//Data//WaterRightsV2.xlsx', sheet_name='RechargeReductions')
RechargePot_Master.index = pd.to_datetime(RechargePot_Master.Date)

#Recharge capacities
RechargeCaps_Master = pd.read_excel('..//Data//RechargeCells.xlsx',sheet_name='RechargeCaps_2')
RechargeCaps_Master.index = RechargeCaps_Master['Site']

Params = pd.read_excel('..//Data//RechargeCells.xlsx', sheet_name='UptimeAssumptions')

Uptime = pd.read_excel('..//Data//RechargeCells.xlsx', sheet_name='Uptime')


#The desired probability that the 10 year average will exceed 250KAF 
ExThresh = 0.75

#Determine historic recharge
Recharge = RechargeDistribution(RechargePot_Master, RechargeCaps_Master, Uptime, Params, [0], 100)
Recharge = np.percentile(np.array(Recharge), (1-ExThresh)*100, axis=0)


Chains = []

prob = MarkovProb()
    
#Generate 30,000 potential futures for Monte Carlo Analysis. Was picked to ensure convergence
#Not one chain, not 2 chainz, but 30,000 chains
for i in range(30000):
#    Chain = markov_state([], 'Wet', prob, 0, 5)
#    #Because you don't know what your next state will be, you need to skip a year
#    Chains.append(StateToAmount(Chain[1:], Recharge, YearType))
    
    #Pick random subsample from historical recharge data
    Chains.append(np.random.choice(Recharge, 4))


#These are all the previous 5 year averages used for the calculation
RechargeCaps = np.arange(225000,325000,25000)
    



ReqRecharge = []

for PrevRecharge in RechargeCaps:
    Exceedence = 0
    Recharge = 0
    
    #Loop through until exceedence passes exceedence threshold
    while (Exceedence<ExThresh) & (Recharge<750000):
        TotAvg = []
        #Loop through previously generated chains
        for Chain in Chains:
            #Determine possible 10 year average in 5 years from now
            #Use 5 year average then one year of possible recharge and 4 years of generated recharge
            Recharge10Yr = np.concatenate((np.zeros(5)+PrevRecharge, [Recharge], Chain))
            
            Yr10Avg = Recharge10Yr.mean()
            TotAvg.append(Yr10Avg)
            
        TotAvg = np.array(TotAvg)
        #Increase actual recharge by 5,000 Acre-ft. 
        Recharge += 5000
        #Find what percentage exceed 250,000 Acre-ft
        Exceedence = len(TotAvg[TotAvg>250000])/len(TotAvg)
    
    #Once exceedence exceeds threshold record
    ReqRecharge.append(Recharge)

ReqRecharge = np.array(ReqRecharge)

PredictedRecharge = np.arange(100000, 600000, 50000)
Bypass = np.zeros((len(RechargeCaps), len(PredictedRecharge)))
for i,Recharge in enumerate(PredictedRecharge):
    #Difference between predicted recharge and required recharge to exceed exceedence threshold can by used for bypass
    Bypass[:,i] = [max(flow,0) for flow in (Recharge - ReqRecharge)]
    

#Convert bypass to KAF
Bypass = np.array(Bypass/1000, dtype=int)

plt.figure()    

#Plot and format bypass flows
SetFonts()
norm=plt.Normalize(0,100)
cmap = LinearSegmentedColormap.from_list("", ["gray","orange","blue"])


ax = sns.heatmap(Bypass, cmap=cmap, annot=True, cbar=False, fmt='d', linewidths=.25)

ax.set_xticklabels([int(cap/1000) for cap in PredictedRecharge])
ax.set_xlabel('Predicted Total Annual Recharge (KAF)') 

ax.set_yticklabels([int(cap/1000) for cap in RechargeCaps])
ax.set_ylabel('Previous Five Year Average Recharge (KAF)')

bottom, top = ax.get_ylim()
ax.set_ylim(bottom + 0.5, top - 0.5)


for x,t in enumerate(ax.texts):
    if '0' == t.get_text():
        t.set_text('')