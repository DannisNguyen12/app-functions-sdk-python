import asyncio
import os
from typing import Any, Tuple
import json

from app_functions_sdk_py.contracts import errors
from app_functions_sdk_py.functions import filters, conversion
from app_functions_sdk_py.factory import new_app_service
from app_functions_sdk_py.interfaces import AppFunctionContext

service_key = "app-simple-filter-json"

if __name__ == "__main__":
    # turn off secure mode for examples. Not recommended for production
    os.environ["EDGEX_SECURITY_SECRET_STORE"] = "false"

    # 1) First thing to do is to create a new instance of an EdgeX Application Service.
    service, result = new_app_service(service_key)
    if result is False:
        os._exit(-1)

    # Leverage the built-in logging service in EdgeX
    lc = service.logger()

    try:
        # 2) shows how to access the application's specific configuration settings.
        device_names = service.get_application_setting_strings("DeviceNames")
        lc.info(f"Filtering for devices {device_names}")
        # 3) This is our pipeline configuration, the collection of functions to execute every time an event is triggered.
        service.set_default_functions_pipeline(
            filters.new_filter_for(filter_values=device_names).filter_by_device_name,
            conversion.Conversion().transform_to_xml
        )
        # 4) Lastly, we'll go ahead and tell the SDK to "start" and begin listening for events to trigger the pipeline.
        asyncio.run(service.run())
    except Exception as e:
        lc.error(f"{e}")
        os._exit(-1)

    # Do any required cleanup here
    os._exit(0)

def print_xml_to_console(ctx: AppFunctionContext, data: Any) -> Tuple[bool, Any]:
    # Leverage the built-in logging service in EdgeX
    if data is None:
        return False, errors.new_common_edgex(errors.ErrKind.CONTRACT_INVALID,"print_xml_to_console: No Data Received")

    if isinstance(data, str):
        print(data)
        return True, None
    return False, errors.new_common_edgex(errors.ErrKind.CONTRACT_INVALID,"print_xml_to_console: Data received is not the expected 'str' type")


service.set_default_functions_pipeline(
            filters.new_filter_for(filter_values=device_names).filter_by_device_name,
            conversion.Conversion().transform_to_xml,
            print_xml_to_console
        )