# Q-TWSA tool for predicting river discharge from GRACE TWSA

The tool is an open-source, interactive hydrologic modeling application designed to estimate global river discharges using satellite-derived Total Water Storage Anomalies (TWSA) data. It integrates preprocessed TWSA data with machine learning (ML)-based regionalized hydrologic model parameters and spatial/temporal applicability classifications.

Key features include:
1. Interactive Map Interface: Users can select gauge locations on a map to compute discharge estimates (Q) and view applicability tags.
2. Model Flexibility: Users can choose from multiple ML models for regionalization, spatial feasibility, and temporal feasibility tasks.
3. Spatial and Temporal Confidence: The tool provides spatial and temporal dependency metrics (e.g., "good" or "poor" applicability) for each selected location.
4. Dockerized Deployment: The tool is packaged as a Dockerized application for local deployment, ensuring portability and reproducibility.

This tool demonstrates the effectiveness of machine learning in handling large-scale hydrologic systems and provides actionable insights for water resource management.

## Setting up the developer environment

The code formatter, `black`, is used within this project. Please ensure to either run black prior to
making commits or have it setup to automatically run when you save files in your IDE.

```shell
# Create and activate python environment, requires python >= 3.8
python -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip

# install dependencies
python -m pip install -r requirements.txt

# install testing / development dependencies
python -m pip install black

# run the application locally
gunicorn --bind :8000 app:server --access-logfile -
```

### Using Docker

```shell
# build docker image
cd docker
docker-compose build app

# start server
docker-compose up
```
