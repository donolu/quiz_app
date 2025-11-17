from zipfile import ZipFile
from pathlib import Path
import xml.etree.ElementTree as ET
import sys

path = Path(sys.argv[1])
with ZipFile(path) as z:
    data = z.read('word/document.xml')

root = ET.fromstring(data)
NS = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
texts = []
for para in root.findall('.//w:p', NS):
    parts = []
    for node in para.findall('.//w:t', NS):
        parts.append(node.text or '')
    text = ''.join(parts).strip()
    if text:
        texts.append(text)

for line in texts:
    print(line)
