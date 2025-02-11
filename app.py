#!/usr/bin/env python3

import dash
import dash_bootstrap_components as dbc
import time
# local imports
import layout
import callbacks
import logging_config
from waitress import serve
start_time = time.time()

logging_config.configure_logger()

app = dash.Dash(name=__name__, external_stylesheets=[dbc.themes.MINTY])

server = app.server
app.title = "Q-TWSA Tool"


# set the layouts defined in layout.py
app.layout = layout.main
end_time = time.time()

print(f"Runtime setting map layout: {end_time - start_time} seconds")
if __name__ == "__main__":
    # for available environment variables see:
    # - https://dash.plotly.com/reference#dash.dash
    # - https://dash.plotly.com/reference#app.run_server

    # short list for convenience:
    # HOST: str
    # PORT: int
    # DASH_DEBUG: int (1, 0)
    # DASH_ROUTES_PATHNAME_PREFIX - "A local URL prefix for JSON requests. Defaults to
    #                                url_base_pathname, and must start and end with '/'."
    # DASH_PROXY - "If this application will be served to a different URL via a proxy configured
    #              outside of Python, you can list it here as a string of the form "{input}::{output}", for
    #              example: "http://0.0.0.0:8050::https://my.domain.com""

    # app.run_server(debug=True, dev_tools_silence_routes_logging=False)
    # app.run_server(debug=True)
    serve(app.server, host='0.0.0.0', port=10000)

