# Spot automation connector

**Plugin to control spot automation**

---
## EC2
### Connecting Contents

- Contents
  - Instance
  
- Boto3 info
  - Client : ec2
  - API used
    - [describe_instances()](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#EC2.Client.describe_instances)
    - [describe_instance_status()](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#EC2.Client.describe_instance_status)
    - [run_instances()](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#EC2.Client.run_instances)
    - [terminate_instances()](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#EC2.Client.terminate_instances)
    - [describe_launch_template_versions()](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#EC2.Client.describe_launch_template_versions)
    - [describe_spot_price_history()](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#EC2.Client.describe_spot_price_history)
    

### Required Policy
  
<pre>
<code>
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Action": [
                "ec2:Describe*",
                "ec2:RunInstances",
                "ec2:TerminateInstances"
            ],
            "Effect": "Allow",
            "Resource": "*"
        }
    ]
}
</code>
</pre>

---
## ASG
### Connecting Contents

- Contents
  - Auto Scaling
  
- Boto3 info
  - Client : autoscaling
  - API used
    - [describe_auto_scaling_groups()](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/autoscaling.html#AutoScaling.Client.describe_auto_scaling_groups)
    - [describe_auto_scaling_instances()](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/autoscaling.html#AutoScaling.Client.describe_auto_scaling_instances)
    - [detach_instances()](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/autoscaling.html#AutoScaling.Client.detach_instances)
    - [attach_instances()](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/autoscaling.html#AutoScaling.Client.attach_instances)
    - [describe_launch_configurations()](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/autoscaling.html#AutoScaling.Client.describe_launch_configurations)
    - [update_auto_scaling_group()](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/autoscaling.html#AutoScaling.Client.update_auto_scaling_group)
    

### Required Policy
  
<pre>
<code>
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Action": [
                "autoscaling:Describe*",
                "autoscaling:DeTachInstances",
                "autoscaling:AttachInstances",
                "autoscaling:UpdateAutoScalingGroup",
            ],
            "Effect": "Allow",
            "Resource": "*"
        }
    ]
}
</code>
</pre>


---
## Event Bridge
### Connecting Contents

- Contents
  - Event Bridge
  
- Boto3 info
  - Client : events
  - API used
    - [put_rule()](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/events.html#EventBridge.Client.put_rule)
    - [put_targets()](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/events.html#EventBridge.Client.put_targets)
    

### Required Policy
  
<pre>
<code>
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Action": [
                "events:Put*",
            ],
            "Effect": "Allow",
            "Resource": "*"
        }
    ]
}
</code>
</pre>

---
## Pricing
### Connecting Contents

- Contents
  - Pricing
  
- Boto3 info
  - Client : pricing
  - API used
    - [get_products()](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/pricing.html#Pricing.Client.get_products)
    

### Required Policy
  
<pre>
<code>
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Action": [
                "pricing:Get*",
            ],
            "Effect": "Allow",
            "Resource": "*"
        }
    ]
}
</code>
</pre>

---
## SNS
### Connecting Contents

- Contents
  - Subscription
  
- Boto3 info
  - Client : sns
  - API used
    - [create_topic()](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sns.html#SNS.Client.create_topic)
    - [subscribe()](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sns.html#SNS.Client.subscribe)

### Required Policy
  
<pre>
<code>
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Action": [
                "sns:CreateTopic",
                "sns:Subscribe",
            ],
            "Effect": "Allow",
            "Resource": "*"
        }
    ]
}
</code>
</pre>