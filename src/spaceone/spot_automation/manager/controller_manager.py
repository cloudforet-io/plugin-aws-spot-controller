__all__ = ['ControllerManager']

import time
import logging
import json

from spaceone.core.manager import BaseManager


_LOGGER = logging.getLogger(__name__)

DEFAULT_REGION = 'us-east-1'

class ControllerManager(BaseManager):

    def __init__(self, transaction):
        super().__init__(transaction)

    def verify(self, secret_data, region_name):
        """ Check connection
        """
        ec2_connector = self.locator.get_connector('EC2Connector')
        r = ec2_connector.verify(secret_data, region_name)
        # ACTIVE/UNKNOWN
        return r

    def patch(self, secret_data, action, command):
        _LOGGER.debug(f'[patch] action: {action}')
        _LOGGER.debug(f'[patch] command: {command}')
        return {}
