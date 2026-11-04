import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import nsdecls
from docx.oxml import parse_xml

doc = docx.Document()

def add_code_listing(doc, caption, code_lines):
    # Caption
    p_cap = doc.add_paragraph()
    p_cap.paragraph_format.space_before = Pt(8)
    p_cap.paragraph_format.space_after = Pt(4)
    run_cap = p_cap.add_run(caption)
    run_cap.font.name = "Times New Roman"
    run_cap.font.size = Pt(10)
    run_cap.font.bold = True
    
    # Table box
    table = doc.add_table(rows=1, cols=1)
    table.alignment = docx.enum.table.WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    
    cell = table.cell(0, 0)
    cell.width = Inches(6.0)
    
    # Table borders: left thick blue, others subtle gray
    tblPr = table._tbl.tblPr
    tblBorders = parse_xml(r'''
        <w:tblBorders %s>
            <w:top w:val="single" w:sz="4" w:space="0" w:color="D0D0D0"/>
            <w:left w:val="single" w:sz="18" w:space="0" w:color="0056B3"/>
            <w:bottom w:val="single" w:sz="4" w:space="0" w:color="D0D0D0"/>
            <w:right w:val="single" w:sz="4" w:space="0" w:color="D0D0D0"/>
        </w:tblBorders>
    ''' % nsdecls('w'))
    tblPr.append(tblBorders)
    
    # Cell shading & margins
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(r'<w:shd %s w:val="clear" w:color="auto" w:fill="F8F9FA"/>' % nsdecls('w'))
    tcMar = parse_xml(r'''
        <w:tcMar %s>
            <w:top w:w="120" w:type="dxa"/>
            <w:left w:w="160" w:type="dxa"/>
            <w:bottom w:w="120" w:type="dxa"/>
            <w:right w:w="160" w:type="dxa"/>
        </w:tcMar>
    ''' % nsdecls('w'))
    tcPr.append(shd)
    tcPr.append(tcMar)
    
    # Clear default paragraph in cell
    p_first = cell.paragraphs[0]
    p_first.paragraph_format.space_before = Pt(0)
    p_first.paragraph_format.space_after = Pt(1)
    p_first.paragraph_format.line_spacing = 1.0
    
    for idx, line in enumerate(code_lines):
        p = p_first if idx == 0 else cell.add_paragraph()
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(1)
        p.paragraph_format.line_spacing = 1.0
        
        r = p.add_run(line)
        r.font.name = "Consolas"
        r.font.size = Pt(8.5)
        r.font.color.rgb = RGBColor(0x20, 0x20, 0x20)
        
    # Spacing after table
    p_after = doc.add_paragraph()
    p_after.paragraph_format.space_before = Pt(4)
    p_after.paragraph_format.space_after = Pt(6)

sample_code = [
    "def build_autoencoder(input_dim: int, dropout_rate: float = 0.20) -> Model:",
    "    inp = Input(shape=(input_dim,), name='flow_input')",
    "    x = Dense(128, activation='relu')(inp)",
    "    x = Dropout(dropout_rate)(x)",
    "    x = Dense(64, activation='relu')(x)",
    "    bottleneck = Dense(16, activation='relu', name='bottleneck')(x)",
    "    x = Dense(64, activation='relu')(bottleneck)",
    "    x = Dense(128, activation='relu')(x)",
    "    out = Dense(input_dim, activation='linear')(x)",
    "    model = Model(inputs=inp, outputs=out, name='Autoencoder')",
    "    model.compile(optimizer=Adam(learning_rate=0.001), loss='mse')",
    "    return model"
]

add_code_listing(doc, "Listing 5.1: Deep Symmetric Autoencoder Architecture & Training Routine", sample_code)
doc.save("scratch/test_code_box.docx")
print("Saved test_code_box.docx successfully!")
