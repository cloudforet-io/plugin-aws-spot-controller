from spaceone.core.service import *
from spaceone.spot_automation.manager.interrupt_manager import InterruptManager


@authentication_handler
class InterruptService(BaseService):
    def __init__(self, metadata):
        super().__init__(metadata)
        self.interrupt_manager: InterruptManager = self.locator.get_manager('InterruptManager')

    @transaction
    @check_required(['endpoint', 'secret_data'])
    def setup(self, params):
        endpoint = params['endpoint']
        secret_data = params['secret_data']

        res = self.interrupt_manager.setup(endpoint, secret_data)
        return res

    @transaction
    @check_required(['spot_group_resource_id', 'resource_id', 'secret_data'])
    def handle(self, params):
        spot_group_resource_id = params['spot_group_resource_id']
        resource_id = params['resource_id']
        secret_data = params['secret_data']

        res = self.interrupt_manager.handle(spot_group_resource_id, resource_id, secret_data)
        return res
