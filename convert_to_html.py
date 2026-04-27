#!/usr/bin/env python3
import markdown
from pathlib import Path

# Read markdown file
md_file = Path('PROJECT_DOCUMENTATION_GUIDE.md')
with open(md_file, 'r', encoding='utf-8') as f:
    md_content = f.read()

# Convert to HTML
html_content = markdown.markdown(md_content, extensions=['extra', 'codehilite', 'toc'])

# Create HTML file
html_template = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>EV Diagnostic Assistant - Complete Documentation</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            background: white;
        }
        h1 {
            color: #0066cc;
            border-bottom: 3px solid #0066cc;
            padding-bottom: 10px;
            page-break-after: avoid;
        }
        h2 {
            color: #0066cc;
            margin-top: 30px;
            page-break-after: avoid;
        }
        h3 {
            color: #0099ff;
            page-break-after: avoid;
        }
        code {
            background: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
        }
        pre {
            background: #f4f4f4;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
            border-left: 4px solid #0066cc;
        }
        table {
            border-collapse: collapse;
            width: 100%;
            margin: 15px 0;
        }
        table th, table td {
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }
        table th {
            background: #0066cc;
            color: white;
        }
        ul, ol {
            margin: 10px 0;
            padding-left: 20px;
        }
        li {
            margin: 5px 0;
        }
        @media print {
            body { margin: 0; padding: 10px; }
            h1, h2, h3 { page-break-after: avoid; }
            pre { page-break-inside: avoid; }
            table { page-break-inside: avoid; }
        }
    </style>
</head>
<body>
""" + html_content + """
</body>
</html>
"""

# Save HTML
html_file = Path('PROJECT_DOCUMENTATION_GUIDE.html')
with open(html_file, 'w', encoding='utf-8') as f:
    f.write(html_template)

print('✅ HTML file created: PROJECT_DOCUMENTATION_GUIDE.html')
print('📄 File size:', html_file.stat().st_size, 'bytes')
print('\nTo convert to PDF, you can:')
print('1. Open the HTML file in a browser')
print('2. Press Ctrl+P (or Cmd+P on Mac)')
print('3. Select "Save as PDF"')
print('\nOr use online tools like:')
print('- https://html2pdf.com/')
print('- https://cloudconvert.com/')
