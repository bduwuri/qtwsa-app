#!/usr/bin/env python3


import math
import numpy as np
import pandas as pd
import dataretrieval.nwis as nwis
import pytz
from datetime import datetime
import geopandas as gpd
import time
from dash import dcc, html
import dash_bootstrap_components as dbc
import plotly.graph_objects as go

# typing imports
from typing import Dict, Union

# local imports
from logging_config import get_logger



# instantiate logger
logger = get_logger(__name__)


CFS_TO_CMS = 0.028316846592


def get_map_data(
    USGS_data_file: str = "static/data/usgs-gauges/gauges_global.shp"
) -> pd.DataFrame:
    """
    Collects the data required for the map component

    Parameters
    ----------
    gauges_data_file: str
            Path to Shapefile containing sites to populate on the map.
    Returns
    -------
    pandas.DataFrame
            A DataFrame containing the data for the map component
    """

    # load data
    usgs_df = pd.DataFrame(gpd.GeoDataFrame.from_file(USGS_data_file))
    usgs_df.drop(columns="geometry", inplace=True)
    print("usgs_df.shape:   .................   ", usgs_df.columns)
    return usgs_df


def get_dependency_color(value):
    try:
        # Convert the dependency value to a float.
        val = float(value)
    except (TypeError, ValueError):
       return "black" # default if conversion fails
    # Adjust thresholds as desired (here we assume value in 0-100):
    if val == 0:
        return "red"
    elif val == 1:
        return "lightgreen"
    elif val == 2:
        return "green"
    else:
        return "darkgreen"
    
def handle_click(
    gageid: str,
    model_regionalisation,
    model_spatial_feasibility,
    model_temporal_feasibility,
) :
    """
    Computes QTWSA measurments.

    Parameters
    ----------
    gageid: str
        USGS streamflow gage identifier
    model_regionalisation: Model Selected,
    model_spatial_feasibility: Model Selected,
    model_temporal_feasibility: Model Selected 
        

    Returns
    -------
    synthetic_qtwsa_data: Dict[str, pandas.Dataframe]
        discharge: List
            Predicted discharges or None
        spatial_discrepency: Value
            The group identifier (KGE groups, see paper)
        temporal_discrepency: Value 
            Number of months
    """
    dates = pd.read_csv("static/data/datesnumberfrombase_TWSA1.csv",usecols=range(2))
    allmodels_tasks = pd.read_csv(r"static/data/global_gauges_models.csv")
    TWSA_data = pd.read_csv(r"static/data/TWSA_gauges_global.csv")
    
    
    print(f"Callback triggered with models: {model_regionalisation}, {model_spatial_feasibility}, {model_temporal_feasibility}")
    

    comid = allmodels_tasks[allmodels_tasks['GAGEID'].astype('str')==str(gageid)].COMID.values[0]
    
    if not comid:
        comid = allmodels_tasks[allmodels_tasks['GAGEID'].astype('int')==gageid].COMID.values[0]

    twsa_values = TWSA_data[TWSA_data['COMID'].astype('int')==int(comid)].iloc[0]
    del TWSA_data
    twsa = dates.copy().iloc[:(twsa_values.shape[0]-1)]
    twsa['twsa'] = twsa_values.values.flatten()[1:]
    twsa['datetime'] = pd.to_datetime(twsa['datetime']).dt.normalize()
    twsa = twsa[twsa['datetime']<=datetime(2022,5,23)]
    twsa = twsa[['datetime','twsa']]
    
    twsa['datetime'] = pd.to_datetime(twsa['datetime']).dt.normalize()
    twsa['month'] = twsa['datetime'].dt.month
    twsa['year'] = twsa['datetime'].dt.year

    
    if model_regionalisation == 'NuSVR':
        var_alpha, var_beta = 'NUSVR_alpha', 'NUSVR_beta'
    elif  model_regionalisation == 'GP':
        var_alpha, var_beta = 'GP_alpha', 'GP_beta'
    elif model_regionalisation == 'GB':
        var_alpha, var_beta = 'GB_alpha', 'GB_beta'
    
    if model_spatial_feasibility == 'SVC':
        var_sd = 'svc_sd'
    elif  model_spatial_feasibility == 'XGB':
        var_sd = 'xgb_sd'
    elif model_spatial_feasibility == 'RF':
        var_sd = 'rf_td'
        
    if model_temporal_feasibility == 'NN':
        var_td = 'NN_td'
    elif  model_temporal_feasibility == 'XT':
        var_td = 'XT_td'
    elif model_temporal_feasibility == 'RF':
        var_td = 'RF_td'

    alp_pred = allmodels_tasks[allmodels_tasks['COMID'] == comid][var_alpha].values[0]
    bet_pred = allmodels_tasks[allmodels_tasks['COMID'] == comid][var_beta].values[0]
    
    twsa['Q_pred'] = alp_pred * np.exp(twsa[['twsa']] * bet_pred)
    
    
    #Get in-situ observations
    observations = pd.read_csv(r"static/data/global_gauges_q.csv")
    df_q = observations[observations['GAGEID'].astype('str')==str(gageid)]
    del observations
    df_q['date'] = pd.to_datetime(df_q['date'])
    df_q['month'] = df_q['date'].dt.month
    df_q['year'] = df_q['date'].dt.year
    
    twsa = pd.merge(twsa,df_q,how='left', on = ['year','month'])
    # twsa = twsa.dropna(axis=0)
    
    # Q at confident months 
    columns_months = [j+'_'+model_temporal_feasibility for j in ['Jan', 'Feb', 'March', 'April', 'May', 'June', 'July', 'Aug','Sept', 'Oct', 'Nov', 'Dec']]
    predicted_months = allmodels_tasks[allmodels_tasks['COMID'] == comid][columns_months].values[0]
    predicted_months = [enum+1 for enum,num in enumerate(predicted_months) if num==1]
    # twsa = twsa.dropna(axis=0)
    
    twsa['Q_pred_selmonths'] = twsa['Q_pred']
    twsa.loc[~twsa["month"].isin(predicted_months),['Q_pred_selmonths']] = np.nan
    print(twsa.head(5), twsa.shape)
    # twsa.to_csv('saved_middle.csv')
    if twsa.shape[0] == 0:
        logger.info("No data for TWSA")
        return dict(discharges=pd.DataFrame(), 
                    spatial_discrepency = None,
                    temporal_discrepency = None)
    
    value_sd = allmodels_tasks[allmodels_tasks['COMID'] == comid][var_sd].values[0]
    twsa['GAGEID'] = gageid
    
    
    return dict(discharges = twsa,
                spatial_discrepency = value_sd,
                temporal_discrepency = allmodels_tasks[allmodels_tasks['COMID'] == comid][var_td].values[0])
    # print(twsa.shape,"TWSA_Shape_Gauge_________________________________s")
    # Troubleshooting--------------------
    # test_df = pd.DataFrame({
    #     'datetime': pd.date_range(start='2014-01-01', periods=100, freq='D'),
    #     'Q_pred': range(100)
    # })

    # return dict(usgs_discharge=range(100)).to_json()


def as_timeseries_scatterplot(
    df: Union[pd.DataFrame, None]
) -> Union[html.P, dcc.Graph]:
    """
    Converts pandas DataFrame into a timeseries plot.

    Parameters
    ----------
    df: pandas DataFrame
        DataFrame containing Q data. Expecting the following
        columns: datetime, month, year, TWSA, Q_pred, Q_pred_subset

    Returns
    -------
    graph: dcc.Graph
        Dash scatter graph object containing the input data.

    """
    start_time = time.time()
    if df is None:
        return html.P(
            "Please select a location on the map to populate this graph",
            style={"margin-top": "1rem"},
        )
    gageid = df['GAGEID'].unique()
    # build figure
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=df['datetime'],
            y=df['Q_pred'],
            mode="lines",
            name="Q simulated"
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df["datetime"],
            y=df["Q_pred_selmonths"],
            mode="markers",
            name="Q months certain",
        )
    )
    
    if ~df['Q_mon'].isnull().all():
        fig.add_trace(
            go.Scatter(
                x=df["datetime"],
                y=df["Q_mon"],
                mode="lines",
                name="Q observed",
            )
        )
        
    fig_margin = (
        0  # default 80 https://plotly.com/python/reference/layout/#layout-margin
    )
    fig.update_layout(
        title =  f" Gauge ID: {gageid[0]}",
        margin_t=fig_margin+35,
        margin_l=fig_margin,
        margin_b=fig_margin,
        margin_r=fig_margin,
        yaxis_title = "River discharge (cm/month)",
        
    )
    
    end_time = time.time()
    print("Generate Graph:      ", end_time - start_time)
    return dcc.Graph(
        id="hydrograph",
        figure=fig,
    )


def as_table(df: Union[pd.DataFrame, None]) -> Union[html.P, dbc.Table]:
    """
    Converts pandas DataFrame into a table.

    Parameters
    ----------
    df: pandas.DataFrame
        DataFrame containing S bWOT and USGS data. Expecting the following
        columns: datetime, month, year, TWSA, Q_pred

    Returns
    -------
    table: dbc.Table
        table object containing the content of the dataframe

    """
    start_time = time.time()
    if df is None:
        return html.P(
            "Please select a location on the map to populate this table",
            style={"margin-top": "1rem"},
        )
    df = df[['datetime','Q_pred',"Q_pred_selmonths","Q_mon"]].round(4)
    df.columns = ['datetime','Q simulated (cm/month)',"Q certain months","Q observed"]
    # df.reset_index(inplace=True)
    end_time = time.time()
    
    print(f"Runtime for table: {end_time - start_time} seconds")
    
    return dbc.Table.from_dataframe(df)
