// Quick test: load reports and check what extractPapers returns
const fs = require('fs');
const md = fs.readFileSync('reports/2026-04-08-report.md', 'utf-8');

const sections = md.split(/^### 论文\d+/gm);
const titleMatches = [...md.matchAll(/^### (论文\d+.+)$/gm)];
console.log('Found', titleMatches.length, 'papers');

for (let i = 0; i < titleMatches.length; i++) {
    const title = titleMatches[i][1].replace(/^论文\d+:\s*/, '');
    const body = sections[i + 1] || '';
    const sourceMatch = body.match(/\*\*来源\*\*:\s*(.+)/);
    const source = sourceMatch ? sourceMatch[1].trim() : 'NO SOURCE';
    console.log(`  ${i+1}. "${title}" | source: "${source}"`);
}
