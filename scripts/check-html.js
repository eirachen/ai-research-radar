const fs = require('fs');
const html = fs.readFileSync('index.html', 'utf-8');

console.log('=== Key Element Checks ===');
console.log('Has talentTable div:', html.includes('id="talentTable"'));
console.log('Has renderTalent func:', html.includes('function renderTalent()'));
console.log('Has isStudent func:', html.includes('function isStudent('));
console.log('Has toggleTalentRow:', html.includes('function toggleTalentRow('));
console.log('Has toggleTalentSection:', html.includes('function toggleTalentSection('));
console.log('Has buildDetailHTML:', html.includes('function buildDetailHTML('));
console.log('Has page-intel:', html.includes('id="page-intel"'));
console.log('Has renderFilterBar:', html.includes('function renderFilterBar('));
console.log('Has renderPapers:', html.includes('function renderPapers('));
console.log('Has baidu company:', html.includes("id: 'baidu'"));
console.log('Has kuaishou company:', html.includes("id: 'kuaishou'"));

// Check the renderTalent function more closely
const rtStart = html.indexOf('function renderTalent()');
const rtEnd = html.indexOf('\nfunction ', rtStart + 10);
const rtBody = html.substring(rtStart, rtEnd > 0 ? rtEnd : rtStart + 500);
console.log('\n=== renderTalent first 300 chars ===');
console.log(rtBody.substring(0, 300));

// Check if talentTable is a <table> or <div>
const tableTag = html.match(/(<(?:table|div)[^>]*id="talentTable"[^>]*>)/);
console.log('\n=== talentTable tag ===');
console.log(tableTag ? tableTag[1] : 'NOT FOUND');

// Check filterBar rendering for new companies  
const detectCompanyFunc = html.indexOf('function detectCompany(');
if (detectCompanyFunc > 0) {
  console.log('\n=== detectCompany exists at position', detectCompanyFunc);
}

// Count how many papers filterBar/renderPapers shows
const rpFunc = html.indexOf('function renderPapers()');
console.log('renderPapers at position:', rpFunc);

// Check if ALL_PAPERS is populated from loadReports
const loadReports = html.indexOf('ALL_PAPERS.push');
console.log('ALL_PAPERS.push at position:', loadReports);
