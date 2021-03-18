import logging

from spaceone.api.spot_automation.plugin import controller_pb2, controller_pb2_grpc
from spaceone.core.pygrpc import BaseAPI
from spaceone.core.pygrpc.message_type import *

_LOGGER = logging.getLogger(__name__)

class Controller(BaseAPI, controller_pb2_grpc.ControllerServicer):

    pb2 = controller_pb2
    pb2_grpc = controller_pb2_grpc

    def init(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service('ControllerService', metadata) as controller_svc:
            data = controller_svc.init(params)
            return self.locator.get_info('PluginInfo', data)

    def verify(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service('ControllerService', metadata) as controller_svc:
            controller_svc.verify(params)
            return self.locator.get_info('EmptyInfo')

    def patch(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service('ControllerService', metadata) as controller_svc:
            result = controller_svc.patch(params)
            _LOGGER.debug(f'[patch] result: {result}')
            return self.locator.get_info('ResponseInfo', result)