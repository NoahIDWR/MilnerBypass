# -*- coding: utf-8 -*-
"""
Created on Mon Dec  2 11:03:41 2019

@author: NStewart-maddox
"""

import pandas as pd
from datetime import datetime, timedelta


def NOAAWebGrab(date, Destination):
    try:
        dateStr = date.strftime('%Y%m%d')
        df = pd.read_csv('https://www.nwrfc.noaa.gov/stp/stp_fmt.cgi?date={}'.format(dateStr), skiprows=2, index_col=1)
        df[' PE'] = [str(PE).strip() for PE in df[' PE']]
        df = df[(df[' PE']=='QI') | (df[' PE']=='QR')]
        df = df.transpose()
        dates = [col for col in df.index if '-' in col]
        df = df.loc[dates]
        
        
        FirstDate = datetime(date.year, int(dates[0][-5:-3]),int(dates[0][-2:]))
        df.index = [FirstDate+timedelta(days=i) for i, date in enumerate(df.index)]
        df.to_csv(Destination+dateStr+'.csv')
    
    except ValueError:
        print('Not Date ')
    except IndexError:
        NOAAWebGrab(date+timedelta(days=1), Destination)