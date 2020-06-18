# Http trigger written in Python to read mails from MS Graph API and store them in Cosmos DB using SQL API

This is a http trigger function written in Python in Visual Studio Code as the editor. It reads emails from your mail account using Microsoft Graph API and store them to Cosmos DB on SQL AP

## Technology stack  
* Python version 3.8.2 64 bit version https://www.python.org/downloads/release/python-382/
* Azure functions for python version 1.2 *(azure-functions 1.2.0)* https://pypi.org/project/azure-functions/
* Azure Cosmos DB 4.0.0 *(azure-cosmos 4.0.0)* to connect to the Cosmos DB Table API https://pypi.org/project/azure-cosmos/

## How to run the solution
 * You have to create a Cosmos DB account with SQL API and go to the Connection String section and get the endpoint and key to connect to the database
 * Open the solution from Visual Studio code, create a virtual environment to isolate the environment to the project by running, *py -m venv .venv* command. It will install all the required packages mentioned in the *requirements.txt* file

## Code snippets
### Package references in the code file
```
import logging
import json
import requests
import azure.functions as func
from azure.cosmos import exceptions, CosmosClient, PartitionKey
```

### Read settings from config file
```
with open('config.json', 'r') as config_file:
    config_data = json.load(config_file)
 ```
 
 ### Read emails from MS graph API
 ```
accesstoken = config_data["accessToken"]

url = "https://graph.microsoft.com/v1.0/me/messages/"

headers = {'Authorization': 'Bearer {}'.format(accesstoken)}

response_data = requests.get(url, headers=headers)
if response_data.status_code != 200 :
    logging.info('Request error ' + str(response_data.status_code) + ' - ' + response_data.reason)
else:
    emails = json.loads(requests.get(url, headers=headers).text)
    if len(emails) > 0 : 
        endpoint = config_data["endpoint"]
        key = config_data["key"]
        client = createclient(endpoint, key)
        
        databasename = config_data["database"]
        finddatabase(client, databasename)
        database = createdatabase(client, databasename)
        
        containername = config_data["container"]
        container = createcontainer(database, containername)
        
        createitems(emails['value'], container)
 ```
 
 ### Create Cosmos DB client
 ```
 def createclient (endpoint, key) :
    # Initialize the Cosmos client
    endpoint = endpoint
    key = key
    client = CosmosClient(endpoint, key)
    return client
 ```
 
 ### Find database in Cosmos account
 ```
def finddatabase(client, database):
    databases = list(client.query_databases({
        "query": "SELECT * FROM r WHERE r.id=@id",
        "parameters": [
            { "name":"@id", "value": database }
        ]
    }))
```

### Create a database in Cosmos DB account
```
def createdatabase(client, databasename):
    try:
        database = client.create_database_if_not_exists(id=databasename)
        logging.info('Database with id \'{0}\' created'.format(databasename))
        return database

    except exceptions.CosmosResourceExistsError:
        logging.info('A database with id \'{0}\' already exists'.format(database))
```

### Create a conainer in the database
```
def createcontainer (database, containername) :
    container = database.create_container_if_not_exists(id=containername, partition_key=PartitionKey(path="/id"), 
        offer_throughput=400)
    return container
```

### Create a item in the database
```
def createitems (emails, container) :
    for item in emails:
        container.create_item(item)
```
