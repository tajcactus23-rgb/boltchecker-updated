const express = require('express');
const path = require('path');
const fs = require('fs');

const app = express();
const PORT = 3000;

app.use(express.json());

// Root route
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'index.html'));
});

// HWID generation
app.get('/api/hwid', (req, res) => {
    const chars = 'ABCDEF0123456789';
    let hwid = '';
    for(let i = 0; i < 32; i++) {
        hwid += chars[Math.floor(Math.random() * chars.length)];
    }
    res.json({ hwid });
});

// Validate beta code
app.post('/api/login', (req, res) => {
    const { beta } = req.body;
    if(!beta || beta.length < 5) {
        return res.json({ success: false, message: "OI! You need a proper beta code mate!" });
    }
    res.json({ success: true, message: "G'day mate! You're cookin' now!" });
});

// Load combos
app.post('/api/load', (req, res) => {
    const { filename } = req.body;
    try {
        const filePath = filename || path.join(__dirname, '../combos.txt');
        const content = fs.readFileSync(filePath, 'utf8');
        const lines = content.split('\n').filter(l => l.trim());
        res.json({ success: true, count: lines.length });
    } catch(e) {
        res.json({ success: false, message: "No file found" });
    }
});

// Start check
app.post('/api/check', (req, res) => {
    const { mode, threads } = req.body;
    res.json({ 
        success: true, 
        message: `Starting ${mode} with ${threads} threads...`,
        status: "running"
    });
});

app.listen(PORT, '0.0.0.0', () => {
    console.log(`🚀 BOLTFM running at http://0.0.0.0:${PORT}`);
});