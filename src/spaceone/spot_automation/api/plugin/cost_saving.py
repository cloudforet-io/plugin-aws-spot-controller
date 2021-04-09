import logging

from spaceone.api.spot_automation.plugin import cost_saving_pb2, cost_saving_pb2_grpc
from spaceone.core.pygrpc import BaseAPI

_LOGGER = logging.getLogger(__name__)


class CostSaving(BaseAPI, cost_saving_pb2_grpc.CostSavingServicer):

    pb2 = cost_saving_pb2
    pb2_grpc = cost_saving_pb2_grpc

    def get(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service('CostSavingService', metadata) as cost_saving_svc:
            result = cost_saving_svc.get(params)
            _LOGGER.debug(f'[get] result: {result}')
            return self.locator.get_info('CostSavingInfo', result)
