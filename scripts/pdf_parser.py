"""
PDF-based author-affiliation parser for arXiv papers.
Downloads PDF, extracts first page, parses author affiliations.
Returns structured data: which authors belong to which organizations.
"""
import urllib.request
import pdfplumber
import tempfile
import os
import re
import time


# Company identifiers (for matching in affiliations)
COMPANY_IDENTIFIERS = {
    'huawei': ['Huawei', 'Noah', "Noah's Ark"],
    'bytedance': ['ByteDance', 'Seed Team', 'Doubao'],
    'alibaba': ['Alibaba', 'Tongyi', 'DAMO Academy', 'Aliyun'],
    'deepseek': ['DeepSeek'],
    'moonshot': ['Moonshot', 'Dark Side of the Moon'],
    'openai': ['OpenAI'],
    'deepmind': ['DeepMind', 'Google DeepMind'],
    'anthropic': ['Anthropic'],
    'meta': ['Meta AI', 'Meta FAIR', 'Meta Platforms', 'FAIR'],
    'nvidia': ['NVIDIA'],
    'baidu': ['Baidu'],
    'kuaishou': ['Kuaishou', 'Kwai'],
    'didi': ['DiDi', 'Didi Chuxing'],
    'xiaomi': ['Xiaomi'],
    'stepfun': ['StepFun', 'Step AI'],
    'taotian': ['Taobao', 'Alibaba Taotian'],
    'antgroup': ['Ant Group', 'Ant Financial', 'Alipay'],
}

# University identifiers
UNI_IDENTIFIERS = [
    'University', 'Institute', 'College', 'School of', 'Department of',
    'Faculty of', 'Academy', 'Polytechnic', 'Lab ', 'Laboratory',
    'MIT', 'CMU', 'ETH', 'EPFL', 'KAIST', 'NUS', 'NTU',
    'HKUST', 'HKU', 'CUHK', 'CityU', 'PolyU', 'HKBU',
    'UCL', 'UCLA', 'USC', 'NYU', 'Caltech', 'Mila', 'INRIA',
    'Max Planck', 'CAS', 'USTC',
]

HK_IDENTIFIERS = ['Hong Kong', 'HKUST', 'HKU', 'CUHK', 'CityU', 'PolyU', 'HKBU']


def download_pdf_page1(pdf_url, timeout=20):
    """Download PDF and extract first page text"""
    try:
        req = urllib.request.Request(pdf_url, headers={"User-Agent": "AI-Research-Radar/2.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            pdf_data = resp.read()
        
        tmp = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
        tmp.write(pdf_data)
        tmp.close()
        
        with pdfplumber.open(tmp.name) as pdf:
            if pdf.pages:
                text = pdf.pages[0].extract_text() or ''
            else:
                text = ''
        
        os.unlink(tmp.name)
        return text
    except Exception as e:
        return ''


def parse_affiliations(page1_text, known_authors=None):
    """
    Parse first page text to extract author-affiliation mapping.
    Returns:
      {
        'authors': [{'name': 'XX', 'affiliation': 'YY University', 'is_company': False, 'is_uni': True, 'company_id': None}],
        'companies_found': ['alibaba'],
        'unis_found': ['Tongji University'],
        'is_confirmed_collab': True/False,  # Both company + uni authors present
        'hk_unis_found': [],
      }
    """
    if not page1_text:
        return None
    
    lines = page1_text.split('\n')
    
    # Find the region between title and abstract
    # Usually: Title -> Authors -> Affiliations -> Abstract
    abstract_idx = -1
    for i, line in enumerate(lines):
        if re.match(r'^\s*(Abstract|ABSTRACT|1\s+Introduction|1\.\s+Introduction)', line.strip()):
            abstract_idx = i
            break
    
    if abstract_idx < 0:
        abstract_idx = min(15, len(lines))
    
    # Get header region (before abstract)
    header = '\n'.join(lines[:abstract_idx])
    
    # Find all affiliations in header
    companies_found = set()
    unis_found = set()
    hk_unis = set()
    
    header_lower = header.lower()
    
    for company_id, identifiers in COMPANY_IDENTIFIERS.items():
        for ident in identifiers:
            if ident.lower() in header_lower:
                companies_found.add(company_id)
    
    for ident in UNI_IDENTIFIERS:
        if ident.lower() in header_lower:
            # Try to extract full university name from context
            for line in lines[:abstract_idx]:
                if ident.lower() in line.lower():
                    unis_found.add(line.strip()[:80])
                    break
    
    for ident in HK_IDENTIFIERS:
        if ident.lower() in header_lower:
            hk_unis.add(ident)
    
    is_confirmed = bool(companies_found) and bool(unis_found)
    
    return {
        'companies_found': list(companies_found),
        'unis_found': list(unis_found),
        'hk_unis_found': list(hk_unis),
        'is_confirmed_collab': is_confirmed,
        'header_text': header[:500],  # For debugging
    }


def verify_paper(pdf_url, known_authors=None):
    """
    Full verification pipeline for a single paper.
    Returns parse result or None if PDF unavailable.
    """
    text = download_pdf_page1(pdf_url)
    if not text:
        return None
    return parse_affiliations(text, known_authors)


if __name__ == '__main__':
    # Test with HingeMem paper
    print("Testing HingeMem paper...")
    result = verify_paper("https://arxiv.org/pdf/2604.06845v1")
    if result:
        print(f"  Companies in header: {result['companies_found']}")
        print(f"  Unis in header: {result['unis_found']}")
        print(f"  HK unis: {result['hk_unis_found']}")
        print(f"  Confirmed collab: {result['is_confirmed_collab']}")
    
    time.sleep(3)
    
    # Test with a known ByteDance paper (In-Place TTT)
    print("\nTesting In-Place TTT paper...")
    result2 = verify_paper("https://arxiv.org/pdf/2604.06169v1")
    if result2:
        print(f"  Companies in header: {result2['companies_found']}")
        print(f"  Unis in header: {result2['unis_found']}")
        print(f"  Confirmed collab: {result2['is_confirmed_collab']}")
