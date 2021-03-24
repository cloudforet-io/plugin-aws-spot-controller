__all__ = ["EventsConnector"]

import boto3
from boto3.session import Session
import datetime
import logging

from spaceone.core.error import *
from spaceone.core import utils
from spaceone.core import pygrpc 
from spaceone.core.utils import parse_endpoint
from spaceone.core.connector import BaseConnector

_LOGGER = logging.getLogger(__name__)
DEFAULT_REGION = 'us-east-1'
PAGINATOR_MAX_ITEMS = 10000
PAGINATOR_PAGE_SIZE = 50
RESOURCES = ['cloudformation', 'cloudwatch', 'dynamodb', 'ec2', 'glacier', 'iam', 'opsworks', 's3', 'sns', 'sqs']

class EventsConnector(BaseConnector):

    def __init__(self, transaction=None, config=None):
        self.session = None
        self.events_client = None

    def verify(self, secret_data):
        self.set_connect(secret_data)
        return "ACTIVE"

    def set_connect(self, secret_data, service="events"):
        region_name = secret_data['region_name']
        session = self.get_session(secret_data)
        aws_conf = {}
        aws_conf['region_name'] = region_name

        if service in RESOURCES:
            resource = session.resource(service, **aws_conf)
            client = resource.meta.client
        else:
            resource = None
            client = session.client(service, region_name=region_name)
        return client, resource

    def get_session(self, secret_data):
        region_name = secret_data['region_name']
        params = {
            'aws_access_key_id': secret_data['aws_access_key_id'],
            'aws_secret_access_key': secret_data['aws_secret_access_key'],
            'region_name': region_name
        }
        _LOGGER.debug(f'[EventsConnector] get_session params : {params}')

        session = Session(**params)

        # ASSUME ROLE
        if role_arn := secret_data.get('role_arn'):
            sts = session.client('sts')
            assume_role_object = sts.assume_role(RoleArn=role_arn,
                                                 RoleSessionName=utils.generate_id('AssumeRoleSession'))
            credentials = assume_role_object['Credentials']

            assume_role_params = {
                'aws_access_key_id': credentials['AccessKeyId'],
                'aws_secret_access_key': credentials['SecretAccessKey'],
                'region_name': region_name,
                'aws_session_token': credentials['SessionToken']
            }
            session = Session(**assume_role_params)

        return session

    def set_client(self, secret_data):
        self.session = self.get_session(secret_data)
        self.events_client = self.session.client('events')

    def put_rule(self, rule_name, event_pattern):
        try:
            response = self.events_client.put_rule(Name=rule_name, EventPattern=event_pattern)
            _LOGGER.debug(f'[EventsConnector] put_rule response : {response}')
            return response
        except Exception as e:
            _LOGGER.error(f'[EventsConnector] put_rule error: {e}')

    def put_targets(self, rule_name, targets):
        try:
            response = self.events_client.put_targets(Rule=rule_name, Targets=targets)
            _LOGGER.debug(f'[EventsConnector] put_targets response : {response}')
            return response
        except Exception as e:
            _LOGGER.error(f'[EventsConnector] put_targets error: {e}')