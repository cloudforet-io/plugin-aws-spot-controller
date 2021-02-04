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
            'Next': 'hasOndemandInstance'
        },
        'hasOndemandInstance': {
            'Type': 'Choice',
            'Choices': [
                {
                    'Valiable': 'response',
                    'StringEquals': 'Success',
                    'Next': 'requestQueryToGetInstanceSpec'
                },
                {
                    'Valiable': 'response',
                    'StringEquals': 'Fail',
                    'Next': 'finish'
                }
            ]
        },
        'requestQueryToGetInstanceSpec': {
            'Type': 'RequestQuery',
            'Next': 'requestQueryToGetCandidateInfo',
            'Query': 'select * from table where instanceType == {instanceType}'
        },
        'requestQueryToGetCandidateInfo': {
            'Type': 'RequestQuery',
            'Next': 'createSpotInstance',
            'Query': 'select * from table where vCPU >= {vCPU} and GPU >= {GPU} and memory >= {memory} and EBSThroughput >= {EBSThroughput}'
        },
        'createSpotInstance': {
            'Type': 'Task',
            'Next': 'IsCreatedSpotInstance'
        },
        'IsCreatedSpotInstance': {
            'Type': 'Task',
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
            'Next': 'attachSpotInstance'
        },
        'attachSpotInstance': {
            'Type': 'Task',
            'Next': 'terminateOnDemandInstance'
        },
        'terminateOnDemandInstance': {
            'Type': 'Task',
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
