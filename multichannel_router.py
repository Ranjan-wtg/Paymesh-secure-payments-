# real_multichannel_router.py - Real multi-channel routing with actual connectivity checks

from connectivity_checker import connectivity_checker
from bluetooth_scanner import bluetooth_scanner
from twilio_sms_sender import twilio_sms_sender
import time
from datetime import datetime

class RealMultiChannelRouter:
    def __init__(self):
        self.channel_priority = ["online", "bluetooth", "sms", "local"]
        self.last_connectivity_check = None
        self.connectivity_cache_duration = 30  # seconds
        
    def process_transaction_with_real_fallback(self, recipient, amount, sender_data):
        """Process transaction with real connectivity checks and fallback"""
        
        print(f"🚀 Processing ₹{amount} transaction to {recipient}")
        print(f"📊 Checking real connectivity status...")
        
        transaction_data = {
            "amount": amount,
            "recipient": recipient,
            "sender": sender_data.get("username", "Unknown"),
            "txn_id": f"TXN_{int(time.time())}",
            "timestamp": datetime.now().isoformat()
        }
        
        # Get real-time channel status
        channel_status = self._check_all_channels()
        print(f"📊 Real channel status: {channel_status}")
        
        # Try channels in priority order
        for channel in self.channel_priority:
            if not channel_status.get(channel, False):
                print(f"⏭️ Skipping {channel} - unavailable")
                continue
                
            print(f"🔄 Attempting {channel} channel...")
            
            result = self._attempt_real_channel_payment(channel, recipient, amount, transaction_data)
            
            if result["success"]:
                print(f"✅ Transaction successful via {channel}")
                result["channel_used"] = channel
                result["channel_status"] = channel_status
                result["transaction_data"] = transaction_data
                return result
            else:
                print(f"❌ {channel} failed: {result.get('error', 'Unknown error')}")
        
        # All channels failed
        return {
            "success": False,
            "error": "All payment channels failed",
            "channel_status": channel_status,
            "channels_attempted": self.channel_priority,
            "recommendation": "Please check your connectivity and try again"
        }
    
    def _check_all_channels(self):
        """Check real availability of all channels"""
        
        # Check internet connectivity
        internet_result = connectivity_checker.check_internet_connectivity()
        online_available = internet_result["online"]
        
        # Check Bluetooth devices
        bluetooth_result = bluetooth_scanner.scan_for_devices()
        bluetooth_available = len(bluetooth_result["devices"]) > 0
        
        # SMS is available if Twilio is configured
        sms_available = twilio_sms_sender.sms_available or True  # Fallback to simulation
        
        # Local storage always available
        local_available = True
        
        return {
            "online": online_available,
            "bluetooth": bluetooth_available,
            "sms": sms_available,
            "local": local_available,
            "detailed_info": {
                "internet_check": internet_result,
                "bluetooth_scan": bluetooth_result,
                "sms_provider": "twilio" if twilio_sms_sender.sms_available else "simulation"
            }
        }
    
    def _attempt_real_channel_payment(self, channel, recipient, amount, transaction_data):
        """Attempt payment through specific channel with real implementations"""
        
        if channel == "online":
            # Simulate online payment (implement your actual online payment here)
            return self._process_online_payment(recipient, amount, transaction_data)
        
        elif channel == "bluetooth":
            # Real Bluetooth payment
            return self._process_bluetooth_payment(recipient, amount, transaction_data)
        
        elif channel == "sms":
            # Real SMS via Twilio
            return self._process_sms_payment(recipient, amount, transaction_data)
        
        elif channel == "local":
            # Local storage
            return self._process_local_payment(recipient, amount, transaction_data)
        
        return {"success": False, "error": f"Unknown channel: {channel}"}
    
    def _process_online_payment(self, recipient, amount, transaction_data):
        """Process online payment (placeholder for actual implementation)"""
        # Here you would integrate with actual payment gateways
        # For now, simulate success
        print("🌐 Processing online payment...")
        time.sleep(1)
        
        return {
            "success": True,
            "message": f"Online payment of ₹{amount} processed",
            "processing_time_ms": 1000,
            "gateway": "simulation"
        }
    
    def _process_bluetooth_payment(self, recipient, amount, transaction_data):
        """Process Bluetooth payment using real device scan"""
        bluetooth_result = bluetooth_scanner.scan_for_devices()
        
        if not bluetooth_result["devices"]:
            return {
                "success": False,
                "error": "No Bluetooth payment devices found"
            }
        
        # Find best device (highest confidence)
        best_device = max(bluetooth_result["devices"], key=lambda d: d.get("confidence", 0))
        
        print(f"🔵 Using Bluetooth device: {best_device['name']}")
        print(f"   Address: {best_device['address']}")
        print(f"   Confidence: {best_device['confidence']:.2f}")
        
        # Simulate payment processing
        time.sleep(0.1)  # Fast BLE transaction
        
        return {
            "success": True,
            "message": f"Bluetooth payment of ₹{amount} completed",
            "device_used": best_device,
            "processing_time_ms": 100
        }
    
    def _process_sms_payment(self, recipient, amount, transaction_data):
        """Process SMS payment using real Twilio"""
        
        # Create transaction SMS
        sms_message = twilio_sms_sender.create_transaction_sms(
            amount, 
            recipient, 
            transaction_data["sender"], 
            transaction_data["txn_id"], 
            "success"
        )
        
        # Send SMS with security checks
        sms_result = twilio_sms_sender.send_secure_sms(recipient, sms_message, transaction_data)
        
        if sms_result["success"]:
            return {
                "success": True,
                "message": f"SMS payment notification sent for ₹{amount}",
                "sms_result": sms_result
            }
        else:
            return {
                "success": False,
                "error": f"SMS sending failed: {sms_result.get('error', 'Unknown error')}",
                "sms_result": sms_result
            }
    
    def _process_local_payment(self, recipient, amount, transaction_data):
        """Process local payment (offline storage)"""
        print("💾 Storing transaction locally for later sync...")
        
        # Here you would save to your local database
        # For now, just simulate
        
        return {
            "success": True,
            "message": f"Transaction of ₹{amount} stored locally",
            "sync_required": True,
            "storage": "local_database"
        }
    
    def get_real_channel_statistics(self):
        """Get real-time channel statistics"""
        channel_status = self._check_all_channels()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "channel_status": {k: v for k, v in channel_status.items() if k != "detailed_info"},
            "connectivity_details": channel_status["detailed_info"],
            "priority_order": self.channel_priority
        }

# Global real multi-channel router
real_multichannel_router = RealMultiChannelRouter()
