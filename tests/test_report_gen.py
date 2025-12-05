
from src.reporting.html_report import generate_html_report
from src.reporting.markdown_report import generate_markdown_report
from src.reporting.pdf_report import generate_pdf_report
import os

def test_report_generation():
    print("Testing All Report Generators...")
    
    # Mock Results Data
    results = {
        "target": "Linus Torvalds",
        "target_type": "individual",
        "statistics": {
            "total_unique": 15,
            "confirmed_count": 2,
            "possible_count": 13,
            "avg_quality_score": 85.5
        },
        "emails": {
            "confirmed_emails": [
                {"email": "torvalds@linux-foundation.org", "source": "PGP Keyserver", "confidence": 1.0},
                {"email": "linus@kernel.org", "source": "HIBP Breach Data", "confidence": 1.0}
            ],
            "possible_emails": [
                {"email": "linus.torvalds@gmail.com", "source": "Pattern Generation", "confidence": 0.5},
                {"email": "ltorvalds@gmail.com", "source": "Pattern Generation", "confidence": 0.5}
            ]
        },
        "social_media": [
            {"platform": "GitHub", "url": "https://github.com/torvalds", "source": "Search Dork", "confidence": 0.9},
            {"platform": "Twitter", "url": "https://twitter.com/Linus__Torvalds", "source": "Active Check", "confidence": 0.7}
        ]
    }
    
    # Create outputs directory
    os.makedirs("tests/outputs", exist_ok=True)
    
    # Test HTML
    html_file = "tests/outputs/test_report_v1.3.html"
    try:
        generate_html_report(results, html_file)
        if os.path.exists(html_file):
            print(f"✓ HTML Report generated: {html_file}")
    except Exception as e:
        print(f"✗ HTML Generation Failed: {e}")

    # Test Markdown
    md_file = "tests/outputs/test_report_v1.3.md"
    try:
        generate_markdown_report(results, md_file)
        if os.path.exists(md_file):
            print(f"✓ Markdown Report generated: {md_file}")
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if "Confirmed Findings" in content and "PGP Keyserver" in content:
                    print("  ✓ Markdown content verified")
                else:
                    print("  ✗ Markdown content missing tiered data")
    except Exception as e:
        print(f"✗ Markdown Generation Failed: {e}")

    # Test PDF
    pdf_file = "tests/outputs/test_report_v1.3.pdf"
    try:
        generate_pdf_report(results, pdf_file)
        if os.path.exists(pdf_file):
            print(f"✓ PDF Report generated: {pdf_file}")
    except Exception as e:
        print(f"✗ PDF Generation Failed: {e}")

if __name__ == "__main__":
    test_report_generation()
