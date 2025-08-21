#!/usr/bin/env python3
"""
EdgeX App Service - Ready to Use (HTTP Version for Testing)
This version uses HTTP trigger for easier testing while demonstrating prebuilt functions.
"""

import asyncio
import os
import json
from typing import Any, Tuple

from app_functions_sdk_py.contracts import errors
from app_functions_sdk_py.functions import filters, conversion
from app_functions_sdk_py.factory import new_app_service
from app_functions_sdk_py.interfaces import AppFunctionContext

service_key = "app-service-ready-http"

def print_json_to_console(ctx: AppFunctionContext, data: Any) -> Tuple[bool, Any]:
    """
    Print the JSON data to the console with pretty formatting
    """
    if data is None:
        return False, errors.new_common_edgex(
            errors.ErrKind.CONTRACT_INVALID,
            "print_json_to_console: No Data Received"
        )

    try:
        if isinstance(data, (bytes, bytearray)):
            # Data from JSON conversion (bytes)
            json_str = data.decode('utf-8')
            json_obj = json.loads(json_str)
            print("=" * 60)
            print("📦 PROCESSED EVENT DATA (JSON):")
            print(json.dumps(json_obj, indent=2))
            print("=" * 60)
        else:
            # Event object or other data
            print("=" * 60)
            print("📦 EVENT DATA:")
            print(json.dumps(data.__dict__ if hasattr(data, '__dict__') else data, 
                           indent=2, default=str))
            print("=" * 60)
        
        return True, None
    except Exception as e:
        ctx.logger().error(f"Error printing JSON: {e}")
        print(f"❌ Error processing data: {e}")
        return True, None  # Continue pipeline even on print errors

def log_device_info(ctx: AppFunctionContext, data: Any) -> Tuple[bool, Any]:
    """
    Log information about the incoming device data
    """
    if hasattr(data, 'deviceName') and hasattr(data, 'readings'):
        device_name = data.deviceName
        reading_count = len(data.readings) if data.readings else 0
        reading_names = [r.resourceName for r in data.readings] if data.readings else []
        
        print(f"🔄 Processing device: {device_name}")
        print(f"📊 Readings: {reading_count}")
        print(f"📋 Resources: {reading_names}")
        
        ctx.logger().info(
            f"Processing device: {device_name}, "
            f"readings: {reading_count}, "
            f"resources: {reading_names}"
        )
    
    return True, data

if __name__ == "__main__":
    # Turn off secure mode for examples
    os.environ["EDGEX_SECURITY_SECRET_STORE"] = "false"

    # Create new EdgeX Application Service
    service, result = new_app_service(service_key)
    if not result:
        print("❌ Failed to create application service")
        os._exit(-1)

    # Get logger
    lc = service.logger()
    
    try:
        # Define target devices (virtual devices in EdgeX)
        target_devices = [
            "Random-Boolean-Device",
            "Random-Float-Device", 
            "Random-Integer-Device"
        ]
        
        lc.info(f"🚀 Starting {service_key}")
        print(f"🎯 Filtering for devices: {target_devices}")
        
        # Create the functions pipeline using prebuilt functions
        service.set_default_functions_pipeline(
            # 1. Log incoming device info (custom function)
            log_device_info,
            
            # 2. Filter for specific virtual devices (prebuilt filter)
            filters.new_filter_for(filter_values=target_devices).filter_by_device_name,
            
            # 3. Convert to JSON (prebuilt conversion)
            conversion.Conversion().transform_to_json,
            
            # 4. Print JSON to console (custom function)
            print_json_to_console
        )
        
        print("✅ Pipeline configured with prebuilt functions:")
        print("   📍 Device Name Filter (prebuilt)")
        print("   🔄 JSON Conversion (prebuilt)")
        print("   📝 Console Output (custom)")
        print("")
        print("🌐 HTTP Trigger ready at: http://localhost:59782/api/v3/trigger")
        print("📝 Send POST requests with EdgeX Event JSON to test")
        
        # Start the service
        asyncio.run(service.run())
        
    except Exception as e:
        lc.error(f"❌ Service error: {e}")
        print(f"❌ Service error: {e}")
        os._exit(-1)

    # Cleanup
    print("🛑 Service shutting down")
    os._exit(0)
