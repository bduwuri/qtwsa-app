#!/usr/bin/env python3

from dash import dcc, html, Input, Output, State, callback
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
import pandas as pd

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
    Input("store-swot", "data"),
)
def render_content(
    tab: str, swot_data: pd.DataFrame
) -> Union[html.P, dcc.Graph, dbc.Table, None]:
    """
    Renders the tab view content

    Parameters
    ----------
    tab: str
        The name of the tab element that is active
    swot_data: pandas.DataFrame
        cached SWOT data needed to populate the graph and table
        tab views.

    Returns
    -------
    page element: Union[message, graph, table, None]
        message: html.P
            An html status message
        graph: dcc.Graph
            Graph containing USGS and SWOT data
        table: dbc.Table
            Table containing data USGS and SWOT data

    """

    df = pd.read_json(swot_data) if swot_data is not None else None

    if tab == "tab-timeseries":
        return utils.as_timeseries_scatterplot(df)

    elif tab == "tab-table":
        return utils.as_table(df)

    return None


@callback(
    Output("store-swot", "data"),
    Input("usgs_sites", "clickData"),
    Input("store-map", "data"),
    State("mean_conversion_parameter", "value"),
    State("standard_deviation_conversion_parameter", "value"),
    State("start_date", "date"),
    prevent_initial_call=True,
)
def figure_clicked_callback(
    selectedData: Dict[Any, Any],
    map_data_dict: Dict[Any, Any],
    mean_conversion_parameter: float,
    standard_deviation_conversion_parameter: float,
    start_date: str,
) -> Union[str, None]:
    
    # Catch the initial load. This functions is called after initial page
    # load because it's the default selected tab. I believe that this
    # kicks off the clicked event.
    if selectedData is None:
        raise PreventUpdate

    station_id = selectedData["points"][0]["hovertext"]

    map_df = pd.DataFrame(map_data_dict)
    map_df.convert_dtypes()
    res = utils.handle_click(
        station_id,
        map_df,
        mean_conversion_parameter,
        standard_deviation_conversion_parameter,
        start_date=start_date,
    )

    usgs, swot = res["usgs_discharge"], res["swot_discharge"]
   
    # return None if there was an error collecting or processing
    # synthetic SWOT data.
    # TODO: add a message to the UI indicating that USGS data was not available
    if (usgs.empty) or (swot.empty):
        return None

    merged = pd.merge(usgs, swot, on="date", how="left", suffixes=["_usgs", "_swot"])
    merged.sort_values("date", inplace=True)
    merged.set_index("date", inplace=True)
    merged.interpolate(limit_area="inside", inplace=True)
    merged.reset_index(inplace=True)

    return merged.to_json()
