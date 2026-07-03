"""Smoke test — generates a PDF with every API method. Run with: python _demo.py"""
from pdf_studio import Document, Style, Font
import matplotlib.pyplot as plt
import pandas as pd

# Build a document using every public API method
doc = Document()
doc.set_header("Demo | Page {page} of {total}")
doc.add_heading("PDF Studio Demo", level=0)
doc.add_paragraph("This document proves every API method works.", Style(font=Font("Lora", 11)))

fig, ax = plt.subplots()
ax.bar(["A", "B", "C"], [1, 2, 3])
doc.add_chart(fig)

df = pd.DataFrame({"City": ["Delhi", "Mumbai"], "Revenue": [100, 200]})
doc.add_table(df, caption="Q3 Results")

doc.render("_demo_output.pdf")

# Self-check
import os
assert os.path.getsize("_demo_output.pdf") > 1000, "PDF too small — render may have failed"
os.remove("_demo_output.pdf")
print("✅ pdf-studio v0.1.0 smoke test passed")
