from spaceone.core.service import *
from spaceone.spot_automation.manager.cost_saving_manager import CostSavingManager


@authentication_handler
class CostSavingService(BaseService):
    def __init__(self, metadata):
        super().__init__(metadata)
        self.cost_saving_manager: CostSavingManager = self.locator.get_manager('CostSavingManager')

    @transaction
    @check_required(['resource_id', 'secret_data'])
    def get(self, params):
        resource_id = params['resource_id']
        secret_data = params['secret_data']

        res = self.cost_saving_manager.get(resource_id, secret_data)
        return res
