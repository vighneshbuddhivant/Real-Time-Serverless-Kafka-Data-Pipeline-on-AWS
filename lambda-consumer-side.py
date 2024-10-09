from time import sleep
from json import dumps
from kafka import KafkaProducer

topic_name = 'demo_testing1'
producer = KafkaProducer(bootstrap_servers=['b-1.mskprojectproducerclu.b88034.c3.kafka.ap-south-1.amazonaws.com:9092','b-2.mskprojectproducerclu.b88034.c3.kafka.ap-south-1.amazonaws.com:9092'], value_serializer=lambda x: dumps(x).encode('utf-8'))

for e in range(1000):
    data = {'number': e}
    print(data)
    producer.send(topic_name, value=data)
    sleep(1)