// Simulate the full extractPapers + detectCompany flow
const fs = require('fs');
const html = fs.readFileSync('index.html', 'utf-8');

// Extract COMPANIES array from HTML
const companiesMatch = html.match(/const COMPANIES = \[([\s\S]*?)\];/);
console.log('=== COMPANIES array found:', !!companiesMatch);

// Extract detectCompany function
const detectMatch = html.match(/function detectCompany\(text\) \{([\s\S]*?)\n\}/);
console.log('=== detectCompany found:', !!detectMatch);

// Manually test detectCompany with new company sources
const testSources = [
    '快手',
    '百度', 
    '小米',
    '阿里淘天',
    'Kuaishou',
    'Baidu',
    'Xiaomi',
    'Taobao',
];

// Parse COMPANIES from HTML
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
console.log('\n=== Companies parsed:', companies.length);
companies.forEach(c => console.log('  ', c.id, ':', c.keywords.join(', ')));

// Simulate detectCompany
function detectCompany(text) {
    for (const c of companies) {
        for (const kw of c.keywords) {
            if (text.includes(kw)) return c.id;
        }
    }
    return 'unknown';
}

console.log('\n=== Testing detectCompany with report sources ===');
testSources.forEach(src => {
    const result = detectCompany(src);
    console.log(`  "${src}" => ${result}`);
});

// Now test with actual report
const report = fs.readFileSync('reports/2026-04-08-report.md', 'utf-8');
const sections = report.split(/^### 论文\d+/gm);
const titleMatches = [...report.matchAll(/^### (论文\d+.+)$/gm)];

console.log('\n=== Papers from report ===');
for (let i = 0; i < titleMatches.length; i++) {
    const title = titleMatches[i][1].replace(/^论文\d+:\s*/, '');
    const body = sections[i + 1] || '';
    const sourceMatch = body.match(/\*\*来源\*\*:\s*(.+)/);
    const source = sourceMatch ? sourceMatch[1].trim() : '';
    const companyId = detectCompany(source + ' ' + title + ' ' + body.substring(0, 300));
    console.log(`  ${i+1}. "${title.substring(0,50)}" | source: "${source}" | detected: ${companyId}`);
}
