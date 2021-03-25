__all__ = ["PricingConnector"]

import json
import time
import botocore
import boto3
from boto3.session import Session
import datetime
import logging

from spaceone.core.error import *
from spaceone.core import utils
from spaceone.core import pygrpc 
from spaceone.core.connector import BaseConnector

_LOGGER = logging.getLogger(__name__)

PRICING_REGION_NAME = 'ap-south-1'

class PricingConnector(BaseConnector):
    default_location = "Asia Pacific (Seoul)"
    aws_region_to_location_dict = {
        'us-east-2': 'US East (Ohio)',
        'us-east-1': 'US East (N. Virginia)',
        'us-west-1': 'US West (N. California)',
        'us-west-2': 'US West (Oregon)',
        'ap-east-1': 'Asia Pacific (Hong Kong)',
        'ap-south-1': 'Asia Pacific (Mumbai)',
        'ap-northeast-3': 'Asia Pacific (Osaka-Local)',
        'ap-northeast-2': 'Asia Pacific (Seoul)',
        'ap-southeast-1': 'Asia Pacific (Singapore)',
        'ap-southeast-2': 'Asia Pacific (Sydney)',
        'ap-northeast-1': 'Asia Pacific (Tokyo)',
        'ca-central-1': 'Canada (Central)',
        'eu-central-1': 'EU (Frankfurt)',
        'eu-west-1': 'EU (Ireland)',
        'eu-west-2': 'EU (London)',
        'eu-west-3': 'EU (Paris)',
        'eu-north-1': 'EU (Stockholm)',
        'me-south-1': 'Middle East (Bahrain)',
        'sa-east-1': 'South America (Sao Paulo)',
    }

    def __init__(self, transaction=None, config=None):
        self.session = None
        self.pricing_client = None

    def get_session(self, secret_data):
        region_name = PRICING_REGION_NAME
        params = {
            'aws_access_key_id': secret_data['aws_access_key_id'],
            'aws_secret_access_key': secret_data['aws_secret_access_key'],
            'region_name': region_name
        }

        session = Session(**params)
        _LOGGER.debug(f'[get_session] get_session session : {session}')

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
        self.pricing_client = self.session.client('pricing')

    def get_products(self, instance_type, region):
        retry_count = 5
        while retry_count > 0:
            try:
                response = self.pricing_client.get_products(
                    ServiceCode='AmazonEC2',
                    Filters=[
                        {'Type': 'TERM_MATCH', 'Field': 'operatingSystem', 'Value': 'Linux'},
                        {'Type': 'TERM_MATCH', 'Field': 'capacitystatus', 'Value': 'Used'},
                        {'Type': 'TERM_MATCH', 'Field': 'instanceType', 'Value': instance_type},
                        {'Type': 'TERM_MATCH', 'Field': 'tenancy', 'Value': 'Shared'},
                        {'Type': 'TERM_MATCH', 'Field': 'location', 'Value': self._get_location(region=region)},
                        {'Type': 'TERM_MATCH', 'Field': 'operation', 'Value': 'RunInstances'},
                    ],
                )
                break
            except botocore.exceptions.ClientError as e:
                _LOGGER.error('pricing get_products api return error', error=e, retry_count=5 - retry_count,
                              resource_name='ec2', instance_type=instance_type, region=region)
                retry_count -= 1
                time.sleep(3)

        if retry_count == 0:
            raise Exception('Exceed Retry Count(5)')

        price_list = response['PriceList']

        if not price_list:
            _LOGGER.error('ec2 price list is empty', instance_type=instance_type, region=region,
                          location=self._get_location(region=region))
            return 0

        price_item = json.loads(price_list[0])
        terms = price_item['terms']

        term = iter(terms['OnDemand'].values()).__next__()
        price_dimension = iter(term['priceDimensions'].values()).__next__()
        price_per_unit = price_dimension['pricePerUnit']['USD']

        return price_per_unit

    ######################
    # Internal
    ######################

    def _get_location(self, region):
        return self.aws_region_to_location_dict[region] if region in self.aws_region_to_location_dict \
            else self.default_location
    