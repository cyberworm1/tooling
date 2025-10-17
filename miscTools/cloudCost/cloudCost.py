import boto3
from azure.mgmt.costmanagement import CostManagementClient
from azure.identity import DefaultAzureCredential
import matplotlib.pyplot as plt

# AWS part
ce = boto3.client('ce')
response = ce.get_cost_and_usage(TimePeriod={'Start': '2025-09-01', 'End': '2025-10-01'}, Granularity='MONTHLY', Metrics=['UnblendedCost'])

# Azure part (simplified)
credential = DefaultAzureCredential()
client = CostManagementClient(credential, subscription_id='your-sub-id')
query = client.query.usage(scope='/subscriptions/your-sub-id', parameters={...})  # Fill query params

# Plot (dummy data for example)
plt.bar(['AWS', 'Azure'], [1000, 800])
plt.savefig('cost_chart.png')