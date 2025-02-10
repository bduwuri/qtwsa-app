#!/usr/bin/env python3

from dash import dcc, html
import dash_bootstrap_components as dbc

# local imports
import components
import utils

# load help documentation
about_md = "static/about.md"
with open(about_md, "r") as f:
    about_text = f.read()




# --------------
# SIDEBAR LAYOUT
# --------------
sidebar = dbc.Card(
    [
        # html.Div([html.P(dcc.Markdown(desc_text))]),
        html.Hr(),
        html.Div(
            [
                html.P("Model Regionalisation"),
                dcc.Dropdown(
                    id="Model Regionalisation",
                    value="GP",
                    options=[
                        dict(label="NuSVR", value="NuSVR"),
                        dict(label="GP", value="GP"),
                        # dict(label="GB", value="GB"),
                    ],
                    style={"margin-bottom": "1rem"},
                ),
            ],
            title="Model Regionalisation",
        ),
        
        html.Div(
            [
                html.P("Model Spatial Feasibility"),
                dcc.Dropdown(
                    id="Model Spatial Feasibility",
                    value="XGB",
                    options=[
                        dict(label="XGB", value="XGB"),
                        dict(label="SVC", value="SVC"),
                        # dict(label="RF", value="RF"),
                    ],
                    style={"margin-bottom": "1rem"},
                ),
            ],
            title="Model Spatial Feasibility",
        ),
        html.Div(
            [
                html.P("Model Temporal Feasibility"),
                dcc.Dropdown(
                    id="Model Temporal Feasibility",
                    value="RF",
                    options=[
                        dict(label="XT", value="XT"),
                        dict(label="NN", value="NN"),
                        dict(label="RF", value="RF"),
                    ],
                    style={"margin-bottom": "1rem"},
                ),
            ],
            title="Model Temporal Feasibility",
        ),
        
        html.Hr(),
        
        # Placeholders for spatial and temporal dependency outputs
        html.Div(id="spatial_dependency", style={"margin-top": "1rem"}),
        html.Div(id="temporal_dependency", style={"margin-top": "1rem"}),
        
    ],
    body=True,
)

# -----------
# Main Layout
# -----------

# collect map data that will be used in the layout
mapdf = utils.get_map_data()

# build the map
map_component, map_data_dict = components.map(mapdf)

# main layout definition
main = dbc.Container(
    id="root",
    children=[
        html.H2("Q-TWSA tool for generating discharge from GRACE satellite TWSA"),
        html.Hr(),
        dbc.Row(
            [
                dbc.Col(sidebar, md=3),
                dbc.Col(
                    [
                        dcc.Tabs(
                            id="tabs-results",
                            value="tab-map",
                            children=[
                                dcc.Tab(
                                    label="Map",
                                    value="tab-map",
                                    children=[map_component],
                                ),
                                dcc.Tab(label="Timeseries", value="tab-timeseries"),
                                dcc.Tab(label="Tabular", value="tab-table"),
                            ],
                        ),
                        html.Div(id="tab-content"),
                    ],
                    md=9,
                ),
            ],
            align="top",
            justify="center",
        ),
        dcc.Store(id="store-qtwsa"),
        dcc.Store(id="store-map", data=map_data_dict),
    ],
    fluid=True,
)
