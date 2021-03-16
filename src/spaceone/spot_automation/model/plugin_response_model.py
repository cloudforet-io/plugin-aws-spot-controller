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
            'Type': 'Choice',
            'RequestType': 'byPass',
            'RequestTarget': 'aws-spot-controller',
            'ChoiceVariable': 'choice_response',
            'Choices': [
                {
                    'StringEquals': 'Success',
                    'Next': 'createSpotInstance'
                },
                {
                    'StringEquals': 'Fail',
                    'Next': 'finish'
                }
            ]
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
            'Next': 'replaceOnDemandInstanceWithSpot',
            'Retry': {
                'IntervalSeconds': 15,
                'MaxAttempts': 5
            }
        },
        'replaceOnDemandInstanceWithSpot': {
            'Type': 'Task',
            'RequestType': 'byPass',
            'RequestTarget': 'aws-spot-controller',
            'Next': 'terminateOnDemandInstance'
        },
        'terminateOnDemandInstance': {
            'Type': 'Task',
            'RequestType': 'byPass',
            'RequestTarget': 'aws-spot-controller',
            'IntervalSeconds': 60,
            'Next': 'getAnyUnprotectedOndemandInstance'
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
