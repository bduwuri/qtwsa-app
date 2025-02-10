FROM python:3.9
RUN pip install pandas==1.4.1

RUN apt-get update && apt-get install -y gdal-bin proj-bin libgdal-dev gcc && pip install -U pip wheel

WORKDIR /app

COPY ./requirements.txt /app/

RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

COPY ./static /app/static
COPY ./assets /app/assets

COPY app.py layout.py utils.py callbacks.py  components.py logging_config.py /app/

# Allow statements and log messages to immediately appear in the Knative logs
ENV PYTHONUNBUFFERED True

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
#              example: "http://0.0.0.0:8000::https://my.domain.com""
ENV N_WORKERS 1
ENV N_THREADS 8
ENV PORT 8000

# For environments with multiple CPU cores, increase the number of workers
# to be equal to the cores available.
# Timeout is set to 0 to disable the timeouts of the workers to allow Cloud Run to handle instance scaling.
CMD exec gunicorn --bind :${PORT} --workers ${N_WORKERS} --threads ${N_THREADS} --timeout 0 --access-logfile - app:server
