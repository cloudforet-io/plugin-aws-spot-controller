import time
import logging
import concurrent.futures
import re

from spaceone.core.service import *
from spaceone.spot_automation.manager.controller_manager import ControllerManager
from spaceone.spot_automation.manager.plugin_manager import PluginManager

_LOGGER = logging.getLogger(__name__)
DEFAULT_REGION = 'us-east-1'
NUMBER_OF_CONCURRENT = 20

@authentication_handler
class ControllerService(BaseService):
    def __init__(self, metadata):
        super().__init__(metadata)
        self.controller_manager: ControllerManager = self.locator.get_manager('ControllerManager')
        self.plugin_manager: PluginManager = self.locator.get_manager('PluginManager')

    @check_required(['options'])
    def init(self, params):
        """ init plugin by options
        """
        return self.plugin_manager.init_response()

    @transaction
    @check_required(['options','secret_data'])
    @append_query_filter(['schema'])
    def verify(self, params):
        """ verify options capability
        Args:
            params
              - options
              - secret_data: may be empty dictionary

        Returns:

        Raises:
             ERROR_VERIFY_FAILED:
        """
        secret_data = params['secret_data']
        region_name = params.get('region_name', DEFAULT_REGION)
        active = self.controller_manager.verify(secret_data, region_name)

        return {}

    @transaction
    @check_required(['secret_data','action', 'command'])
    @append_query_filter(['schema'])
    def patch(self, params):
        """ verify options capability
        Args:
            params
              - secret_data: dict
              - action: string
              - command: dict
              - schema: string

        Returns:
        """
        secret_data = params['secret_data']
        action = params['action']
        command = params['command']

        res = self.controller_manager.patch(secret_data, action, command)
        result = {}
        result['data'] = res
        return result

    @transaction
    @check_required(['resource_id', 'secret_data'])
    def get_instance_count_status(self, params):
        """ verify options capability
        Args:
            params
              - resource_id: str
              - secret_data: dict

        Returns:
        """
        secret_data = params['secret_data']
        resource_id = params['resource_id']

        res = self.controller_manager.get_instance_count_status(resource_id, secret_data)
        return res