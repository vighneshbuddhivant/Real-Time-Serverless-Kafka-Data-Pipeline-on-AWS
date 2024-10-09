from time import sleep
from json import dumps
from kafka import KafkaProducer
import json


topic_name='{Provide the topic name here}'
producer = KafkaProducer(bootstrap_servers=['b-1.msklambdaproject.00frff.c3.kafka.ap-south-1.amazonaws.com:9092'
,'b-2.msklambdaproject.00frff.c3.kafka.ap-south-1.amazonaws.com:9092'],value_serializer=lambda x: dumps(x).encode('utf-8'))

def lambda_handler(event, context):
    print(event)
    for i in event['Records']:
        sqs_message =json.loads((i['body']))
        print(sqs_message)
        producer.send(topic_name, value=sqs_message)
    
    producer.flush()