__all__ = ['InterruptManager']

import logging
from spaceone.core.manager import BaseManager

_LOGGER = logging.getLogger(__name__)


class InterruptManager(BaseManager):

    def __init__(self, transaction):
        super().__init__(transaction)

    def setup(self, secret_data):
        # TODO implementation
        _LOGGER.debug(f'[setup] secret_data: {secret_data}')
        res = {}
        return res

    def handle(self, spot_group_resource_id, resource_id, secret_data):
        # TODO implementation
        _LOGGER.debug(f'[handle] spot_group_resource_id: {spot_group_resource_id},'
                      f'resource_id: {resource_id},secret_data: {secret_data}')
        res = {}
        return res
