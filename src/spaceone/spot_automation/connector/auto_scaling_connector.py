__all__ = ["AutoScalingConnector"]

import boto3
import botocore
from boto3.session import Session
import logging

from spaceone.core.error import *
from spaceone.core import utils
from spaceone.core import pygrpc 
from spaceone.core.utils import parse_endpoint
from spaceone.core.connector import BaseConnector

_LOGGER = logging.getLogger(__name__)

class AutoScalingConnector(BaseConnector):

    def __init__(self, transaction=None, config=None):
        self.session = None
        self.asg_client = None

    def get_session(self, secret_data):
        region_name = secret_data['region_name']
        params = {
            'aws_access_key_id': secret_data['aws_access_key_id'],
            'aws_secret_access_key': secret_data['aws_secret_access_key'],
            'region_name': region_name
        }

        session = Session(**params)
        _LOGGER.debug(f'[AutoScalingConnector] get_session session : {session}')

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
        self.asg_client = self.session.client('autoscaling')

    def get_asg(self, asg_name):
        try:
            response = self.asg_client.describe_auto_scaling_groups(
                AutoScalingGroupNames=[
                    asg_name,
                ],
            )
            _LOGGER.debug(f'[AutoScalingConnector] get_asg response : {response}')
            return response['AutoScalingGroups'][0]
        except Exception as e:
            _LOGGER.error(f'[AutoScalingConnector] get_asg error: {e}')

    def get_asg_instances(self, instance_id):
        try:
            response = self.asg_client.describe_auto_scaling_instances(
                InstanceIds=[
                    instance_id,
                ],
            )
            _LOGGER.debug(f'[AutoScalingConnector] get_asg_instances response : {response}')
            return response['AutoScalingInstances'][0]
        except Exception as e:
            _LOGGER.error(f'[AutoScalingConnector] get_asg_instances error: {e}')

    def detach_instances(self, instance_id, asg_name):
        try:
            response = self.asg_client.detach_instances(
                AutoScalingGroupName=asg_name,
                InstanceIds=[
                    instance_id,
                ],
                ShouldDecrementDesiredCapacity=True
            )
            _LOGGER.debug(f'[AutoScalingConnector] detach_instances response : {response}')
        except Exception as e:
            _LOGGER.error(f'[AutoScalingConnector] detach_instances error: {e}')

    def attach_instances(self, instance_id, asg_name):
        try:
            response = self.asg_client.attach_instances(
                AutoScalingGroupName=asg_name,
                InstanceIds=[
                    instance_id,
                ]
            )
            _LOGGER.debug(f'[AutoScalingConnector] attach_instances response : {response}')
        except Exception as e:
            _LOGGER.error(f'[AutoScalingConnector] attach_instances error: {e}')

    def describe_launch_configurations(self, lc_name):
        try:
            response = self.asg_client.describe_launch_configurations(
                LaunchConfigurationNames=[
                    lc_name,
                ],
            )
            _LOGGER.debug(f'[AutoScalingConnector] describe_launch_configurations response : {response}')
            return response['LaunchConfigurations'][0]
        except Exception as e:
            _LOGGER.error(f'[AutoScalingConnector] describe_launch_configurations error: {e}')