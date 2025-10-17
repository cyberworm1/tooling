# Python script to simulate queue metrics push (for testing hybrid integration). Use AWS SDK.
import boto3
import random
import time

cloudwatch = boto3.client('cloudwatch')

def simulate_render_metrics(queue_name, duration_minutes=5):
    for _ in range(duration_minutes):
        depth = random.randint(50, 200)  # Simulate varying queue
        cloudwatch.put_metric_data(
            Namespace='AWS/Batch',
            MetricData=[{
                'MetricName': 'JobQueueDepth',
                'Dimensions': [{'Name': 'JobQueueName', 'Value': queue_name}],
                'Value': depth,
                'Unit': 'Count'
            }]
        )
        time.sleep(60)  # Minute intervals

# Usage: simulate_render_metrics("render-queue")