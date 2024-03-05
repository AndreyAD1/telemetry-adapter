# Telemetry Adapter
This is a service that receives telemetry messages from [an SQS queue](https://docs.aws.amazon.com/sqs/), 
converts messages into events, and sends the events to [a Kinesis stream](https://docs.aws.amazon.com/kinesis/).

## Motivation
When processing device telemetry submissions, we encounter several risks:
1. Invalid and/or malicious submissions;
2. Low performance and difficulties with delivering data to multiple consumers 
(a fan-out delivery).
3. Submission duplicates (a standard SQS queue guarantees at least one delivery, 
so multiple consumers might receive the same submission).

Using this service with a Kinesis stream helps mitigate these risks.

## Design
### Description
The application consists of two parts: an HTTP server and a worker processing
SQS messages. 

Currently, an HTTP server provides only a healthcheck endpoint
based on a worker status.

The worker polls an SQS queue, parses, and validates messages. Afterwards,
the worker asynchronously processes all received messages. The worker stores the state
of every submission in a PostgreSQL database so that a Kinesis and/or network
outage will have a minimal impact on an event order and an event number (see image). 
Additionally, the state storage helps avoid duplicates in case two workers receive 
the same submission simultaneously.

![telemetry-adapter.png](telemetry-adapter.png)

## Getting Started
1. Install [Docker](https://docs.docker.com/get-docker/).
2. Configure an SQS queue and a Kinesis stream.
3. Set your configurations in a file [.env](.env). 
Alternatively, you can set parameters when you start a container.
4. Build a Docker image.
   ```shell
   docker build . --tag telemetry-adapter
   ```
5. Run the service container.
   ```shell
   docker run telemetry-adapter
   ```
   If everything works fine, you can see application log notes and 
   consume messages from a Kinesis stream.

## Development
### Run in a Testing Environment
Follow these steps to run a testing environment.
1. Install [Docker](https://docs.docker.com/get-docker/).
2. Go to the upper directory and execute this command:
    ```shell
    docker compose up --build
    ```
   This command will run device emulators (`sensor-fleet`), an SQS queue,
   a Kinesis stream (`localstack`), this service, and its database.
3. When you update a service code, the application will immediately restart with
the updated code.

### Tests
TODO: There are no tests in the project yet.

## Outgoing event data format example
```json
{
   "id":"169a9a74-cd8f-446a-9803-d2786e01b2c6",
   "event_type":"network_connection",
   "device_id":"154ef306-c788-4934-9489-118173e4ea1a",
   "processing_timestamp":"2024-03-05T01:49:51.260080Z",
   "event_details": {
      "source_ip":"192.168.0.1",
      "destination_ip":"142.250.74.110",
      "destination_port":23680
   }
}
```

## Design questions and answers
#### How does your application scale and guarantee near-realtime processing when the incoming traffic increases?

Upscale option:
1. Increasing the number of messages received from SQS in one request (`MAX_MESSAGE_NUMBER_BY_REQUEST`).
2. Increasing connection pool size (`MIN_POOL_SIZE` and `MAX_POOL_SIZE`). 
[Read more](https://www.psycopg.org/psycopg3/docs/advanced/pool.html#what-s-the-right-size-for-the-pool).
3. Deploying several application instances.

#### Where are the possible bottlenecks and how to tackle those?
The main bottleneck seems to be the effective number of open database connections 
and/or database interactions. 
This application needs speed and does not require much consistency. 
So, NoSQL databases are likely to fit this application better.

#### What kind of metrics you would collect from the application to get visibility to its througput, performance and health?
1. Latency of processing an SQS message batch.
2. Requests per second to SQS and Kinesis.
3. Difference between received and deleted SQS messages.
4. An SQS queue size.
5. Number of open and used database connections.
6. Response time of database queries.
7. CPU and memory usage.

#### How would you deploy your application in a real world scenario?
Kubernetes autoscaling workloads or an AWS autoscaling group in a private subnet.
Connections with a scalable database cluster.

#### What kind of testing, deployment stages or quality gates you would build to ensure a safe production deployment?
Pre-build stage:
- static analysis, type checkers;
- unit tests;
- "grey-box" tests that check database interactions.

Component tests:
- configuration tests;
- component tests verifying conversions from SQS responses to event messages;
- component integration tests, checking contracts between a device, an adapter, and consumers.

Testing environment that mimics a production environment:
- system functional tests from test devices to telemetry consumers;
- performance tests, checking the expected payload;
- security tests.
