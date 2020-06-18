import logging
import json
import requests
import azure.functions as func
from azure.cosmos import exceptions, CosmosClient, PartitionKey

def main(req: func.HttpRequest) -> func.HttpResponse: 
    
    logging.info('Python HTTP trigger function processed a request.')

    with open('config.json', 'r') as config_file:
        config_data = json.load(config_file)

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

    return func.HttpResponse("Cosmos DB - SQL API emails database is created.")

def createclient (endpoint, key) :
    # Initialize the Cosmos client
    endpoint = endpoint
    key = key
    client = CosmosClient(endpoint, key)
    return client

def finddatabase(client, database):
    databases = list(client.query_databases({
        "query": "SELECT * FROM r WHERE r.id=@id",
        "parameters": [
            { "name":"@id", "value": database }
        ]
    }))

    if len(databases) > 0:
        logging.info('Database with id \'{0}\' was found'.format(database))
    else:
        logging.info('No database with id \'{0}\' was found'. format(database))

def createdatabase(client, databasename):
    try:
        database = client.create_database_if_not_exists(id=databasename)
        logging.info('Database with id \'{0}\' created'.format(databasename))
        return database

    except exceptions.CosmosResourceExistsError:
        logging.info('A database with id \'{0}\' already exists'.format(database))


def createcontainer (database, containername) :
    container = database.create_container_if_not_exists(id=containername, partition_key=PartitionKey(path="/id"), offer_throughput=400)
    return container

def createitems (emails, container) :
    for item in emails:
        container.create_item(item)