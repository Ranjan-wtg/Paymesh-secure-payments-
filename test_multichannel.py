# test_real_multichannel.py - Test real multi-channel system

from multichannel_router import real_multichannel_router

def test_real_multichannel_system():
    """Test the complete real multi-channel system"""
    
    print("🚀 Testing PayMesh REAL Multi-Channel Payment System")
    print("=" * 60)
    
    # Test data
    sender_data = {"username": "testuser", "phone": "+919876543210"}
    recipient = "+919876543211"  # Replace with your actual phone number for SMS testing
    amount = 100
    
    # Get real-time statistics
    stats = real_multichannel_router.get_real_channel_statistics()
    print("📊 REAL-TIME CHANNEL STATUS:")
    for channel, status in stats["channel_status"].items():
        print(f"   {channel.title()}: {'🟢 Available' if status else '🔴 Unavailable'}")
    
    print(f"\n🔍 CONNECTIVITY DETAILS:")
    details = stats["connectivity_details"]
    
    # Internet details
    internet = details["internet_check"]
    print(f"   Internet: DNS {'✅' if internet['dns_resolution'] else '❌'} | HTTP {'✅' if internet['http_requests'] else '❌'} | Ping {'✅' if internet['ping_test'] else '❌'}")
    
    # Bluetooth details
    bluetooth = details["bluetooth_scan"]
    print(f"   Bluetooth: {len(bluetooth['devices'])} payment devices found")
    for device in bluetooth['devices']:
        print(f"      • {device['name']} (Confidence: {device['confidence']:.2f})")
    
    # SMS details
    print(f"   SMS: Provider {details['sms_provider']}")
    
    print("\n" + "=" * 60)
    print("🔄 PROCESSING TRANSACTION...")
    
    # Process transaction
    result = real_multichannel_router.process_transaction_with_real_fallback(
        recipient, amount, sender_data
    )
    
    print("\n" + "=" * 60)
    print("📊 TRANSACTION RESULT:")
    print(f"Success: {'✅' if result['success'] else '❌'} {result['success']}")
    
    if result["success"]:
        print(f"Channel used: {result.get('channel_used', 'Unknown')}")
        print(f"Transaction ID: {result.get('transaction_data', {}).get('txn_id', 'N/A')}")
        print(f"Message: {result.get('message', 'No message')}")
    else:
        print(f"Error: {result.get('error', 'Unknown error')}")
        print(f"Channels attempted: {result.get('channels_attempted', [])}")

if __name__ == "__main__":
    test_real_multichannel_system()
