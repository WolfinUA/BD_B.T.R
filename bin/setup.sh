environment_name=os

conda create -n $environment_name -c conda-forge --strict-channel-priority osmnx
conda activate $environment_name
pip install -r requirements.txt