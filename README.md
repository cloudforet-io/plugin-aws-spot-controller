# plugin-aws-spot-automation-controller

**Plugin to control spot automation**

> SpaceONE's plugin-aws-spot-automation-controller is a convenient tool to manage spot instance automatically from AWS.

---

## Collecting Contents

* Table of Contents
    * [Auto Scaling Group](/src/spaceone/spot_automation/connector/README.md)
        * Auto Scaling
    * [EC2](/src/spaceone/spot_automation/connector/README.md)
        * Instance
    * [Event Bridge](/src/spaceone/spot_automation/connector/README.md)
        * Event Bridge
    * [Pricing](/src/spaceone/spot_automation/connector/README.md)
        * Pricing
    * [SNS](/src/spaceone/spot_automation/connector/README.md)
        * Subscription

---
## Authentication Overview

Registered service account on SpaceONE must have certain permissions to use spot automation. 
Please, set authentication privilege for followings:

<pre>
<code>
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Action": [
                "ec2:Describe*",
                "ec2:RunInstances",
                "ec2:TerminateInstances",
                "autoscaling:Describe*",
                "autoscaling:DeTachInstances",
                "autoscaling:AttachInstances",
                "autoscaling:UpdateAutoScalingGroup",
                "events:Put*",
                "pricing:Get*",
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
