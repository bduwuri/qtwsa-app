#!/usr/bin/env python3

from dash import dcc
import dash_bootstrap_components as dbc
from plotly import express as px
import pandas as pd

# typing imports
import plotly.graph_objs._figure as graph_objects
from typing import Dict, Tuple, Any

# shadow types
MapDataframe = pd.DataFrame

def help(txt: str) -> dbc.Modal:
    """
    Builds the help documentation Modal. Documentation text is
    obtained from a markdown file.

    Parameters
    ----------
    txt: str
        Markdown text to render in the modal element.

    Returns
    -------
    dbc.Modal
            Dash bootstrap modal component with help text.
    """

    help_modal = dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle("Learn More")),
            dbc.ModalBody(
                dcc.Markdown(txt),
            ),
            dbc.ModalFooter(
                dbc.Button(
                    "Close",
                    id="btn-help-close",
                    className="ms-auto",
                    n_clicks=0,
                )
            ),
        ],
        id="modal-help",
        size="lg",
        scrollable=True,
        is_open=False,
    )

    return help_modal


def map(map_data: MapDataframe,
) -> Tuple[dcc.Graph, Dict[Any, Any]]:
    """
    Builds the Dash map object

    Parameters
    ----------
    map_data: pandas.DataFrame
        Dataframe containing the USGS points as metadata to be displayed 
        on the map.

    Returns
    -------
    dcc.Graph
            Dash graph object
    Dict[Any, Any]
            Dictionary of map data
    """
    # build the map object
    fig = px.scatter_mapbox(
        map_data,
        lat='Lat',
        lon='Lon',
        hover_name="GAGEID",
        hover_data=["GAGEID","area"],
        mapbox_style="open-street-map",
        zoom=1.5,
        center={"lat": 20, "lon": 0}
    )  # type: graph_objects.Figure

    # default 80 https://plotly.com/python/reference/layout/#layout-margin
    fig_margin = 0

    fig.update_layout(
        margin_t=fig_margin,
        margin_l=fig_margin,
        margin_b=fig_margin ,
        margin_r=fig_margin,
    )

    return dcc.Graph(
        id="usgs_sites",
        figure=fig,
        style={"height": "80vh"},
    ), map_data.to_dict(orient="records")
