import kfp
from datetime import datetime
import re
import os
import mechanize
from bs4 import BeautifulSoup
import urllib
import http.cookiejar as cookielib 

# Get today's date for tags
today = str(datetime.now())

# Def
def get_id(text):
    """
    Function that retrieves a pipelines's ID from its logs

    Parameters
    ----------
    text : str
        string version of the logs.

    Returns
    -------
    str : Id of the pipeline.

    """
    match = re.search('{\'id\': \'(.+?)\',\\n', text)        
    if match:
        found = match.group(1)
        return(found)
    
def get_cookie(text):
    """
    Function that retrieves login cookie

    Parameters
    ----------
    text : str
        string version of the logs.

    Returns
    -------
    str : cookie value.

    """
    match = re.search('authservice_session=(.+?) ', text)        
    if match:
        found = match.group(1)
        return(found)

# Parameters
URL = os.getenv('URL')
pipeline_name = "advanced_pipeline"
job_name = pipeline_name + today
ENDPOINT = os.getenv('ENDPOINT') # Reminder : ENDPOINT is URL which ends with ...amazonaws.com/pipeline
EMAIL = os.getenv('EMAIL')
PASSWORD = os.getenv('PASSWORD')



#EMAIL = "user"


# Run parameters

version_id = '1'
#params = {'bucket' : 'src-data',
 #       'data_2015' : 'temptest/2015-building-energy-benchmarking.csv',
  #      'data_2016' : 'temptest/2016-building-energy-benchmarking.csv',
   #     'hyperopt_iterations' : '1',
    #    'subfolder' : 'temptest'}

params = {'hyperopt_iterations' : 1}

# Create run or update ?
kind = "update"

# Get cookie value
cj = cookielib.CookieJar()
br = mechanize.Browser()
br.set_cookiejar(cj)
br.open(URL)

br.select_form(nr=0)
br.form['login'] = EMAIL
br.form['password'] = PASSWORD
br.submit()
authservice_session = 'authservice_session={}'.format(get_cookie(str(cj)))

# Connect to Kubeflow Pipelines Manager
client = kfp.Client(host=ENDPOINT, cookies=authservice_session)

# Create pipeline
if kind == "create":
    pipe_logs = client.upload_pipeline(pipeline_package_path="./pipeline/pipeline.yaml",
                          pipeline_name=pipeline_name,
                          description="Advanced MLOps pipeline")
    
# Upload new version of existing pipeline
elif kind == "update":
    version_name = "update-pipeline-" + today
    pipe_logs = client.upload_pipeline_version(pipeline_package_path="./pipeline/pipeline.yaml",
                                   pipeline_version_name=version_name,
                                   pipeline_name = pipeline_name)

pipeline_id = get_id(str(pipe_logs))
print(client.list_experiments(namespace = 'kubeflow-user'))
try:
    experiment_id = client.get_experiment(experiment_name=pipeline_name, namespace='kubeflow-user').id
except:
    experiment_id = client.create_experiment(pipeline_name, namespace='kubeflow-user').id
    
#experiments = list_experiments_response.experiments

# Run pipeline
client.run_pipeline(experiment_id=experiment_id,
                   job_name=job_name,
                   params=params,
                   pipeline_id=pipeline_id)

from kale.common.serveutils import serve

kfserver = serve(model, preprocessing_fn=process_features, preprocessing_assets={'tokenizer':tokenizer})