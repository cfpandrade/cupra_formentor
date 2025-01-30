from weconnect_cupra.api.cupra.elements.charging_status import ChargingStatus
import logging

_LOGGER = logging.getLogger(__name__)

def safe_charging_status_update(self, fromDict):
    try:
        # Safely handle potential None values
        if fromDict is None or 'value' not in fromDict:
            _LOGGER.debug("Skipping charging status update due to invalid data")
            return

        value = fromDict.get('value', {})
        charge_power = value.get('chargePower_kW')
        
        if charge_power is not None:
            try:
                self.chargePower_kW = float(charge_power)
            except (TypeError, ValueError):
                _LOGGER.warning(f"Could not convert chargePower_kW to float: {charge_power}")
                self.chargePower_kW = None
        else:
            self.chargePower_kW = None

        # Call the original update method for other fields
        super(ChargingStatus, self).update(fromDict)
    except Exception as ex:
        _LOGGER.error(f"Error in charging status update: {ex}")

# Apply the monkey patch
ChargingStatus.update = safe_charging_status_update