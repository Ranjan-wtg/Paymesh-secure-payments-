# bluetooth_scanner.py - Real Bluetooth Low Energy device scanning

import asyncio
import time
from datetime import datetime
from pathlib import Path
import json

try:
    from bleak import BleakScanner, BleakClient
    BLUETOOTH_AVAILABLE = True
    print("✅ Bluetooth BLE library available")
except ImportError:
    print("⚠️ Bluetooth BLE library not found. Install with: pip install bleak")
    BLUETOOTH_AVAILABLE = False

class BluetoothDeviceScanner:
    def __init__(self):
        self.payment_service_uuids = [
            "0000180F-0000-1000-8000-00805F9B34FB",  # Battery Service (common in payment devices)
            "0000FFF0-0000-1000-8000-00805F9B34FB",  # Custom payment service UUID
        ]
        self.scan_timeout = 10  # seconds
        self.log_dir = Path("bluetooth_logs")
        self.log_dir.mkdir(exist_ok=True)
    
    async def scan_for_payment_devices(self):
        """Scan for actual Bluetooth payment devices"""
        if not BLUETOOTH_AVAILABLE:
            return {
                "devices": [],
                "error": "Bluetooth library not available",
                "mock_devices": self._get_mock_devices()
            }
        
        print(f"🔵 Scanning for Bluetooth devices... ({self.scan_timeout}s)")
        
        try:
            # Scan for devices
            devices = await BleakScanner.discover(timeout=self.scan_timeout)
            
            payment_devices = []
            for device in devices:
                device_info = await self._analyze_device(device)
                if device_info["is_payment_device"]:
                    payment_devices.append(device_info)
            
            print(f"✅ Found {len(payment_devices)} potential payment devices out of {len(devices)} total")
            
            # Log scan results
            self._log_scan_results(payment_devices)
            
            return {
                "devices": payment_devices,
                "total_devices_found": len(devices),
                "scan_duration": self.scan_timeout,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"❌ Bluetooth scan failed: {e}")
            return {
                "devices": [],
                "error": f"Bluetooth scan failed: {str(e)}",
                "mock_devices": self._get_mock_devices()
            }
    
    async def _analyze_device(self, device):
        """Analyze if a device could be a payment terminal"""
        device_info = {
            "name": device.name or "Unknown Device",
            "address": device.address,
            "rssi": device.rssi,
            "is_payment_device": False,
            "confidence": 0.0,
            "device_type": "unknown"
        }
        
        # Check device name for payment indicators
        payment_keywords = ["pay", "pos", "terminal", "merchant", "card", "nfc", "wallet"]
        if device.name:
            name_lower = device.name.lower()
            keyword_matches = sum(1 for keyword in payment_keywords if keyword in name_lower)
            device_info["confidence"] += keyword_matches * 0.3
            
            if keyword_matches > 0:
                device_info["is_payment_device"] = True
                device_info["device_type"] = "payment_terminal"
        
        # Check signal strength (closer devices more likely to be payment terminals)
        if device.rssi and device.rssi > -60:  # Strong signal
            device_info["confidence"] += 0.2
        
        # Try to connect and check services (optional, can be slow)
        try:
            async with BleakClient(device.address, timeout=5.0) as client:
                services = await client.get_services()
                
                for service in services:
                    if str(service.uuid).upper() in [uuid.upper() for uuid in self.payment_service_uuids]:
                        device_info["is_payment_device"] = True
                        device_info["confidence"] += 0.4
                        device_info["device_type"] = "verified_payment_device"
                        break
        except:
            # Connection failed, probably not a payment device or device is busy
            pass
        
        return device_info
    
    def _get_mock_devices(self):
        """Fallback mock devices when real Bluetooth isn't available"""
        return [
            {
                "name": "PayMesh_Mock_POS", 
                "address": "12:34:56:78:90:AB",
                "rssi": -45,
                "is_payment_device": True,
                "confidence": 0.9,
                "device_type": "mock_payment_terminal"
            }
        ]
    
    def _log_scan_results(self, devices):
        """Log Bluetooth scan results"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "devices_found": len(devices),
            "devices": devices
        }
        
        log_file = self.log_dir / f"bluetooth_scan_{datetime.now().strftime('%Y-%m-%d')}.json"
        
        logs = []
        if log_file.exists():
            try:
                with open(log_file, 'r') as f:
                    logs = json.load(f)
            except:
                logs = []
        
        logs.append(log_entry)
        
        with open(log_file, 'w') as f:
            json.dump(logs, f, indent=2)
    
    def scan_for_devices(self):
        """Synchronous wrapper for async scanning"""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self.scan_for_payment_devices())

# Global Bluetooth scanner
bluetooth_scanner = BluetoothDeviceScanner()
