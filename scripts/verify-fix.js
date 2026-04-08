const fs = require('fs');
const html = fs.readFileSync('index.html', 'utf-8');

// Parse COMPANIES (new order)
const companiesMatch = html.match(/const COMPANIES = \[([\s\S]*?)\];/);
const companyLines = companiesMatch[1];
const companyRegex = /id:\s*'(\w+)'.*?keywords:\s*\[(.*?)\]/g;
let m;
const companies = [];
while ((m = companyRegex.exec(companyLines)) !== null) {
    const id = m[1];
    const kwStr = m[2];
    const keywords = kwStr.match(/'([^']+)'/g).map(s => s.replace(/'/g, ''));
    companies.push({ id, keywords });
}

function detectCompany(text) {
    for (const c of companies) {
        for (const kw of c.keywords) {
            if (text.includes(kw)) return c.id;
        }
    }
    return 'unknown';
}

// Test with report
const report = fs.readFileSync('reports/2026-04-08-report.md', 'utf-8');
const sections = report.split(/^### 论文\d+/gm);
const titleMatches = [...report.matchAll(/^### (论文\d+.+)$/gm)];

console.log('Papers found:', titleMatches.length);
for (let i = 0; i < titleMatches.length; i++) {
    const title = titleMatches[i][1].replace(/^论文\d+:\s*/, '');
    const body = sections[i + 1] || '';
    const sourceMatch = body.match(/\*\*来源\*\*:\s*(.+)/);
    const source = sourceMatch ? sourceMatch[1].trim() : '';
    // New logic: source first, then source+title
    const companyId = detectCompany(source) !== 'unknown' ? detectCompany(source) : detectCompany(source + ' ' + title);
    console.log(`  ${i+1}. source="${source}" => ${companyId} ${companyId === 'unknown' ? '❌' : '✅'}`);
}
