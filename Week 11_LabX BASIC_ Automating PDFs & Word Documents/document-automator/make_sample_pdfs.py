# Helper: creates the sample input PDFs in documents/ (needs: pip install reportlab)
import os
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

D = os.path.join(os.path.dirname(__file__), 'documents')
os.makedirs(D, exist_ok=True)

def simple(name, lines):
    c = canvas.Canvas(os.path.join(D, name), pagesize=A4)
    y = 780
    for ln in lines:
        c.drawString(72, y, ln); y -= 18
    c.save()

simple('dummy_doc1.pdf', ["This is Dummy Document 1 for merging test."])
simple('dummy_doc2.pdf', ["This is Dummy Document 2 for merging test."])

c = canvas.Canvas(os.path.join(D, 'input_article.pdf'), pagesize=A4)
page1 = ["Introduction to Automation", "",
 "Automation is the creation and application of technology to produce and deliver goods and services with minimal human intervention.",
 "The implementation of automation technologies, techniques, and processes improves the efficiency, reliability, and speed of many tasks",
 "that were previously performed manually.", "",
 "This leads to increased productivity, reduced costs, and improved quality."]
page2 = ["Benefits of Automation", "",
 "1. Increased Efficiency: Tasks are completed faster and with higher throughput.",
 "2. Cost Reduction: Lower labor costs and reduced waste.",
 "3. Improved Accuracy: Minimizes human error.",
 "4. Enhanced Safety: Dangerous tasks can be automated.",
 "5. Greater Consistency: Uniform quality in output.", "",
 "Conclusion", "",
 "Automation is transforming industries globally. Embracing these technologies is crucial for future competitiveness."]
for pg in (page1, page2):
    y = 780
    for ln in pg:
        c.setFont("Helvetica-Bold" if ln in ("Introduction to Automation","Benefits of Automation","Conclusion") else "Helvetica", 10)
        c.drawString(50, y, ln); y -= 16
    c.showPage()
c.save()
