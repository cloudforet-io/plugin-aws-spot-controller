from schematics.models import Model
from schematics.types import ListType, DictType, StringType
from schematics.types.compound import ModelType

import json

__all__ = ['PluginInitResponse']

_SUPPORTED_RESOURCE_TYPE = [
    'inventory.CloudService?provider=aws&cloud_service_group=EC2&cloud_service_type=AutoScalingGroup'
]

_INTERRUPT_TOKEN_KEYS = ['data.account_id', 'region_code']

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
                    'Next': 'Finish'
                }
            ]
        },
        'createSpotInstance': {
            'Type': 'Choice',
            'RequestType': 'byPass',
            'RequestTarget': 'aws-spot-controller',
            'ChoiceVariable': 'choice_response',
            'Choices': [
                {
                    'StringEquals': 'Success',
                    'Next': 'IsCreatedSpotInstance'
                },
                {
                    'StringEquals': 'Fail',
                    'Next': 'Fail'
                }
            ]
        },
        'IsCreatedSpotInstance': {
            'Type': 'Task',
            'RequestType': 'byPass',
            'RequestTarget': 'aws-spot-controller',
            'Next': 'replaceOnDemandInstanceWithSpot',
            'Retry': {
                'IntervalSeconds': 15,
                'MaxAttempts': 100
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
        'Finish': {
            'Type': 'Succeed'
        }
    }
}

class PluginMetadata(Model):
    supported_resource_type = ListType(StringType, default=_SUPPORTED_RESOURCE_TYPE)
    interrupt_token_keys = ListType(StringType, default=_INTERRUPT_TOKEN_KEYS)
    template_json = json.dumps(_TEMPLATE)
    template = StringType(required=True, default=template_json)

class PluginInitResponse(Model):
    _metadata = ModelType(PluginMetadata, default=PluginMetadata, serialized_name='metadata')
