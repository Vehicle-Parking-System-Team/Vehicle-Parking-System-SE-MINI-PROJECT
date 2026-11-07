"""Build the three editable specifications from their reviewed Markdown sources.

Requires python-docx and Pillow. PDF export uses LibreOffice (see docs/README.md).
"""
from pathlib import Path
import re

from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.section import WD_SECTION_START, WD_ORIENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SOURCES = [
    ROOT/'docs/requirements/Vehicle_Parking_System_SRS.md',
    ROOT/'docs/SAD/Vehicle_Parking_System_SAD.md',
    ROOT/'docs/testing/Vehicle_Parking_System_Test_Plan.md',
]


def text(value):
    return re.sub(r'\[([^]]+)\]\([^)]+\)', r'\1', value).replace('**', '').replace('`', '')


def field(paragraph, name):
    node = OxmlElement('w:fldSimple')
    node.set(qn('w:instr'), name)
    paragraph._p.append(node)


def build(source):
    doc = Document()
    doc.core_properties.author = 'Vehicle Parking System Project Team'
    doc.core_properties.last_modified_by = 'Vehicle Parking System Project Team'
    doc.core_properties.title = source.read_text(encoding='utf-8').splitlines()[0].lstrip('# ')
    section = doc.sections[0]
    section.page_width, section.page_height = Inches(8.5), Inches(11)
    section.top_margin = section.bottom_margin = Inches(.8)
    section.left_margin = section.right_margin = Inches(.85)
    for name in ['Normal', 'Title', 'Subtitle', 'Heading 1', 'Heading 2', 'Heading 3']:
        style = doc.styles[name]
        style.font.name = 'Calibri'
        style.font.color.rgb = RGBColor(0, 0, 0)
        style.font.size = Pt(11 if name == 'Normal' else {'Title':24, 'Subtitle':12, 'Heading 1':17, 'Heading 2':13, 'Heading 3':11}[name])
        style.paragraph_format.space_after = Pt(7)
    doc.styles['Normal'].paragraph_format.line_spacing = 1.1
    # Remove template paragraph rules from titles and inherited styles.
    for style in doc.styles:
        for border in style.element.findall('.//' + qn('w:pBdr')):
            border.getparent().remove(border)
    header = section.header.paragraphs[0]
    header.text = 'VEHICLE PARKING SYSTEM  |  ENGINEERING DOCUMENTATION'
    header.style = doc.styles['Normal']
    for run in header.runs:
        run.font.size = Pt(8)
    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    footer.add_run('Version 2.0  |  Page ')
    field(footer, 'PAGE')
    lines = source.read_text(encoding='utf-8').splitlines()
    i = 0
    code = False
    contents_inserted = False
    requirement_group = False
    while i < len(lines):
        line = lines[i].strip()
        i += 1
        if not line or line == '---':
            continue
        if line.startswith('```'):
            code = not code
            continue
        if line.startswith('|'):
            rows = [line]
            while i < len(lines) and lines[i].strip().startswith('|'):
                rows.append(lines[i].strip()); i += 1
            cells = [[text(c.strip()) for c in row.strip('|').split('|')] for row in rows if not re.match(r'^\|[ :|\-]+\|$', row)]
            table = doc.add_table(rows=1, cols=len(cells[0]))
            table.autofit = False
            for col in table.columns:
                col.width = Inches(6.8/len(cells[0]))
            for ri, row in enumerate(cells):
                target = table.rows[0] if ri == 0 else table.add_row()
                no_split = OxmlElement('w:cantSplit'); target._tr.get_or_add_trPr().append(no_split)
                if ri == 0:
                    repeat = OxmlElement('w:tblHeader'); target._tr.get_or_add_trPr().append(repeat)
                for ci, val in enumerate(row):
                    cell = target.cells[ci]
                    cell.text = val
                    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
                    props = cell._tc.get_or_add_tcPr()
                    borders = OxmlElement('w:tcBorders')
                    for side in ['top','left','bottom','right']:
                        border = OxmlElement('w:'+side)
                        for key, value in [('val','single'),('sz','4'),('color','D9D9D9')]:
                            border.set(qn('w:'+key), value)
                        borders.append(border)
                    props.append(borders)
                    shading = OxmlElement('w:shd')
                    shading.set(qn('w:fill'), 'DCE6F1' if ri == 0 else ('F5F7FA' if ri % 2 == 0 else 'FFFFFF'))
                    props.append(shading)
                    for paragraph in cell.paragraphs:
                        paragraph.paragraph_format.space_before = Pt(4)
                        paragraph.paragraph_format.space_after = Pt(4)
                        for run in paragraph.runs:
                            run.font.size = Pt(9)
                            run.bold = ri == 0
            doc.add_paragraph().paragraph_format.space_after = Pt(2)
        elif line.startswith('!['):
            match = re.match(r'!\[([^]]*)\]\(([^)]+)\)', line)
            if not match:
                raise ValueError(line)
            image = (source.parent/match[2]).resolve()
            with Image.open(image) as picture:
                width, height = picture.size
            landscape = width/height > 1.1
            scale = min((9.3 if landscape else 6.8)/width, (6.6 if landscape else 8.3)/height)
            # Dedicated figure sections use the orientation that fits the model.
            figure_section = doc.add_section(WD_SECTION_START.NEW_PAGE)
            figure_section.orientation = WD_ORIENT.LANDSCAPE if landscape else WD_ORIENT.PORTRAIT
            figure_section.page_width = Inches(11 if landscape else 8.5)
            figure_section.page_height = Inches(8.5 if landscape else 11)
            paragraph = doc.add_paragraph()
            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
            paragraph.add_run().add_picture(str(image), width=Inches(width*scale))
            paragraph.paragraph_format.keep_with_next = True
            caption = doc.add_paragraph(match[1])
            caption.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for run in caption.runs:
                run.font.size = Pt(9)
                run.italic = True
            next_line = next((value.strip() for value in lines[i:] if value.strip()), '')
            if not next_line.startswith('!['):
                body_section = doc.add_section(WD_SECTION_START.NEW_PAGE)
                body_section.orientation = WD_ORIENT.PORTRAIT
                body_section.page_width, body_section.page_height = Inches(8.5), Inches(11)
        elif line.startswith('# '):
            doc.add_paragraph(text(line[2:]), 'Title')
        elif line.startswith('## '):
            if not contents_inserted:
                doc.add_paragraph('Contents', 'Subtitle')
                field(doc.add_paragraph(), 'TOC \\o "1-1" \\h \\z \\u')
                doc.add_page_break()
                contents_inserted = True
            doc.add_heading(text(line[3:]), 1)
        elif line.startswith('### '):
            doc.add_heading(text(line[4:]), 2)
        elif line.startswith('#### '):
            doc.add_heading(text(line[5:]), 3)
            requirement_group = bool(re.match(r'#### FR-\d+', line))
        else:
            paragraph = doc.add_paragraph(text(line[2:]) if line.startswith('- ') else text(line), 'List Bullet' if line.startswith('- ') else 'Normal')
            if requirement_group:
                paragraph.paragraph_format.keep_with_next = not line.startswith('Verification:')
                if line.startswith('Verification:'):
                    requirement_group = False
            if code:
                for run in paragraph.runs:
                    run.font.name = 'Consolas'; run.font.size = Pt(9)
    output = source.with_suffix('.docx')
    doc.save(output)
    print(output.relative_to(ROOT))


if __name__ == '__main__':
    for source in SOURCES:
        build(source)
