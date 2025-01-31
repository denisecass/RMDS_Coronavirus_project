#!/usr/bin/env python
# coding: utf-8

# # Update CDC Functions

# The purpose of this notebook is as follows:<br>
# 1. Create a function that grabs data from MongoDB (COVID19-DB/CDC-TimeSeries table)
# 
# 2. Create a function that takes in the dataset CDC-TimeSeries from MongoDB and spits out country, date, total_num_infections, total_num_deaths. 
# 
# 3. Create a function that takes in CDC-TimeSeries from MongoDB and spits out country, days_since_first_infection, total_num_infections, total_num_deaths.

import argparse
import pandas as pd
import numpy as np
import pymongo
from pymongo import MongoClient
import matplotlib.pyplot as plt
from datetime import datetime
import warnings
warnings.filterwarnings("ignore")



# # Update CDC Functions

# The purpose of this notebook is as follows:<br>
# 1. Create a function that grabs data from MongoDB (COVID19-DB/CDC-TimeSeries table)
# 
# 2. Create a function that takes in the dataset CDC-TimeSeries from MongoDB and spits out country, date, total_num_infections, total_num_deaths. 
# 
# 3. Create a function that takes in CDC-TimeSeries from MongoDB and spits out country, days_since_first_infection, total_num_infections, total_num_deaths.


def mongodb_import(collection_name:str):
    """
    Import the database from MongoDB and put it into a dataframe. 
    The exact name of the database has to be know to call the function.
    Currently, the collections in the MongoDB are as follows: 'CDC-TimeSeries', 'DXY-TimeSeries', 'World_population', 'counties'
    
    """
    import pymongo
    from pymongo import MongoClient
    import pandas as pd
    
    auth = "mongodb://analyst:grmds@3.101.18.8/COVID19-DB"
    db_name = 'COVID19-DB'
    
    client = pymongo.MongoClient(auth) # defaults to port 27017
    db = client[db_name]
    cdc_ts = pd.DataFrame(list(db[collection_name].find({})))
    return cdc_ts


def tracker_update():
    """
    The purpose of this function is as follows:
    1. Import data from the CDC-TimeSeries table using the function above
    2. Based on the data, returns 4 columns: country, date, num_infections, and num_deaths
    
    """ 
    import pandas as pd
    import numpy as np
    import pymongo
    from pymongo import MongoClient
    import matplotlib.pyplot as plt
    
    df = mongodb_import('CDC-TimeSeries')
    df = df.loc[:,['Country/Region','Date','Confirmed','Death']].fillna(0)
    df['Confirmed'] = df['Confirmed'].astype(int)
    df['Death'] = df['Death'].astype(int)

    tracker = pd.DataFrame(columns=['num_infections', 'num_deaths'])

    tracker['num_infections'] = df.groupby(['Country/Region','Date'])['Confirmed'].sum()   
    tracker['num_deaths'] = df.groupby(['Country/Region','Date'])['Death'].sum()    
        
    tracker.reset_index(inplace= True)
    tracker.rename(columns={"Country/Region": "country", "Date": "date"}, inplace = True)
    
    # I realized the original dataset was in cumulative terms already --> had to un-cumulate
    tracker['num_infections'] = tracker.groupby(['country'])['num_infections'].diff().fillna(0)
    tracker['num_deaths'] = tracker.groupby(['country'])['num_deaths'].diff().fillna(0)
    
    return tracker


def cml_tracker_update():  
    """
    The purpose of this function is as follows:
    1. Call the tracker_update() function created above
    2. Create "days_since_first_infection" column that shows how many days since the first occurrence of infection
        - ex) -10 means 10 days until the first infection and 10 means 10 days since the first infection
    3. Create 2 new columns (total_num_infections and total_num_deaths) that calculates the cumulated sum for each category
    
    Note that this function may not be efficient as it can be. If anyone else on the team has a better idea, please feel free to update it!
    """
    import pandas as pd
    import numpy as np
    import pymongo
    from pymongo import MongoClient
    import matplotlib.pyplot as plt
    

    tracker = tracker_update()
    from datetime import datetime, timedelta
    tracker['days_since_first_infection'] = ""

    country = []
    first_infection = []
    for name, group in tracker.groupby('country'):
        first = next(x for x, val in enumerate(group.num_infections) if val > 0)
        first_date = group.iloc[first,1] 
        first_infection.append(first_date)
        country.append(name)

    for x in range(0,len(country)):
        for i in range(0,len(tracker)):
            infection_date = first_infection[x]
            if tracker.iloc[i,0] == country[x] and tracker.iloc[i,1] == infection_date:
                tracker.iloc[i,4] = 1
            elif tracker.iloc[i,0] == country[x] and tracker.iloc[i,1] >= infection_date:
                tracker.iloc[i,4] = tracker.iloc[i-1,4] + 1
            elif tracker.iloc[i,0] == country[x] and tracker.iloc[i,1] < infection_date:
                tracker.iloc[i,4] = (tracker.iloc[i,1]-infection_date).days

    tracker["total_num_infections"] = tracker.groupby('country')['num_infections'].cumsum()
    tracker["total_num_deaths"] = tracker.groupby('country')['num_deaths'].cumsum()
    
    
    tracker_cml = tracker.drop(['num_infections','num_deaths'], axis=1)
    return tracker_cml



def infection_plot(country_list):
    """
    This function creates a visualization that presents date as the x-axis and number of infections on the y-axis.
    User can put any country that he/she wants to compare in the list as shown below.
    The function will plot based on this selectionof countries.
    """
    import pandas as pd
    import matplotlib.pyplot as plt
    
    
    tracker = tracker_update()
    
    plt.figure(figsize = (16,8))
    for x in country_list:
        country = tracker[tracker.country == x]
        plt.plot("date", "num_infections", data = country, label = x)
        plt.title("Number of Infections by Country", size = 15)
        plt.xlabel("Date")
        plt.ylabel("Number of Infections")
        plt.legend(loc=2)
    plt.grid()
    plt.show()
    
    
def death_plot(country_list):
    """
    This function creates a visualization that presents date as the x-axis and number of deaths on the y-axis.
    User can put any country that he/she wants to compare in the list as shown below.
    The function will plot based on this selectionof countries.
    """
    import pandas as pd
    import matplotlib.pyplot as plt
    
    tracker = tracker_update()
    
    plt.figure(figsize = (16,8))
    for x in country_list:
        country = tracker[tracker.country == x]
        plt.plot("date", "num_deaths", data = country, label = x)
        plt.title("Number of Deaths by Country", size = 15)
        plt.xlabel("Date")
        plt.ylabel("Number of Deaths")
        plt.legend(loc=2)
    plt.grid()
    plt.show()
    

def cml_infection_plot(country_list):
    """
    This function creates a visualization that presents Days Since the First Infection as the x-axis and cumulative number of infections on the y-axis.
    User can put any country that he/she wants to compare in the list as shown below.
    The function will plot based on this selectionof countries.
    Note that the function calls another function defined above, which may take some time. 
    """
    import pandas as pd
    import matplotlib.pyplot as plt
    
    cml_tracker = cml_tracker_update()
    plt.figure(figsize = (16,8))
    for x in country_list:
        country = cml_tracker[cml_tracker.country == x]
        plt.plot("days_since_first_infection", "total_num_infections", data = country, label = x)
        plt.title("Cumulative Number of Infections by Country", size = 15)
        plt.xlabel("Days Since 1st Infection")
        plt.ylabel("Cumulative Number of Infections")
        plt.legend(loc=2)
    plt.grid()
    plt.show()
    

def cml_death_plot(country_list):
    """
    This function creates a visualization that presents Days Since the First Infection as the x-axis and cumulative number of deaths on the y-axis.
    User can put any country that he/she wants to compare in the list as shown below.
    The function will plot based on this selectionof countries.
    Note that the function calls another function defined above, which may take some time. 
    """
    import pandas as pd
    import matplotlib.pyplot as plt

    cml_tracker = cml_tracker_update()
    plt.figure(figsize = (16,8))
    for x in country_list:
        country = cml_tracker[cml_tracker.country == x]
        plt.plot("days_since_first_infection", "total_num_deaths", data = country, label = x)
        plt.title("Cumulative Number of Deaths by Country", size = 15)
        plt.xlabel("Days Since 1st Infection")
        plt.ylabel("Cumulative Number of Deaths")
        plt.legend(loc=2)
    plt.grid()
    plt.show()
    

def days_taken_infection(infection):
    
    """
    Present how many days it took to reach certain number of infections that is provided in the function
    The output dataframe only shows the countries with infection # more than the number provided in ascending order.
    
    """
    import pandas as pd
    
    output = pd.DataFrame()
    cml_tracker = cml_tracker_update()
    for name, group in cml_tracker.groupby('country'):
        country_name = cml_tracker[cml_tracker.country == name]
        result = country_name.loc[cml_tracker.total_num_infections >= infection, ['country','days_since_first_infection']].min()
        output = output.append(result, ignore_index = True)

    output.dropna(inplace=True)
    output.sort_values(by = 'days_since_first_infection', inplace=True)
    return output


def days_taken_death(death):
    
    """
    Present how many days it took to reach certain number of deaths that is provided in the function
    The output dataframe only shows the countries with deaths # more than the number provided in ascending order.
    
    """
    
    import pandas as pd
    output = pd.DataFrame()
    cml_tracker = cml_tracker_update()
    for name, group in cml_tracker.groupby('country'):
        country_name = cml_tracker[cml_tracker.country == name]
        result = country_name.loc[cml_tracker.total_num_deaths >= death, ['country','days_since_first_infection']].min()
        output = output.append(result, ignore_index = True)

    output.dropna(inplace=True)
    output.sort_values(by = 'days_since_first_infection', inplace=True)
    return output


if __name__ == '__main__':

    mongodb_import('CDC-TimeSeries')
    tracker_update()
    cml_tracker_update()
    