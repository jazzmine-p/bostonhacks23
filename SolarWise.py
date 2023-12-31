import streamlit as st
import pandas as pd
import numpy as np

import urllib.request
import sys

import pandas as pd
from sklearn.ensemble import AdaBoostRegressor
from sklearn.model_selection import train_test_split
from sklearn.ensemble import AdaBoostRegressor
from sklearn.tree import DecisionTreeRegressor

import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

# page config and header
st.set_page_config(page_title='SolarWise', page_icon='Solar Wise Logo.png', layout='wide')
col1, col2 = st.columns([0.1, 0.9], gap="small")
col1.image('Solar Wise Logo.png', use_column_width=True)
col2.title('SolarWise Energy Forecast')
col2.markdown('Enter your location for a 15 day solar panel production forecast')
# primary color = #427F13

forecast = []

def gen_link(loc):
    apikey = st.secrets["apikey"]

    apilink1 = 'https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/'
    apilink2 = '?unitGroup=metric&elements=name%2Cdatetime%2Ctemp%2Cdew%2Chumidity%2Cwindspeed%2Ccloudcover%2Cvisibility%2Csolarenergy&include=days%2Cstats%2Cstatsfcst%2Cremote%2Cobs%2Cfcst&key=' + apikey + '&contentType=csv'

    loc = loc.replace(' ', '%20')

    return apilink1 + loc + apilink2    # concatenate forecast api call link

def gen_data(link):
    try:         
        forecast = pd.read_csv(urllib.request.urlopen(link))        # parse api return into forecasts data format       
    except urllib.error.HTTPError as e:                             # check for errors in url fetch
        ErrorInfo= e.read().decode() 
        st.write('Error code: ', e.code, ErrorInfo)
        sys.exit()
    except  urllib.error.URLError as e:
        ErrorInfo= e.read().decode() 
        st.write('Error code: ', e.code,ErrorInfo)
        sys.exit()

    st.write('Solar energy production data for ' + '**' + forecast['name'][1]+ '**' + ':')     # write city name at top of page
    return forecast

def graph():
    col2.area_chart(forecast, x='Date', y='Predicted Solar Output (kW/hr)', color=(66, 127, 19, 150), height=562)   # graph results


def predict(vs_test):
    # read training data
    df = pd.read_csv("joined-weather-solar.csv")
    df = df.drop(columns=['Date','Station pressure', 'Unnamed: 0', 'Altimeter'])
    df = df.rename(columns={'Temperature':'temp',
                            'Dew point':'dew',
                            'Wind speed':'windspeed',
                            'Cloud coverage': 'cloudcover',
                            'Visibility': 'visibility',
                            'Solar energy': 'solarenergy',
                            'Relative humidity':'humidity'})
    X = df.drop(columns=['Site Performance Estimate'], axis=1)
    y = df['Site Performance Estimate']

    # Splitting the dfset into training and testing sets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=37)

    vs_test_df = vs_test    # for later use

    # Preprocess the data
    vs_test['Date'] = pd.to_datetime(vs_test['datetime'])
    vs_test = vs_test.drop(columns=['Date', 'name'])

    # Reorder column and MinMaxScaler
    vs_test = vs_test[['cloudcover', 'visibility', 'temp', 'dew', 'humidity', 'windspeed',
        'solarenergy']]

    # Predict using AdaBoosting based on DecisionTreeRegressor base tree
    base_tree = DecisionTreeRegressor(max_depth=5, random_state=37)
    base_tree.fit(X_train, y_train)
    
    # run adaboost
    final_ada = AdaBoostRegressor(base_estimator=base_tree, 
                                learning_rate=0.5, 
                                n_estimators=150,
                                random_state=37)
    result = final_ada.fit(X_train, y_train)

    # Final prediction
    vs_pred = result.predict(vs_test)

    vs_test_df = vs_test_df.join(pd.DataFrame(data=vs_pred, columns=['Predicted Solar Output (kW/hr)']))                                    # merge results into table
    col1.dataframe(vs_test_df.loc[:, ['Date', 'Predicted Solar Output (kW/hr)']], use_container_width=True, hide_index=True, height=562)    # display table

    return vs_test_df
  
# main process
loc = st.text_input('Location')                         # get location from user
if loc != '':
    link = gen_link(loc)                                # generate api link
    forecast = gen_data(link)                           # gather forecast data
    col1, col2 = st.columns([0.3, 0.7], gap="small")    # format page
    forecast = predict(forecast)                        # predict output
    graph()                                             # graph prediction
