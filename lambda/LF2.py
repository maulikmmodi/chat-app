import json
import boto3
from elasticsearch import Elasticsearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth

def lambda_handler(event, context):
    sqs = boto3.client('sqs')
    queue_url = 'https://sqs.us-west-2.amazonaws.com/844243140541/food-bot-queue'

    # Receive message from SQS queue
    response = sqs.receive_message(
        QueueUrl=queue_url,
        AttributeNames=[
            'SentTimestamp'
        ],
        MaxNumberOfMessages=1,
        MessageAttributeNames=[
            'All'
        ],
        VisibilityTimeout=0,
        WaitTimeSeconds=0
    )
    
    if (response and 'Messages' in response):
        
        host = 'search-dining-suggestion-search-bzwynnc3fgpjqu2tlpou72tbre.us-west-2.es.amazonaws.com'
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
        
        for each_message in response['Messages']:
        
            message = each_message
            receipt_handle = message['ReceiptHandle']
            attributes = message['MessageAttributes']
            
            
            print (message)
            print (attributes)
            res_category = 'Mexican'
            searchData = es.search(index="restaurants", body={
                                                            "query": {
                                                                "match": {
                                                                    "categories": res_category
                                                                }}})
           
            print ('searchData', searchData)
            
            
            # Delete received message from queue
            # sqs.delete_message(
            #     QueueUrl=queue_url,
            #     ReceiptHandle=receipt_handle
            # )
            print('Received and deleted message: %s' % message)
    
    
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
