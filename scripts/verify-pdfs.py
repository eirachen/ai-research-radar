"""
PDF Verification Script
Verifies collab confidence by downloading PDFs and parsing first-page affiliations.
Runs incrementally: only processes papers where pdfVerified=False.
Limit per run to avoid timeout.
"""
import json
import os
import sys
import time

# Add scripts dir to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pdf_parser import verify_paper, COMPANY_IDENTIFIERS

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ARXIV_JSON = os.path.join(SCRIPT_DIR, "..", "reports", "arxiv-daily.json")
MAX_PER_RUN = 15  # Limit to avoid timeout


def main():
    with open(ARXIV_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    verified = 0
    confirmed = 0
    downgraded = 0

    for company_id, company_data in data["companies"].items():
        for paper in company_data["papers"]:
            if paper.get("pdfVerified"):
                continue
            if not paper.get("pdfUrl"):
                continue
            if verified >= MAX_PER_RUN:
                break

            print(f"  Verifying: {paper['title'][:60]}...")
            result = verify_paper(paper["pdfUrl"])
            time.sleep(2)  # Rate limit

            if result:
                paper["pdfVerified"] = True
                paper["pdfCompanies"] = result["companies_found"]
                paper["pdfUnis"] = result["unis_found"][:5]
                paper["pdfHKUnis"] = result["hk_unis_found"]

                if result["is_confirmed_collab"]:
                    paper["collabConfidence"] = "confirmed"
                    paper["hasUniCollab"] = True
                    confirmed += 1
                    print(f"    ✅ CONFIRMED: companies={result['companies_found']}, unis={result['unis_found'][:3]}")
                else:
                    if result["companies_found"] and not result["unis_found"]:
                        paper["collabConfidence"] = "company_only"
                        paper["hasUniCollab"] = False
                        downgraded += 1
                        print(f"    🏢 Company only: {result['companies_found']}")
                    elif result["unis_found"] and not result["companies_found"]:
                        paper["collabConfidence"] = "uni_only"
                        paper["hasUniCollab"] = False
                        downgraded += 1
                        print(f"    🎓 Uni only: {result['unis_found'][:3]}")
                    else:
                        paper["collabConfidence"] = "mentioned"
                        downgraded += 1
                        print(f"    ⚠️ No company/uni in header")
            else:
                paper["pdfVerified"] = True
                paper["collabConfidence"] = paper.get("collabConfidence", "mentioned")
                print(f"    ❌ PDF unavailable")

            verified += 1

        if verified >= MAX_PER_RUN:
            break

    # Update counts
    for company_id, company_data in data["companies"].items():
        company_data["uniCollabCount"] = sum(1 for p in company_data["papers"] if p.get("hasUniCollab"))
        company_data["hkCollabCount"] = sum(1 for p in company_data["papers"] if p.get("hasHKCollab"))

    data["totalUniCollab"] = sum(c["uniCollabCount"] for c in data["companies"].values())
    data["totalHKCollab"] = sum(c["hkCollabCount"] for c in data["companies"].values())

    with open(ARXIV_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # Stats
    total = sum(len(c["papers"]) for c in data["companies"].values())
    total_verified = sum(1 for c in data["companies"].values() for p in c["papers"] if p.get("pdfVerified"))
    print(f"\nThis run: {verified} verified ({confirmed} confirmed, {downgraded} downgraded)")
    print(f"Overall: {total_verified}/{total} papers verified")


if __name__ == "__main__":
    main()
