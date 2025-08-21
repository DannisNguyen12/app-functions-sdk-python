#!/usr/bin/env python3
"""
EdgeX Event Forwarder - Forward Core Data events to App Service HTTP trigger
This script polls Core Data for new events and forwards them to our app service
"""

import os
import requests
import json
import time
from datetime import datetime


def load_simple_config(path: str):
    """Very small YAML-lite parser to extract Service and Database settings.

    Returns dict with possible keys: service_host, service_port, db_host, db_port,
    core_data_url (if present in file under a recognizable key).
    This avoids adding an external YAML dependency while still allowing
    `app.py` to derive the ports/hosts from `res/configuration.yaml`.
    """
    cfg = {}
    if not os.path.exists(path):
        return cfg

    current = None
    try:
        with open(path, 'r', encoding='utf-8') as f:
            for raw in f:
                line = raw.rstrip('\n')
                stripped = line.lstrip()
                if not stripped or stripped.startswith('#'):
                    continue

                # section headers (no deeper nesting required)
                if stripped.startswith('Service:'):
                    current = 'Service'
                    continue
                if stripped.startswith('Database:'):
                    current = 'Database'
                    continue
                if stripped.startswith('CoreData:') or stripped.startswith('Core_Data:'):
                    current = 'CoreData'
                    continue

                # key: value lines
                if ':' in stripped:
                    key, val = [p.strip() for p in stripped.split(':', 1)]
                    # remove surrounding quotes if present
                    if val.startswith('"') and val.endswith('"'):
                        val = val[1:-1]
                    if val.startswith("'") and val.endswith("'"):
                        val = val[1:-1]

                    if current == 'Service':
                        if key == 'Host':
                            cfg['service_host'] = val
                        elif key == 'Port':
                            try:
                                cfg['service_port'] = int(val)
                            except Exception:
                                cfg['service_port'] = val
                    elif current == 'Database':
                        if key == 'Host':
                            cfg['db_host'] = val
                        elif key == 'Port':
                            try:
                                cfg['db_port'] = int(val)
                            except Exception:
                                cfg['db_port'] = val
                    elif current == 'CoreData':
                        # accept a key like Url or Urls
                        if key.lower() in ('url', 'urlroot', 'root', 'base'):
                            cfg['core_data_url'] = val
                        else:
                            # fallback: if value looks like http:// treat it as url
                            if val.startswith('http'):
                                cfg['core_data_url'] = val
    except Exception:
        # silently ignore parse errors and fall back to defaults
        return cfg

    return cfg

# Configuration defaults
_DEFAULT_CORE = "http://localhost:59880/api/v3"
_DEFAULT_APP_HOST = "localhost"
_DEFAULT_APP_PORT = 59788

# Attempt to load service/database settings from res/configuration.yaml
config_path = os.path.join(os.path.dirname(__file__), "res", "configuration.yaml")
_cfg = load_simple_config(config_path)

CORE_DATA_URL = _cfg.get('core_data_url', _DEFAULT_CORE)
APP_SERVICE_HOST = _cfg.get('service_host', _DEFAULT_APP_HOST)
APP_SERVICE_PORT = _cfg.get('service_port', _DEFAULT_APP_PORT)
APP_SERVICE_URL = f"http://{APP_SERVICE_HOST}:{APP_SERVICE_PORT}/api/v3/trigger"

# Track last processed event ID to avoid duplicates
last_event_id = None
poll_interval = 2  # seconds

def get_latest_events(limit=10):
    """Get latest events from EdgeX Core Data"""
    try:
        response = requests.get(f"{CORE_DATA_URL}/event/all?offset=0&limit={limit}")
        if response.status_code == 200:
            data = response.json()
            return data.get('events', [])
        else:
            print(f"❌ Error getting events: {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ Exception getting events: {e}")
        return []

def forward_event_to_app_service(event):
    """Print an event to the console (no exporting to another app)."""
    try:
        device_name = event.get('deviceName', 'Unknown')
        readings_count = len(event.get('readings', []))
        print(f"📥 Received event from {device_name} ({readings_count} readings)")
        try:
            print(json.dumps(event, indent=2, default=str))
        except Exception:
            print(repr(event))
        return True
    except Exception as e:
        print(f"❌ Error printing event: {e}")
        try:
            print(repr(event))
        except Exception:
            pass
        return False

def main():
    global last_event_id
    
    print("🚀 EdgeX Event Forwarder Starting...")
    print(f"📡 Polling Core Data: {CORE_DATA_URL}")
    print(f"🎯 Forwarding to App Service: {APP_SERVICE_URL}")
    print(f"⏱️  Poll interval: {poll_interval} seconds")
    print("=" * 60)
    
    # Check if app service is running
    try:
        response = requests.get(APP_SERVICE_URL.replace('/trigger', '/ping'), timeout=3)
        if response.status_code != 200:
            print("⚠️  App Service may not be running. Start it with: python app.py")
    except:
        print("⚠️  App Service not responding. Start it with: python app.py")
    
    while True:
        try:
            # Get latest events
            events = get_latest_events(5)
            
            if events:
                # Process events in chronological order (reverse, as API returns newest first)
                for event in reversed(events):
                    event_id = event.get('id')
                    
                    # Skip if we've already processed this event
                    if last_event_id and event_id == last_event_id:
                        break
                    
                    # Forward the event
                    success = forward_event_to_app_service(event)
                    
                    if success:
                        last_event_id = event_id
                
                # Update our tracking
                if events:
                    last_event_id = events[0].get('id')  # Most recent event ID
            
            time.sleep(poll_interval)
            
        except KeyboardInterrupt:
            print("\n🛑 Forwarder stopping...")
            break
        except Exception as e:
            print(f"❌ Main loop error: {e}")
            time.sleep(poll_interval)

if __name__ == "__main__":
    main()
