#!/usr/bin/env python3

from dash import dcc, html, Input, Output, State, callback
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
import pandas as pd
import time
# local imports
import utils

# typing imports
from typing import Dict, Any, Union


@callback(
    Output("modal-help", "is_open"),
    [Input("btn-help-open", "n_clicks"), Input("btn-help-close", "n_clicks")],
    State("modal-help", "is_open"),
)
def toggle_modal(n1: int, n2: int, is_open: bool) -> bool:
    """
    Sets the open/close state of the modal window

    Parameters
    ----------
    n1: int
        number of times the open button was clicked.
    n2: int
        number of times the close button was clicked.
    is_open: bool
        current state of the modal window

    Returns
    bool
        new state of the modal window
    """
    if n1 or n2:
        return not is_open
    return is_open


@callback(
    Output("tab-content", "children"),
    Input("tabs-results", "value"),
    Input("store-qtwsa", "data"),
)
def render_content(
    tab: str, 
    qtwsa_data: pd.DataFrame
) -> Union[html.P, dcc.Graph, dbc.Table, None]:
    """
    Renders the tab view content

    Parameters
    ----------
    tab: str
        The name of the tab element that is active
    qtwsa_data: pandas.DataFrame
        cached data needed to populate the graph and table
        tab views.

    Returns
    -------
    page element: Union[message, graph, table, None]
        message: html.P
            An html status message
        graph: dcc.Graph
            Graph containing observed and simulated data 
        table: dbc.Table
            Table containing observed and simulated data 

    """

    df = pd.read_json(qtwsa_data) if qtwsa_data is not None else None

    if tab == "tab-timeseries":
        return utils.as_timeseries_scatterplot(df)

    elif tab == "tab-table":
        return utils.as_table(df)

    return None



@callback(
    [
        Output("store-qtwsa", "data"),
        Output("spatial_dependency", "children"),
        Output("temporal_dependency", "children"),
    ],
    [
        Input("usgs_sites", "clickData"),
        # Input("store-map", "data"),
    ],
    [
        State("Model Regionalisation", "value"),
        State("Model Spatial Feasibility", "value"),
        State("Model Temporal Feasibility", "value"),
    ],
    prevent_initial_call=True
)
def figure_clicked_callback(
    selectedData: Dict[Any, Any],
    model_regionalisation: str,
    model_spatial_feasibility: str,
    model_temporal_feasibility: str,
) -> Union[str, None]:
    
    
    start_time = time.time()
    if selectedData is None:
        raise PreventUpdate

    station_id = selectedData["points"][0]["hovertext"]


    
    res = utils.handle_click(
    station_id,
    model_regionalisation,
    model_spatial_feasibility,
    model_temporal_feasibility,
    )

    discharge = res["discharges"]

    # TODO: add a message to the UI indicating that USGS data was not available
    if (discharge.empty):
        return None

    discharge.sort_values("datetime", inplace=True)
    
    value_sd = res['spatial_discrepency']
    
    def get_dependency_color(value):
        try:
            # Convert the dependency value to a float.
            val = int(value)
        except (TypeError, ValueError):
           return "black" # default if conversion fails
       
        if val == 0:
            return "red", "Poor"
        elif val == 1:
            return "lightgreen", "Good"
        elif val == 2:
            return "green", "Very Good"
        elif val == 3:
            return "darkgreen", "Excellent"
        
    color_sd, quality_sd = get_dependency_color(value_sd)
    spatial_confidence = html.Div(["Spatial Feasibility: ",
    html.Div(
        str(quality_sd),
        style={
            "background-color": color_sd,
            "color": "white",      # adjust text color for contrast
            "padding": "10px",
            "margin-left": "10px",
            "display": "inline-block",
            "border-radius": "5px"
        }
    )
])
    
    spatial_dependency = spatial_confidence
    temporal_dependency = f"Number of months with confident results: {res['temporal_discrepency']}"
    end_time = time.time()
    print("Generate Q Timeseries:      ", end_time - start_time)
    return discharge.to_json(),spatial_dependency, temporal_dependency
