#!/usr/bin/env python3

from dash import dcc, html
import dash_bootstrap_components as dbc
from datetime import date

# local imports
import components
import utils

# load help documentation
about_md = "static/about.md"
with open(about_md, "r") as f:
    about_text = f.read()

# load description text
desc_md = "static/description.md"
with open(desc_md, "r") as f:
    desc_text = f.read()


# --------------
# SIDEBAR LAYOUT
# --------------
sidebar = dbc.Card(
    [
        html.Div([html.P(dcc.Markdown(desc_text))]),
        html.Hr(),
        html.Div(
            [
                html.P("μ Conversion"),
                dcc.Dropdown(
                    id="mean_conversion_parameter",
                    value=-0.27,
                    options=[
                        dict(label=-0.027, value=-0.27),
                        dict(label=-0.01, value=-0.01),
                        dict(label=-0.5, value=-0.5),
                    ],
                    style={"margin-bottom": "1rem"},
                ),
            ],
            title="Mean Conversion Parameter",
        ),
        
        # html.Div(
        #     [
        #         html.P("Model Regionalisation"),
        #         dcc.Dropdown(
        #             id="standard_deviation_conversion_parameter",
        #             value=0.051,
        #             options=[
        #                 dict(label=0.051, value=0.051),
        #                 dict(label=0.01, value=0.01),
        #                 dict(label=0.1, value=0.1),
        #             ],
        #             style={"margin-bottom": "1rem"},
        #         ),
        #     ],
        #     title="Standard Deviation Conversion Parameter",
        # ),
        html.Div(
            [
                html.P("Model Spatial Feasibility"),
                dcc.Dropdown(
                    id="standard_deviation_conversion_parameter",
                    value=0.051,
                    options=[
                        dict(label=0.051, value=0.051),
                        dict(label=0.01, value=0.01),
                        dict(label=0.1, value=0.1),
                    ],
                    style={"margin-bottom": "1rem"},
                ),
            ],
            title="Standard Deviation Conversion Parameter",
        ),
        html.Div(
            [
                html.P("Start Date"),
                dcc.DatePickerSingle(
                    id="start_date",
                    date=date(2014, 4, 1),
                ),
            ],
            title="Assumed SWOT Mission Launch Date",
        ),
        html.Hr(),
        html.Div(
            [
                dbc.Button("Learn More", id="btn-help-open",
                           color='info', n_clicks=0),
                components.help(about_text),
            ],
            title="Learn More",
        ),
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
        html.H2("Synthetic SWOT Streamflow Generator"),
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
                    md=8,
                ),
            ],
            align="top",
            justify="center",
        ),
        dcc.Store(id="store-swot"),
        dcc.Store(id="store-map", data=map_data_dict),
    ],
    fluid=True,
)
