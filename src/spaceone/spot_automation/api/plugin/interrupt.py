import logging

from spaceone.api.spot_automation.plugin import interrupt_pb2, interrupt_pb2_grpc
from spaceone.core.pygrpc import BaseAPI

_LOGGER = logging.getLogger(__name__)


class Interrupt(BaseAPI, interrupt_pb2_grpc.InterruptServicer):
    pb2 = interrupt_pb2
    pb2_grpc = interrupt_pb2_grpc

    def setup(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service('InterruptService', metadata) as interrupt_svc:
            result = interrupt_svc.setup(params)
            _LOGGER.debug(f'[setup] result: {result}')
            return self.locator.get_info('EmptyInfo')

    def handle(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service('InterruptService', metadata) as interrupt_svc:
            result = interrupt_svc.handle(params)
            _LOGGER.debug(f'[setup] handle: {result}')
            return self.locator.get_info('EmptyInfo')
