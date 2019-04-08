import json
import boto3
import datetime
from botocore.vendored import requests
from elasticsearch import Elasticsearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth

def lambda_handler(event, context):
    # TODO implement
    resultData = []
    totalRestaurantCount = 1
    for cuisine in ['mexican']:#, 'indian', 'japanese', 'chinese', 'thai', 'french']:
        
        for i in range(totalRestaurantCount):
            requestData = {
                            "term": cuisine + " restaurants",
                            "location": "manhattan",
                            "limit": 5,
                            "offset": 5*i
                        }
            result = yelpApiCall(requestData)
            resultData = resultData + result
    
    # Add data to the dynamodDB
    dynamoInsert(resultData)
    
    # Add index data to the ElasticSearch
    elasticIndex(resultData)
    
    
    return {
        'statusCode': 200,
        'body': json.dumps('success'),
        'total': len(resultData)
    }

def yelpApiCall(requestData):
    
    url = "https://api.yelp.com/v3/businesses/search"
    
    querystring = requestData
    
    payload = ""
    headers = {
        'Authorization': "Bearer 7NjA90modOdaeEn6bLkfmOoy3YIibnWpCUki41GqXzW5z0nlxHPwRpjXeAJ1ycwHd0qeiipWT-9vtxH-WcSdM5zj9TcHhJrEzW6n_4tuQCS5YHUOnmvg_Ax4KYmKXHYx",
        'cache-control': "no-cache",
        'Postman-Token': "d1b24c2d-4f0d-4a67-b5fa-48f40f6fa447"
        }
    
    response = requests.request("GET", url, data=payload, headers=headers, params=querystring)
    message = json.loads(response.text)
    
    if len(message['businesses']) <= 0:
        return []
    
    return message['businesses']

def dynamoInsert(restaurants):
    
    dynamodb = boto3.resource('dynamodb', region_name='us-west-2')
    table = dynamodb.Table('yelp-restaurants')
    
    
    for each_restaurants in restaurants:
        
        dataObject = {
            'Id': each_restaurants['id'],
            'alias': each_restaurants['alias'],
            'name': each_restaurants['name'],
            'is_closed': each_restaurants['is_closed'],
            'categories': each_restaurants['categories'],
            'rating': int(each_restaurants['rating']),
            'review_count': each_restaurants['review_count'],
            'transactions': each_restaurants['transactions'],
            'zip_code': each_restaurants['location']['zip_code'],
            'display_address': each_restaurants['location']['display_address']
        }
        
        if (each_restaurants['image_url']):
            dataObject['image_url'] = each_restaurants['image_url']
        
        if (each_restaurants['coordinates'] and each_restaurants['coordinates']['latitude'] and each_restaurants['coordinates']['longitude']):
            dataObject['latitude'] = str(each_restaurants['coordinates']['latitude'])
            dataObject['longitude'] = str(each_restaurants['coordinates']['longitude'])
            
        if (each_restaurants['phone']):
            dataObject['phone'] = each_restaurants['phone']
        
        table.put_item(
               Item={
                   'insertedAtTimestamp': str(datetime.datetime.now()),
                   'info': dataObject,
                   'Id': dataObject['Id']
               }
            )
    

def elasticIndex(restaurants):
    host = 'search-dining-suggestion-search-bzwynnc3fgpjqu2tlpou72tbre.us-west-2.es.amazonaws.com' # For example, my-test-domain.us-east-1.es.amazonaws.com
    region = 'us-west-2'
    
    service = 'es'
    credentials = boto3.Session().get_credentials()
    awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service)
    
    es = Elasticsearch(
        hosts = [{'host': host, 'port': 443}],
        # http_auth = awsauth,
        use_ssl = True,
        verify_certs = True,
        connection_class = RequestsHttpConnection
    )
    
    for each_restaurants in restaurants:
        
        dataObject = {
            'Id': each_restaurants['id'],
            'alias': each_restaurants['alias'],
            'name': each_restaurants['name'],
            'categories': each_restaurants['categories']
        }
        
        alreadyExists = es.indices.exists(index="restaurants")
                            
        print ('alreadyExists', alreadyExists)
        
        if alreadyExists:
            es.index(index="restaurants", doc_type="Restaurant", body=dataObject, refresh=True)
        else:
            es.create(index="restaurants", doc_type="Restaurant", body=dataObject)
