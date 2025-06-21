# connectivity_checker.py - Real internet and network connectivity checking

import socket
import requests
import subprocess
import platform
from datetime import datetime

class ConnectivityChecker:
    def __init__(self):
        self.test_hosts = [
            "8.8.8.8",        # Google DNS
            "1.1.1.1",        # Cloudflare DNS
            "208.67.222.222"  # OpenDNS
        ]
        self.test_urls = [
            "https://httpbin.org/status/200",
            "https://www.google.com",
            "https://amazon.com"
        ]
    
    def check_internet_connectivity(self, timeout=5):
        """Check if internet is actually available"""
        print("🌐 Checking internet connectivity...")
        
        # Method 1: DNS resolution test
        dns_working = self._check_dns_resolution(timeout)
        
        # Method 2: HTTP request test
        http_working = self._check_http_connectivity(timeout)
        
        # Method 3: Ping test
        ping_working = self._check_ping_connectivity(timeout)
        
        connectivity_score = sum([dns_working, http_working, ping_working])
        is_online = connectivity_score >= 2  # At least 2 out of 3 methods work
        
        result = {
            "online": is_online,
            "dns_resolution": dns_working,
            "http_requests": http_working,
            "ping_test": ping_working,
            "connectivity_score": f"{connectivity_score}/3",
            "timestamp": datetime.now().isoformat()
        }
        
        print(f"📊 Internet status: {'🟢 Online' if is_online else '🔴 Offline'}")
        print(f"   DNS: {'✅' if dns_working else '❌'} | HTTP: {'✅' if http_working else '❌'} | Ping: {'✅' if ping_working else '❌'}")
        
        return result
    
    def _check_dns_resolution(self, timeout):
        """Test DNS resolution"""
        try:
            socket.setdefaulttimeout(timeout)
            for host in self.test_hosts:
                socket.gethostbyname(host)
            return True
        except (socket.gaierror, socket.timeout):
            return False
    
    def _check_http_connectivity(self, timeout):
        """Test HTTP connectivity"""
        try:
            for url in self.test_urls[:2]:  # Test first 2 URLs
                response = requests.get(url, timeout=timeout)
                if response.status_code == 200:
                    return True
            return False
        except (requests.RequestException, requests.Timeout):
            return False
    
    def _check_ping_connectivity(self, timeout):
        """Test ping connectivity"""
        try:
            system = platform.system().lower()
            if system == "windows":
                cmd = ["ping", "-n", "1", "-w", str(timeout * 1000), self.test_hosts[0]]
            else:
                cmd = ["ping", "-c", "1", "-W", str(timeout), self.test_hosts[0]]
            
            result = subprocess.run(cmd, capture_output=True, timeout=timeout + 1)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            return False

# Global connectivity checker
connectivity_checker = ConnectivityChecker()
