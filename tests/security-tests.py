#!/usr/bin/env python3
"""
Security tests for Azure infrastructure
"""

import os
import sys
import json
import subprocess
import requests
from typing import Dict, List, Tuple
import socket
import ssl

class SecurityTester:
    def __init__(self, public_ip: str):
        self.public_ip = public_ip
        self.results = []
        
    def test_port_accessibility(self) -> bool:
        """Test that only required ports are accessible"""
        print("🔍 Testing port accessibility...")
        
        # Ports that should be accessible
        required_ports = [80, 443]
        
        # Ports that should NOT be accessible
        forbidden_ports = [22, 3389, 5432, 3306, 1433, 6379, 27017]
        
        success = True
        
        # Test required ports
        for port in required_ports:
            if not self._is_port_open(port):
                print(f"❌ Required port {port} is not accessible")
                success = False
            else:
                print(f"✅ Required port {port} is accessible")
        
        # Test forbidden ports
        for port in forbidden_ports:
            if self._is_port_open(port):
                print(f"❌ SECURITY RISK: Port {port} should not be accessible from internet")
                success = False
            else:
                print(f"✅ Port {port} is properly blocked")
        
        return success
    
    def test_ssl_configuration(self) -> bool:
        """Test SSL/TLS configuration"""
        print("🔍 Testing SSL/TLS configuration...")
        
        try:
            # Test SSL certificate
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            with socket.create_connection((self.public_ip, 443), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=self.public_ip) as ssock:
                    cert = ssock.getpeercert()
                    cipher = ssock.cipher()
                    
                    print(f"✅ SSL connection established")
                    print(f"✅ Cipher: {cipher[0]}")
                    print(f"✅ Protocol: {cipher[1]}")
                    
                    # Check for secure protocols
                    if cipher[1] in ['TLSv1.2', 'TLSv1.3']:
                        print(f"✅ Secure TLS version: {cipher[1]}")
                        return True
                    else:
                        print(f"❌ Insecure TLS version: {cipher[1]}")
                        return False
                        
        except Exception as e:
            print(f"❌ SSL test failed: {str(e)}")
            return False
    
    def test_http_to_https_redirect(self) -> bool:
        """Test HTTP to HTTPS redirect"""
        print("🔍 Testing HTTP to HTTPS redirect...")
        
        try:
            response = requests.get(f"http://{self.public_ip}", 
                                  allow_redirects=False, timeout=10)
            
            if response.status_code in [301, 302, 308]:
                location = response.headers.get('Location', '')
                if location.startswith('https://'):
                    print("✅ HTTP to HTTPS redirect is working")
                    return True
                else:
                    print(f"❌ Redirect location is not HTTPS: {location}")
                    return False
            else:
                print(f"❌ No redirect found, status code: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ HTTP redirect test failed: {str(e)}")
            return False
    
    def test_security_headers(self) -> bool:
        """Test security headers"""
        print("🔍 Testing security headers...")
        
        try:
            response = requests.get(f"https://{self.public_ip}", 
                                  verify=False, timeout=10)
            
            headers = response.headers
            security_headers = {
                'X-Content-Type-Options': 'nosniff',
                'X-Frame-Options': ['DENY', 'SAMEORIGIN'],
                'X-XSS-Protection': '1; mode=block'
            }
            
            success = True
            for header, expected in security_headers.items():
                if header in headers:
                    if isinstance(expected, list):
                        if headers[header] in expected:
                            print(f"✅ {header}: {headers[header]}")
                        else:
                            print(f"⚠️ {header}: {headers[header]} (consider {expected})")
                    else:
                        if headers[header] == expected:
                            print(f"✅ {header}: {headers[header]}")
                        else:
                            print(f"⚠️ {header}: {headers[header]} (expected {expected})")
                else:
                    print(f"⚠️ Missing security header: {header}")
                    success = False
            
            return success
            
        except Exception as e:
            print(f"❌ Security headers test failed: {str(e)}")
            return False
    
    def test_application_availability(self) -> bool:
        """Test application availability and content"""
        print("🔍 Testing application availability...")
        
        try:
            response = requests.get(f"https://{self.public_ip}", 
                                  verify=False, timeout=10)
            
            if response.status_code == 200:
                if "Hello World" in response.text:
                    print("✅ Application is available and serving correct content")
                    return True
                else:
                    print("❌ Application is available but serving unexpected content")
                    return False
            else:
                print(f"❌ Application returned status code: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Application availability test failed: {str(e)}")
            return False
    
    def test_health_endpoint(self) -> bool:
        """Test health check endpoint"""
        print("🔍 Testing health endpoint...")
        
        try:
            response = requests.get(f"https://{self.public_ip}/health", 
                                  verify=False, timeout=10)
            
            if response.status_code == 200 and "healthy" in response.text.lower():
                print("✅ Health endpoint is working")
                return True
            else:
                print(f"❌ Health endpoint failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Health endpoint test failed: {str(e)}")
            return False
    
    def _is_port_open(self, port: int, timeout: int = 5) -> bool:
        """Check if a port is open"""
        try:
            with socket.create_connection((self.public_ip, port), timeout=timeout):
                return True
        except (socket.timeout, socket.error):
            return False
    
    def run_all_tests(self) -> bool:
        """Run all security tests"""
        print(f"🚀 Starting security tests for {self.public_ip}")
        print("=" * 50)
        
        tests = [
            ("Port Accessibility", self.test_port_accessibility),
            ("SSL Configuration", self.test_ssl_configuration),
            ("HTTP to HTTPS Redirect", self.test_http_to_https_redirect),
            ("Security Headers", self.test_security_headers),
            ("Application Availability", self.test_application_availability),
            ("Health Endpoint", self.test_health_endpoint)
        ]
        
        results = []
        for test_name, test_func in tests:
            print(f"\n📋 Running: {test_name}")
            try:
                result = test_func()
                results.append((test_name, result))
                print(f"{'✅ PASSED' if result else '❌ FAILED'}: {test_name}")
            except Exception as e:
                print(f"❌ ERROR in {test_name}: {str(e)}")
                results.append((test_name, False))
        
        print("\n" + "=" * 50)
        print("📊 SECURITY TEST SUMMARY")
        print("=" * 50)
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} - {test_name}")
        
        print(f"\nOverall: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All security tests passed!")
            return True
        else:
            print("⚠️ Some security tests failed. Please review and fix the issues.")
            return False

def main():
    if len(sys.argv) != 2:
        print("Usage: python security-tests.py <public_ip>")
        sys.exit(1)
    
    public_ip = sys.argv[1]
    tester = SecurityTester(public_ip)
    
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()