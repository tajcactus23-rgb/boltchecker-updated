#!/usr/bin/env python3
"""Standalone Proxy Scraper - Simplified"""
import requests
import sys

PROXY_URLS = [
    ('https://api.proxyscrape.com/?request=getproxies&proxytype=http&timeout=10000', 'http'),
    ('https://api.proxyscrape.com/?request=getproxies&proxytype=socks5&timeout=10000', 'socks5'),
    ('https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt', 'http'),
]

def scrape(output='proxies.txt'):
    print("[*] Proxy Scraper")
    print("-" * 40)
    
    proxies = []
    
    for url, ptype in PROXY_URLS:
        print(f"Fetching: {url[:50]}...")
        try:
            r = requests.get(url, timeout=20)
            lines = r.text.split('\n')
            
            count = 0
            for line in lines:
                line = line.strip()
                if ':' in line and line.count(':') == 1:
                    try:
                        ip, port = line.split(':')
                        if port.isdigit() and 0 < int(port) < 65536:
                            proxies.append(line)
                            count += 1
                    except: pass
            print(f"  +{count} {ptype} proxies")
        except Exception as e:
            print(f"  Error: {e}")
    
    # Remove duplicates
    proxies = list(set(proxies))
    print("-" * 40)
    print(f"Total: {len(proxies)} unique proxies")
    
    if proxies:
        with open(output, 'w') as f:
            f.write('\n'.join(proxies))
        print(f"Saved: {output}")
    
    return len(proxies)

if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else 'proxies.txt'
    scrape(out)
    print("Done!")