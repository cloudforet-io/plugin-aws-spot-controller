__all__ = ["SNSConnector"]

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

class SNSConnector(BaseConnector):

    def __init__(self, transaction=None, config=None):
        self.session = None
        self.sns_client = None

    def verify(self, secret_data):
        self.set_connect(secret_data)
        return "ACTIVE"

    def set_connect(self, secret_data, service="sns"):
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
        _LOGGER.debug(f'[SNSConnector] get_session params : {params}')

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
        self.sns_client = self.session.client('sns')

    def create_topic(self, topic_name):
        try:
            response = self.sns_client.create_topic(Name=topic_name)
            _LOGGER.debug(f'[SNSConnector] create_topic response : {response}')
            return response
        except Exception as e:
            _LOGGER.error(f'[SNSConnector] create_topic error: {e}')

    def subscribe(self, topic_arn, protocol, endpoint):
        try:
            response = self.sns_client.subscribe(TopicArn=topic_arn, Protocol=protocol, Endpoint=endpoint)
            _LOGGER.debug(f'[SNSConnector] subscribe response : {response}')
            return response
        except Exception as e:
            _LOGGER.error(f'[SNSConnector] subscribe error: {e}')