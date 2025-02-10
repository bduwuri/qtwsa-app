#!/usr/bin/env python3


import math
import numpy as np
import pandas as pd
import dataretrieval.nwis as nwis
import pytz
from datetime import datetime
import geopandas as gpd

from dash import dcc, html
import dash_bootstrap_components as dbc
import plotly.graph_objects as go

# typing imports
from typing import Dict, Union

# local imports
from logging_config import get_logger

# shadow types
UsgsDischarge = pd.DataFrame
SwotDischarge = pd.DataFrame

# instantiate logger
logger = get_logger(__name__)


CFS_TO_CMS = 0.028316846592


def get_map_data(
    USGS_data_file: str = "static/data/usgs-gauges/USGS_Q_sites_Active2015_1000sqkm.shp",
    SWOT_data_file: str = "static/data/swot-orbit/SWOT21day_Swath120m20.shp",
) -> pd.DataFrame:
    """
    Collects the data required for the map component

    Parameters
    ----------
    USGS_data_file: str
            Path to Shapefile containing USGS sites to populate
            on the map.
    SWOT_data_file: str
            Path to Shapefile containing SWOT orbit. This is
            used to reproject the USGS data.

    Returns
    -------
    pandas.DataFrame
            A DataFrame containing the data for the map component
    """

    # load data
    usgs_df = gpd.GeoDataFrame.from_file(USGS_data_file)
    swot_df = gpd.GeoDataFrame.from_file(SWOT_data_file)

    # re-project usgs data to match swot data's crs
    # use wkt string to avoid projections that do not have an assigned EPSG string
    usgs_df = usgs_df.to_crs(swot_df.crs.to_wkt())

    # join geodataframes by intersection
    joined_df = gpd.sjoin(swot_df, usgs_df, predicate="intersects")

    # drop geometry col
    joined_df.drop(columns="geometry", inplace=True)

    return pd.DataFrame(joined_df)


def get_data(
    site_no: str, start_date: datetime, end_date: datetime
) -> Union[pd.DataFrame, None]:
    """
    Collects and prepares USGS streamflow data required
    to generate synthetic SWOT data.

    Parameters
    ----------
    site_no: str
        The USGS site identifier.
    start_date: datetime.datetime
        Beginning of desired time span.
    end_date: datetime.datetime
        End of desired time span.

    Returns
    -------
    pandas.DataFrame
        USGS streamflow data for the requested site.

    """

    # set parameters
    station_id = str(site_no)

    # get instantaneous values (dv)
    data = nwis.get_record(
        sites=station_id,
        service="dv",
        start=start_date.strftime("%Y-%m-%d"),
        end=end_date.strftime("%Y-%m-%d"),
    )

    col_of_interest = "00060_Mean"
    initial_datetime_col = "datetime"

    # return None if streamflow data was not found
    # at this USGS gage.
    if col_of_interest not in data.columns:
        return None
    logger.info("Got NWIS Data for {}".format(station_id))

    data = data.loc[:, col_of_interest]

    data = data.reset_index()

    # assert that incoming datetime is in UTC tz
    assert data[initial_datetime_col].dt.tz == pytz.UTC

    # drop to naive UTC time
    data[initial_datetime_col] = data[initial_datetime_col].dt.tz_convert(None)

    # convert cfs to cms
    data[col_of_interest] = data[col_of_interest] * CFS_TO_CMS

    data.rename(
        columns={initial_datetime_col: "date", col_of_interest: "discharge_m3s"},
        inplace=True,
    )

    return data


def handle_click(
    gageid: str,
    swot_days: pd.DataFrame,
    mu_conversion: float = -0.027,
    sigma_conversion: float = 0.051,
    start_date: str = "2014-04-01",
) -> Dict[str, Union[UsgsDischarge, SwotDischarge]]:
    """
    Computes synthetic SWOT measurments.

    Parameters
    ----------
    gageid: str
        USGS streamflow gage identifier
    swot_days: pandas.DataFrame
        Dataframe containing SWOT orbit data. More information
        can be found at: https://www.aviso.altimetry.fr/en/missions/future-missions/swot/orbit.html
    mu_conversion: float
        mean conversion parameter from Mississippi river derivation in m3/s. Used for scaling the log-transformed mean calculated from a gaussian error distribution for the gauge discharges (Nickles et al., 2019).
    sigma_conversion: float
        standard deviation conversion parameter from Mississippi river derivation in m3/s. Used for scaling the log-transformed standard deviation calculated from a gaussian error distribution for the gauge discharges (Nickles et al., 2019).
    start_date: str
        Assumed launch date of SWOT mission

    Returns
    -------
    synthetic_swot_data: Dict[str, pandas.Dataframe]
        usgs_discharge: List
            USGS observed river discharge or None
        swot_discharge: List
            Synthetic SWOT river discharge or None
    """

    # convert start_date into a datetime object
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")

    # Name of discharge column in input file (usgsflow)
    DischargeCol = "discharge_m3s"

    # answering the question if it is a discharge timeseries (y/n)
    Uncertainty = "y"

    SWOT_Days_Table = swot_days

    # SWOT day calculation
    # The algorithm for synthetically derived SWOT data was presented at
    # the 2021 AGU Fall Conference but has yet to be formally published. For
    # more information about the algorithm, see the following link.
    # https://agu.confex.com/agu/fm21/meetingapp.cgi/Paper/943261
    SWOT_1_day = start_dt.isoformat()
    datelist = [
        datetime.fromisoformat(str(d)).date().isoformat()
        for d in pd.date_range(start=SWOT_1_day, end="2021-01-01").tolist()
    ]
    rank = list(range(1, (len(datelist) + 1)))
    SWOT_day = [i % 21 for i in rank]
    SWOT_day = [i if i != 0 else 21 for i in SWOT_day]
    datelist = pd.DataFrame(datelist)
    rank = pd.DataFrame(rank)
    SWOT_day = pd.DataFrame(SWOT_day)
    SWOT_days = pd.concat([datelist, rank, SWOT_day], axis=1)
    SWOT_days.columns = ["date", "rank", "SWOT_day"]
    SWOT_days["date"] = pd.to_datetime(SWOT_days["date"])

    point = str(gageid)
    site_data = get_data(gageid, start_dt, datetime.today())

    # check to make sure that USGS data was retrieved successfully
    if site_data is None:
        logger.info(f"Data not available for: {gageid}")
        return dict(usgs_discharge=pd.DataFrame(), swot_discharge=pd.DataFrame())

    # remove nodata values, typically a large negative number
    site_data = site_data[site_data["discharge_m3s"] > 0]

    # check to make sure that data is available after 2014
    site_data = site_data[site_data["date"] > SWOT_1_day]
    if site_data.shape[0] == 0:
        logger.info("Data after 2014 not available")
        return dict(usgs_discharge=pd.DataFrame(), swot_discharge=pd.DataFrame())

    q_g = site_data
    site_data = pd.merge(site_data, SWOT_days, on="date")

    if Uncertainty == "y":
        discharge_uncertainty_array = []
        for discharge in range(len(site_data)):

            # mean and standard deviation of Gaussian Error
            if getattr(site_data, DischargeCol).values[discharge] <= 0:
                discharge_uncertainty = getattr(site_data, DischargeCol).values[
                    discharge
                ]
            else:
                mu = mu_conversion * math.log10(
                    getattr(site_data, DischargeCol).values[discharge]
                )
                sigma = sigma_conversion * math.log10(
                    getattr(site_data, DischargeCol).values[discharge]
                )

                # generate error scalar
                if sigma <= 0:
                    GaussianError = 0
                else:
                    GaussianError = np.random.normal(mu, sigma)

                # add error to flow
                discharge_uncertainty = (
                    math.log10(getattr(site_data, DischargeCol).values[discharge])
                    + GaussianError
                )
                discharge_uncertainty = math.pow(10, discharge_uncertainty)

            # add clause if less than zero
            if discharge_uncertainty < 0:
                discharge_uncertainty = 0.1

            discharge_uncertainty_array += [discharge_uncertainty]
        # end for discharge in range(len(df_flow)):
        # convert to dataframe with title
        df_discharge_uncertainty = pd.DataFrame(discharge_uncertainty_array)
        df_discharge_uncertainty.columns = ["discharge_uncertainty_m3s"]

        # add uncertainty column to flow
        site_data = pd.concat([site_data, df_discharge_uncertainty], axis=1)

    swotpass = np.floor(
        SWOT_Days_Table[SWOT_Days_Table.GAGEID == point].FIRST_DayT.values
    )
    df_point = site_data
    df_point_swotday = df_point[df_point.SWOT_day.isin(swotpass)]

    if df_point_swotday.shape[0] == 0:
        logger.info("No data for SWOT pass days")
        return dict(usgs_discharge=pd.DataFrame(), swot_discharge=pd.DataFrame())

    q_s = df_point_swotday

    return dict(usgs_discharge=q_g, swot_discharge=q_s)


def as_timeseries_scatterplot(
    df: Union[pd.DataFrame, None]
) -> Union[html.P, dcc.Graph]:
    """
    Converts pandas DataFrame into a timeseries plot.

    Parameters
    ----------
    df: pandas DataFrame
        DataFrame containing SWOT and USGS data. Expecting the following
        columns: date, discharge_m3s_usgs, discharge_m3s_swot

    Returns
    -------
    graph: dcc.Graph
        Dash scatter graph object containing the input data.

    """

    if df is None:
        return html.P(
            "Please select a location on the map to populate this graph",
            style={"margin-top": "1rem"},
        )

    # build figure
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(x=df["date"], y=df["discharge_m3s_usgs"], mode="lines", name="USGS")
    )
    fig.add_trace(
        go.Scatter(
            x=df["date"],
            y=df["discharge_m3s_swot"],
            mode="markers",
            name="Synthetic SWOT",
        )
    )

    fig_margin = (
        0  # default 80 https://plotly.com/python/reference/layout/#layout-margin
    )
    fig.update_layout(
        margin_t=fig_margin,
        margin_l=fig_margin,
        margin_b=fig_margin + 20,
        margin_r=fig_margin,
    )

    return dcc.Graph(
        id="swot_hydrograph",
        figure=fig,
    )


def as_table(df: Union[pd.DataFrame, None]) -> Union[html.P, dbc.Table]:
    """
    Converts pandas DataFrame into a table.

    Parameters
    ----------
    df: pandas.DataFrame
        DataFrame containing SWOT and USGS data. Expecting the following
        columns: date, discharge_m3s_swot, discharge_m3s_usgs,
        discharge_uncertainty_m3s

    Returns
    -------
    table: dbc.Table
        table object containing the content of the dataframe

    """

    if df is None:
        return html.P(
            "Please select a location on the map to populate this table",
            style={"margin-top": "1rem"},
        )

    df.reset_index(inplace=True)

    return dbc.Table.from_dataframe(
        df[
            [
                "date",
                "discharge_m3s_usgs",
                "discharge_m3s_swot",
                "discharge_uncertainty_m3s",
            ]
        ],
        id="swot_table",
        striped=True,
        bordered=True,
        hover=True,
        index=False,
        responsive=True,
        size="sm",
    )
