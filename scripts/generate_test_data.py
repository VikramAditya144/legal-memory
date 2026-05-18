#!/usr/bin/env python3
"""
Generate dummy test data for the Legal Memory system.

Creates:
  - Sample WhatsApp chat exports (iOS and Android formats)
  - Real PDF legal documents using fpdf2
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import random

sys.path.insert(0, str(Path(__file__).parent.parent))

OUTPUT_DIR = Path(__file__).parent.parent / "sample_data"


def generate_whatsapp_ios(filename: str):
    messages = [
        ("Alice Johnson", "Hi team, reviewing the vendor agreement. Need to check the arbitration clause."),
        ("Bob Smith", "The arbitration clause is on page 3. We modified it to require mandatory mediation first."),
        ("Alice Johnson", "Thanks. I also noticed the payment terms specify net-30 with a 2% discount for net-10."),
        ("Bob Smith", "That's correct. We negotiated those terms carefully with their finance team."),
        ("Carol Davis", "Is there a termination without cause clause? What's the notice period?"),
        ("Bob Smith", "Yes, it requires 90 days notice for termination without cause. 30 days if either party is in breach."),
        ("Alice Johnson", "And what about the IP ownership clause? I want to make sure we retain all intellectual property."),
        ("Carol Davis", "The IP clause states work product created during the engagement belongs to us. Background IP stays with vendor."),
        ("Bob Smith", "Exactly. We also have a non-compete clause that extends for 12 months after termination."),
        ("Alice Johnson", "Good. What about the confidentiality period for the NDA we signed?"),
        ("Carol Davis", "The NDA confidentiality obligations survive termination for 3 years. We extended it from the standard 2 years."),
        ("Bob Smith", "Right. And don't forget the insurance requirements - we need at least $2M in general liability coverage."),
        ("Alice Johnson", "That's noted. Any other key terms I should review before we sign?"),
        ("Carol Davis", "The severance package for key employees includes 6 months salary plus benefits continuation."),
        ("Bob Smith", "Also, the force majeure clause now includes pandemic-related events."),
        ("Alice Johnson", "Perfect. I'll document these and prepare the final signature package."),
        ("Bob Smith", "The client requested changes to the dispute resolution clause. They want arbitration in New York."),
        ("Alice Johnson", "That's a significant change. We should review the implications for venue and applicable law."),
        ("Carol Davis", "I agree. Let me check our past disputes and see if New York jurisdiction would have made a difference."),
        ("Bob Smith", "Also, they're asking about late payment penalties. Should we impose interest on overdue invoices?"),
        ("Alice Johnson", "Standard practice is 1.5% monthly interest on overdue amounts, with a minimum of $100."),
        ("Carol Davis", "I found three similar contracts. Two had 1.5% monthly, one had a flat 5% annual rate."),
        ("Bob Smith", "Let's go with the 1.5% monthly approach as it's more standard and recovers costs better."),
    ]

    current_date = datetime(2024, 5, 15, 9, 30, 0)
    lines = []
    for sender, text in messages:
        ts = current_date.strftime("[%m/%d/%y, %H:%M:%S]")
        lines.append(f"{ts} {sender}: {text}")
        current_date += timedelta(minutes=random.randint(1, 15))

    Path(filename).write_text("\n".join(lines))
    print(f"✅ Created {filename} ({len(lines)} messages, iOS format)")


def generate_whatsapp_android(filename: str):
    messages = [
        ("Alice Johnson", "The employment agreement needs revision. Are we keeping the non-compete clause?"),
        ("Bob Smith", "Yes, we agreed to keep it. It's 12 months from termination date."),
        ("Carol Davis", "What about the severance package terms? I need to confirm with HR."),
        ("Bob Smith", "Severance is 6 months of salary plus benefits continuation for 30 days after termination."),
        ("Alice Johnson", "That aligns with what we discussed. Are there any vesting schedules we need to include?"),
        ("Carol Davis", "Stock options vest over 4 years with a 1-year cliff. Standard startup terms."),
        ("Bob Smith", "I'll incorporate these into the final draft. What about the indemnification clause?"),
        ("Alice Johnson", "The employee should be indemnified for actions within the scope of their role."),
        ("Carol Davis", "We also need to include the standard representations and warranties section."),
        ("Bob Smith", "Will do. Let me also confirm the governing law - should this be Delaware or California?"),
        ("Alice Johnson", "Delaware is our standard for employee agreements. We've had good outcomes with Delaware courts."),
        ("Carol Davis", "Updated the vendor contract for review. Main changes are in the service level agreements section."),
        ("Bob Smith", "What are the uptime requirements?"),
        ("Carol Davis", "99.5% monthly uptime guarantee with 5% service credit for each 0.1% below target."),
        ("Alice Johnson", "That's a strong SLA. What about response times for support?"),
        ("Carol Davis", "Critical issues: 1 hour response, High: 4 hours, Medium: 1 day, Low: 2 days"),
        ("Bob Smith", "Good. Are there any penalties if they don't meet these SLAs?"),
        ("Carol Davis", "Service credits accumulate and can result in contract termination if they fall below 98% for 3 months."),
        ("Alice Johnson", "Excellent. This protects us well. When can we send it to them for signature?"),
        ("Bob Smith", "I'll prepare the signature version by end of week."),
    ]

    current_date = datetime(2024, 5, 20, 10, 15, 0)
    lines = []
    for sender, text in messages:
        ts = current_date.strftime("%m/%d/%Y, %H:%M")
        lines.append(f"{ts} - {sender}: {text}")
        current_date += timedelta(minutes=random.randint(1, 20))

    Path(filename).write_text("\n".join(lines))
    print(f"✅ Created {filename} ({len(lines)} messages, Android format)")


def generate_pdf(filename: str, title: str, sections: list[tuple[str, str]]):
    """Generate a real PDF using fpdf2."""
    try:
        from fpdf import FPDF
    except ImportError:
        print("❌ fpdf2 not installed. Run: pip install fpdf2")
        return

    pdf = FPDF()
    pdf.set_margins(25, 25, 25)
    pdf.add_page()

    # Title
    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 12, title, ln=True, align="C")
    pdf.ln(4)
    pdf.set_draw_color(148, 163, 184)
    pdf.line(25, pdf.get_y(), 185, pdf.get_y())
    pdf.ln(8)

    for section_title, body in sections:
        # Section heading
        pdf.set_font("Helvetica", "B", 13)
        pdf.set_text_color(15, 23, 42)
        pdf.cell(0, 8, section_title, ln=True)
        pdf.ln(2)

        # Body text
        pdf.set_font("Helvetica", "", 11)
        pdf.set_text_color(51, 65, 85)
        pdf.multi_cell(0, 6, body)
        pdf.ln(6)

    pdf.output(filename)
    print(f"✅ Created {filename} (real PDF, {pdf.page} page(s))")


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("Generating test data...\n")

    # WhatsApp exports
    generate_whatsapp_ios(str(OUTPUT_DIR / "sample_whatsapp_ios.txt"))
    generate_whatsapp_android(str(OUTPUT_DIR / "sample_whatsapp_android.txt"))

    # Real PDF: Service Agreement
    generate_pdf(
        str(OUTPUT_DIR / "sample_contract.pdf"),
        "SERVICE AGREEMENT",
        [
            ("1. SERVICES",
             "The Provider agrees to provide consulting services related to legal document analysis and "
             "contract review as detailed in this agreement. Services include document drafting, review, "
             "negotiation support, and legal research."),
            ("2. PAYMENT TERMS",
             "Services will be billed on a monthly basis. Payment is due within 30 days of invoice date. "
             "A 2% early payment discount is available for settlement within 10 days of invoice. "
             "Overdue amounts accrue interest at 1.5% per month (minimum $100)."),
            ("3. TERMINATION",
             "Either party may terminate this agreement with 90 days written notice. Immediate termination "
             "is permitted if either party materially breaches the agreement and fails to cure within 30 days "
             "of written notice. Upon termination all confidential materials must be returned or destroyed."),
            ("4. INTELLECTUAL PROPERTY",
             "All work product and deliverables created by Provider under this agreement shall be the "
             "exclusive property of Client upon full payment. Provider's pre-existing materials and background "
             "intellectual property shall remain Provider's sole and exclusive property."),
            ("5. CONFIDENTIALITY",
             "All confidential information shared under this agreement shall remain confidential during the "
             "term and for a period of 3 years following termination. Neither party shall disclose the "
             "other's confidential information to any third party without prior written consent."),
            ("6. LIABILITY & INSURANCE",
             "Provider shall maintain comprehensive general liability insurance of at least $2,000,000 per "
             "occurrence and $5,000,000 in aggregate throughout the term of this agreement. Certificates "
             "of insurance shall be provided upon request."),
            ("7. DISPUTE RESOLUTION",
             "Any disputes arising under this agreement shall first be subject to mandatory mediation before "
             "proceeding to binding arbitration. Arbitration shall take place in New York, New York under "
             "the AAA Commercial Arbitration Rules. The prevailing party shall be entitled to recover "
             "reasonable attorneys' fees and costs."),
            ("8. GOVERNING LAW",
             "This agreement shall be governed by the laws of the State of Delaware, without regard to "
             "its conflict of laws provisions. The parties consent to the exclusive jurisdiction of the "
             "courts of Delaware for any matters not subject to arbitration."),
        ],
    )

    # Real PDF: NDA
    generate_pdf(
        str(OUTPUT_DIR / "sample_nda.pdf"),
        "NON-DISCLOSURE AGREEMENT",
        [
            ("RECITALS",
             "This Non-Disclosure Agreement ('Agreement') is entered into as of May 1, 2024, by and between "
             "the parties identified below (each a 'Party' and collectively the 'Parties') for the purpose "
             "of exploring a potential business relationship."),
            ("1. DEFINITION OF CONFIDENTIAL INFORMATION",
             "Confidential Information means all non-public, proprietary, or confidential information "
             "disclosed by one Party (the 'Disclosing Party') to the other Party (the 'Receiving Party'), "
             "whether orally, in writing, electronically, or by any other means, including but not limited "
             "to: trade secrets, business plans, financial information, customer lists, technical data, "
             "know-how, and any other information designated as confidential."),
            ("2. OBLIGATIONS OF RECEIVING PARTY",
             "The Receiving Party agrees to: (a) maintain the confidentiality of all Confidential Information "
             "using at least the same degree of care as it uses to protect its own confidential information, "
             "but no less than reasonable care; (b) limit access to Confidential Information to those "
             "employees or contractors with a legitimate need to know; (c) not use Confidential Information "
             "for any purpose other than evaluating the potential business relationship."),
            ("3. TERM AND DURATION",
             "The obligations under this Agreement shall remain in effect during the term of any subsequent "
             "agreement between the Parties and shall survive termination for a period of three (3) years. "
             "The Parties mutually agreed to extend the standard 2-year confidentiality period given the "
             "sensitivity of the information being shared."),
            ("4. EXCLUSIONS",
             "Confidential Information does not include information that: (a) is or becomes publicly available "
             "through no breach of this Agreement; (b) was already known to the Receiving Party at time of "
             "disclosure; (c) is independently developed without use of Confidential Information; "
             "(d) must be disclosed under applicable law or court order, provided the Disclosing Party "
             "receives prompt written notice and an opportunity to seek a protective order."),
            ("5. RETURN OR DESTRUCTION",
             "Upon written request by the Disclosing Party or termination of this Agreement, the Receiving "
             "Party shall promptly return or certifiably destroy all Confidential Information and any copies "
             "thereof, and shall certify such destruction in writing within five (5) business days."),
            ("6. REMEDIES",
             "The Parties acknowledge that any breach of this Agreement may cause irreparable harm for which "
             "monetary damages would be an inadequate remedy. Accordingly, the Disclosing Party shall be "
             "entitled to seek injunctive or other equitable relief in addition to all other remedies "
             "available at law or equity."),
        ],
    )

    print(f"\n{'='*55}")
    print("✅ All test data generated in sample_data/")
    print("\nTo test ingestion:")
    print("  1. docker compose up -d")
    print("  2. streamlit run main.py  (or: uvicorn api:app)")
    print("  3. Upload files from sample_data/")


if __name__ == "__main__":
    main()
