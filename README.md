# Real Time Serverless Kafka Data Pipeline on AWS Cloud

## Project Overview
This project implements a **Serverless Kafka Data Pipeline** using AWS services. It leverages Amazon MSK Serverless for Kafka management, AWS Lambda for data processing, API Gateway for API management, SQS for load balancing, Kinesis Firehose for data batching, and S3 for storage. The pipeline facilitates real-time data streaming from external applications to data warehouses like Snowflake or querying services like Athena using AWS Glue.

## Architecture Diagram
![Architecture Diagram]()

## Architecture Details
1. **Data Producers:** External applications (e.g., mobile devices) send data via POST requests to an API managed by API Gateway.
2. **API Gateway:** Receives POST requests and forwards data to SQS for load balancing.
3. **SQS:** Queues incoming data, ensuring smooth handling of high data volumes.
4. **Producer Lambda:** Triggered by SQS, reads messages, and sends them to Kafka topics in the Amazon MSK Serverless cluster.
5. **Consumer Lambda:** Triggered by Kafka topics, consumes messages, batches them using Kinesis Firehose, and flushes them to S3.
6. **Kinesis Firehose:** Buffers data and periodically flushes it to S3 for storage.
7. **Data Storage and Processing:** Data stored in S3 can be loaded into data warehouses like Snowflake or queried using Athena via AWS Glue ETL jobs.
   
## Tools and Technologies
- **AWS Services:**
  - Amazon MSK Serverless
  - AWS Lambda
  - Amazon API Gateway
  - Amazon SQS
  - Amazon Kinesis Firehose
  - Amazon S3
  - AWS Glue
  - Amazon Athena
  - Amazon VPC, Subnets, NAT Gateway, Internet Gateway
- **Programming Languages:**
  - Python 3.8
- **Other Tools:**
  - `kafka-python` library
  - AWS CLI
  - GitHub for version control



## Setup and Deployment

### 1. Create VPC
- **Name:** `virtual-private-cloud-lambda`
- **IPv4 CIDR:** `11.0.0.0/16`
- **Host Address Range:** `11.0.0.1 - 11.0.255.254`

### 2. Create Subnets
- **Public Subnets:**
  - `Public-Subnet-A-lambda` — `11.0.0.0/24` (Host range: `11.0.0.1 - 11.0.0.254`)
  - `Public-Subnet-B-lambda` — `11.0.1.0/24` (Host range: `11.0.1.1 - 11.0.1.254`)
  
- **Private Subnets:**
  - `Private-Subnet-A-lambda` — `11.0.2.0/24` (Host range: `11.0.2.1 - 11.0.2.254`)
  - `Private-Subnet-B-lambda` — `11.0.3.0/24` (Host range: `11.0.3.1 - 11.0.3.254`)


### 3. Configure Internet Gateway and Route Tables
1. **Create Internet Gateway:**
   - **Name:** `InternetGateway-Lambda`
   - **Attach to VPC:** `virtual-private-cloud-lambda`
   
2. **Create Route Tables:**
   - **Public Route Table:**
     - **Routes:** `0.0.0.0/0` → `InternetGateway-Lambda`
     - **Associations:** `Public-Subnet-A-lambda`, `Public-Subnet-B-lambda`
     
   - **Private Route Table:**
     - **Routes:** `0.0.0.0/0` → `NAT Gateway` (to be created)
     - **Associations:** `Private-Subnet-A-lambda`, `Private-Subnet-B-lambda`

### 4. Create NAT Gateway
- **Location:** Deploy in `Public-Subnet-A-lambda`
- **Elastic IP:** Allocate a new Elastic IP for the NAT Gateway
- **Attach to Private Route Table:** Ensure private subnets route outbound traffic through the NAT Gateway


### 5. Deploy Amazon MSK Cluster
1. **Create MSK Cluster:**
   - **Type:** Amazon MSK Serverless
   - **VPC:** `virtual-private-cloud-lambda`
   - **Subnets:** `Private-Subnet-A-lambda`, `Private-Subnet-B-lambda`
   - **Security Groups:** Configure to allow traffic from Lambda functions

2. **Ensure High Availability:**
   - Deploy MSK across a minimum of two Availability Zones within your preferred region.

3. **Security Best Practices:**
   - Deploy MSK brokers in private subnets to enhance security.
  
![](https://github.com/vighneshbuddhivant/Real-Time-Serverless-Kafka-Data-Pipeline-on-AWS/blob/14747f7dd1103f33a2f05195a2dafdf5e4a5a21b/msk-cluster.png) 

### 6. Create Lambda Functions

#### Producer Lambda
**Purpose:** Reads messages from SQS and publishes them to Kafka topics in the MSK cluster.

**Code:**

```python
from json import dumps
from kafka import KafkaProducer
import json

topic_name = '{Provide the topic name here}'
producer = KafkaProducer(
    bootstrap_servers=[
        'b-1.msklambdaproject.00frff.c3.kafka.ap-south-1.amazonaws.com:9092',
        'b-2.msklambdaproject.00frff.c3.kafka.ap-south-1.amazonaws.com:9092'
    ],
    value_serializer=lambda x: dumps(x).encode('utf-8')
)

def lambda_handler(event, context):
    print(event)
    for record in event['Records']:
        sqs_message = json.loads(record['body'])
        print(sqs_message)
        producer.send(topic_name, value=sqs_message)
    
    producer.flush()
```

**Configuration:**
- **Timeout:** Increase to 2 minutes to accommodate potential delays in processing SQS messages.
- **VPC Configuration:** Ensure the Lambda function has access to the VPC, subnets, and security groups where MSK is deployed.


#### Consumer Lambda
**Purpose:** Consumes messages from Kafka topics in the MSK cluster and batches them using Kinesis Firehose before storing in S3.

**Code:**

```python
import base64
import boto3
import json

client = boto3.client('firehose')

def lambda_handler(event, context):
    print(event)
    for partition_key in event['records']:
        partition_value = event['records'][partition_key]
        for record_value in partition_value:
            actual_message = json.loads(base64.b64decode(record_value['value']).decode('utf-8'))
            print(actual_message)
            newImage = (json.dumps(actual_message) + '\n').encode('utf-8')
            print(newImage)
            response = client.put_record(
                DeliveryStreamName='PUT-S3-t0zZu',
                Record={
                    'Data': newImage
                }
            )
```

**Configuration:**
- **VPC Configuration:** Ensure the Lambda function is **not** running in the same VPC as the MSK cluster (as per the note).
- **Permissions:** Grant necessary permissions for Kinesis Firehose, VPC access, and MSK access.

### 7. Create Lambda Layer for `kafka-python`
Since the `kafka-python` module is not available by default in AWS Lambda, you need to create a Lambda layer containing this library.

**Steps:**

1. **Start WSL (Windows Subsystem for Linux):**
   ```bash
   wsl
   ```

2. **Update Package Lists:**
   ```bash
   sudo apt-get update
   ```

3. **Install `virtualenv`:**
   ```bash
   sudo apt install python3-virtualenv
   ```

4. **Create a Virtual Environment:**
   ```bash
   virtualenv kafka_yt
   ```

5. **Activate the Virtual Environment:**
   ```bash
   source kafka_yt/bin/activate
   ```

6. **Check Python Version:**
   ```bash
   python3 --version
   ```

7. **Install `pip` (if not already installed):**
   ```bash
   sudo apt install python3-pip
   ```

8. **Upgrade `pip`:**
   ```bash
   python3 -m pip install --upgrade pip
   ```

9. **Create Directory for Lambda Layer:**
   ```bash
   mkdir -p lambda_layers/python/lib/python3.8/site-packages
   ```

10. **Navigate to the `site-packages` Directory:**
    ```bash
    cd lambda_layers/python/lib/python3.8/site-packages
    ```

11. **Install `kafka-python` to the `site-packages` Directory:**
    ```bash
    pip install kafka-python -t .
    ```

12. **Install `zip` (if not already installed):**
    ```bash
    sudo apt install zip
    ```

13. **Zip the Lambda Layer:**
    ```bash
    cd ../../../..
    zip -r kafka_layer.zip python
    ```

14. **Upload the Lambda Layer to S3:**
    - Upload `kafka_layer.zip` to an S3 bucket (e.g., `msk-lambda-pipeline-bucket`).

15. **Create Lambda Layer in AWS:**
    - Navigate to **AWS Lambda** > **Layers** > **Create Layer**.
    - **Name:** `kafka-layer`
    - **Upload Zip File:** Provide the S3 link to `kafka_layer.zip`.
    - **Compatible Runtimes:** Python 3.8

16. **Attach the Layer to Lambda Functions:**
    - Go to your Lambda functions and add the `kafka-layer` under the **Layers** section.

### 8. Set Up API Gateway and SQS Integration
1. **Create API Gateway:**
   - **Type:** REST API
   - **Name:** `KafkaDataPipelineAPI`

2. **Create IAM Role for API Gateway:**
   - **Role Name:** `api-gateway-role`
   - **Permissions:** Grant permissions to publish messages to SQS.

3. **Create SQS Queue:**
   - **Name:** `KafkaDataPipelineQueue`

4. **Configure Integration:**
   - **Integration Type:** AWS Service
   - **Service:** SQS
   - **Action:** `SendMessage`
   - **Resource:** `KafkaDataPipelineQueue`

5. **Create Route:**
   - **Method:** POST
   - **Path:** `/publisher`
   - **Integration:** Link to SQS using the created role.

6. **Deploy API:**
   - **Stage Name:** `prod`
   - **Invoke URL Example:** `https://7n5otnhjjg.execute-api.ap-south-1.amazonaws.com/prod/publisher`

### 9. Configure Kinesis Firehose
1. **Create S3 Bucket for Data Storage:**
   - **Bucket Name:** `msk-lambda-pipeline-bucket`

2. **Create Kinesis Firehose Delivery Stream:**
   - **Name:** `MSKToS3Firehose`
   - **Source:** Direct PUT
   - **Destination:** S3 (`msk-lambda-pipeline-bucket`)

3. **Configure Buffer Settings:**
   - Set appropriate buffer sizes and interval to batch data before flushing to S3.

### 10. Set Up Kafka on EC2
**Purpose:** Manage Kafka topics within the MSK cluster.

**Steps:**

1. **Launch EC2 Instances:**
   - **Public EC2:** For SSH access and as a bastion host.
   - **Private EC2:** For managing Kafka topics within the private subnet.

2. **Configure Security Groups:**
   - **Public EC2 Security Group:** Allow inbound SSH (port 22) from your IP.
   - **Private EC2 Security Group:** Allow all traffic from Public EC2 and MSK Security Groups.

3. **SSH into Public EC2:**
   - Use PuTTY or your preferred SSH client with the EC2 instance's IPv4 address and key pair.

4. **Access Private EC2 from Public EC2:**
   - SSH from Public EC2 to Private EC2 using its private IP address.

5. **Install Java on Private EC2:**
   ```bash
   sudo amazon-linux-extras enable corretto8
   sudo yum install -y java-1.8.0-amazon-corretto-devel
   ```

6. **Download and Extract Kafka:**
   ```bash
   wget https://archive.apache.org/dist/kafka/3.5.1/kafka_2.12-3.5.1.tgz
   tar -xzf kafka_2.12-3.5.1.tgz
   cd kafka_2.12-3.5.1
   ```

7. **Create Kafka Topic:**
   ```bash
   bin/kafka-topics.sh --create --topic demo_testing1 --bootstrap-server b-1.msklambdaproject.00frff.c3.kafka.ap-south-1.amazonaws.com:9092,b-2.msklambdaproject.00frff.c3.kafka.ap-south-1.amazonaws.com:9092 --replication-factor 1 --partitions 1
   ```

8. **Start Kafka Console Consumer:**
   ```bash
   bin/kafka-console-consumer.sh --topic demo_testing1 --bootstrap-server b-1.msklambdaproject.00frff.c3.kafka.ap-south-1.amazonaws.com:9092,b-2.msklambdaproject.00frff.c3.kafka.ap-south-1.amazonaws.com:9092
   ```

   - **Testing:** Send a POST request via Postman to the API Gateway endpoint and verify that messages appear in the Kafka console consumer.

### Conclusion
This project demonstrates a robust, serverless data pipeline leveraging AWS services to handle real-time data streaming with Kafka. By utilizing Amazon MSK Serverless, Lambda functions, API Gateway, SQS, Kinesis Firehose, and S3, the pipeline ensures scalability, high availability, and efficient data processing. The architecture adheres to best practices for security and scalability, making it suitable for production environments. Future enhancements can include integrating data analytics tools, implementing monitoring and alerting, and optimizing for cost and performance.
