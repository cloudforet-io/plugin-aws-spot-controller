from schematics.models import Model
from schematics.types import ListType, DictType, StringType
from schematics.types.compound import ModelType

import json

__all__ = ['PluginInitResponse']

_SUPPORTED_RESOURCE_TYPE = [
    'inventory.CloudService?provider=aws&cloud_service_group=EC2&cloud_service_type=AutoScalingGroup'
]

_TEMPLATE = {
    'StartAt': 'getAnyUnprotectedOndemandInstance',
    'States': {
        'getAnyUnprotectedOndemandInstance': {
            'Type': 'Task',
            'RequestType': 'byPass',
            'RequestTarget': 'aws-spot-controller',
            'Next': 'hasOndemandInstance'
        },
        'hasOndemandInstance': {
            'Type': 'Choice',
            'Choices': [
                {
                    'Valiable': 'response',
                    'StringEquals': 'Success',
                    'RequestType': 'byPass',
                    'RequestTarget': 'aws-spot-controller',
                    'Next': 'requestQueryToGetInstanceSpec'
                },
                {
                    'Valiable': 'response',
                    'StringEquals': 'Fail',
                    'RequestType': 'byPass',
                    'RequestTarget': 'aws-spot-controller',
                    'Next': 'finish'
                }
            ]
        },
        'requestQueryToGetInstanceSpec': {
            'Type': 'Task',
            'RequestType': 'Query',
            'RequestTarget': 'aws-spot-worker',
            'Next': 'requestQueryToGetCandidateInfo',
            'Query': 'select * from table where instanceType == {instanceType}'
        },
        'requestQueryToGetCandidateInfo': {
            'Type': 'Task',
            'RequestType': 'Query',
            'RequestTarget': 'aws-spot-worker',
            'Next': 'createSpotInstance',
            'Query': 'select * from table where vCPU >= {vCPU} and GPU >= {GPU} and memory >= {memory} and EBSThroughput >= {EBSThroughput}'
        },
        'createSpotInstance': {
            'Type': 'Task',
            'RequestType': 'byPass',
            'RequestTarget': 'aws-spot-controller',
            'Next': 'IsCreatedSpotInstance'
        },
        'IsCreatedSpotInstance': {
            'Type': 'Task',
            'RequestType': 'byPass',
            'RequestTarget': 'aws-spot-controller',
            'Next': 'detachOndemandInstance',
            'Retry': {
                'Valiable': 'response',
                'StringEquals': 'Fail',
                'IntervalSeconds': 3,
                'MaxAttempts': 5
            }
        },
        'detachOndemandInstance': {
            'Type': 'Task',
            'RequestType': 'byPass',
            'RequestTarget': 'aws-spot-controller',
            'Next': 'attachSpotInstance'
        },
        'attachSpotInstance': {
            'Type': 'Task',
            'RequestType': 'byPass',
            'RequestTarget': 'aws-spot-controller',
            'Next': 'terminateOnDemandInstance'
        },
        'terminateOnDemandInstance': {
            'Type': 'Task',
            'RequestType': 'byPass',
            'RequestTarget': 'aws-spot-controller',
            'Next': 'finish'
        },
        'finish': {
            'Type': 'Succeed'
        }
    }
}

class PluginMetadata(Model):
    supported_resource_type = ListType(StringType, default=_SUPPORTED_RESOURCE_TYPE)
    template_json = json.dumps(_TEMPLATE)
    template = StringType(required=True, default=template_json)

class PluginInitResponse(Model):
    _metadata = ModelType(PluginMetadata, default=PluginMetadata, serialized_name='metadata')
