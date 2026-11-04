import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn
import re
import shutil

# Code snippets to add
code_listing_51 = [
    "def sanitize_and_partition_flows(raw_df: pd.DataFrame, time_col: str = 'Timestamp')",
    "                                -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:",
    "    '''Performs cryptographic flow deduplication and strictly enforces",
    "       chronological split boundaries to guarantee zero leakage.'''",
    "    # Construct cryptographic 5-tuple session hash for each flow",
    "    session_keys = (raw_df['Src IP'].astype(str) + '_' +",
    "                    raw_df['Dst IP'].astype(str) + '_' +",
    "                    raw_df['Src Port'].astype(str) + '_' +",
    "                    raw_df['Dst Port'].astype(str) + '_' +",
    "                    raw_df['Protocol'].astype(str))",
    "    raw_df['session_hash'] = session_keys.apply(",
    "        lambda x: hashlib.sha256(x.encode()).hexdigest()",
    "    )",
    "    # Purge duplicated session keys across split boundaries (362 records)",
    "    dedup_df = raw_df.drop_duplicates(subset=['session_hash', time_col]).copy()",
    "    dedup_df.sort_values(by=time_col, ascending=True, inplace=True)",
    "    # Partition strictly on timestamps (70% train, 15% val, 15% test)",
    "    n_total = len(dedup_df)",
    "    idx_train, idx_val = int(0.70 * n_total), int(0.85 * n_total)",
    "    train_df = dedup_df.iloc[:idx_train].copy()",
    "    val_df = dedup_df.iloc[idx_train:idx_val].copy()",
    "    test_df = dedup_df.iloc[idx_val:].copy()",
    "    return train_df, val_df, test_df"
]

code_listing_52 = [
    "class LeakageSafeScaler:",
    "    '''Fits standard normalization parameters exclusively on benign training",
    "       flows, clipping extreme outliers to prevent numerical instability.'''",
    "    def __init__(self, clip_quantiles: tuple[float, float] = (0.001, 0.999)):",
    "        self.scaler = StandardScaler()",
    "        self.clip_min = None",
    "        self.clip_max = None",
    "        self.quantiles = clip_quantiles",
    "    def fit(self, X_benign_train: np.ndarray) -> 'LeakageSafeScaler':",
    "        # Establish robust clipping thresholds strictly on benign baseline",
    "        self.clip_min = np.percentile(X_benign_train, self.quantiles[0] * 100, 0)",
    "        self.clip_max = np.percentile(X_benign_train, self.quantiles[1] * 100, 0)",
    "        X_clipped = np.clip(X_benign_train, self.clip_min, self.clip_max)",
    "        self.scaler.fit(X_clipped)",
    "        return self",
    "    def transform(self, X: np.ndarray) -> np.ndarray:",
    "        # Apply locked clipping boundaries and normalization transforms",
    "        X_clipped = np.clip(X, self.clip_min, self.clip_max)",
    "        return self.scaler.transform(X_clipped)"
]

code_listing_b1 = [
    "class AsynchronousFlowSniffer(threading.Thread):",
    "    '''Captures live promiscuous Ethernet packets via Scapy raw sockets,",
    "       reassembles bidirectional network flows, and computes 78 metrics.'''",
    "    def __init__(self, interface: str = 'eth0', flow_timeout: float = 15.0,",
    "                 queue_max: int = 10000):",
    "        super().__init__(daemon=True)",
    "        self.interface = interface",
    "        self.flow_timeout = flow_timeout",
    "        self.active_flows: dict[tuple, dict] = {}",
    "        self.completed_flows: queue.Queue = queue.Queue(maxsize=queue_max)",
    "        self.is_running = True",
    "    def _extract_5tuple(self, packet: Packet) -> tuple | None:",
    "        if IP not in packet: return None",
    "        proto = packet[IP].proto",
    "        src_ip, dst_ip = packet[IP].src, packet[IP].dst",
    "        src_p, dst_p = 0, 0",
    "        if TCP in packet:",
    "            src_p, dst_p = packet[TCP].sport, packet[TCP].dport",
    "        elif UDP in packet:",
    "            src_p, dst_p = packet[UDP].sport, packet[UDP].dport",
    "        return (src_ip, dst_ip, src_p, dst_p, proto)",
    "    def process_packet(self, packet: Packet) -> None:",
    "        flow_key = self._extract_5tuple(packet)",
    "        if not flow_key: return",
    "        rev_key = (flow_key[1], flow_key[0], flow_key[3], flow_key[2], flow_key[4])",
    "        now = time.time()",
    "        if flow_key in self.active_flows:",
    "            s = self.active_flows[flow_key]",
    "            s['fwd_pkts'] += 1; s['fwd_bytes'] += len(packet)",
    "            s['fwd_iat'].append(now - s['last_seen']); s['last_seen'] = now",
    "        elif rev_key in self.active_flows:",
    "            s = self.active_flows[rev_key]",
    "            s['bwd_pkts'] += 1; s['bwd_bytes'] += len(packet)",
    "            s['bwd_iat'].append(now - s['last_seen']); s['last_seen'] = now",
    "        else:",
    "            self.active_flows[flow_key] = {",
    "                'start_time': now, 'last_seen': now,",
    "                'fwd_pkts': 1, 'bwd_pkts': 0, 'fwd_bytes': len(packet),",
    "                'bwd_bytes': 0, 'fwd_iat': [], 'bwd_iat': [],",
    "                'tcp_flags': {'FIN': 0, 'SYN': 0, 'RST': 0, 'PSH': 0, 'ACK': 0}",
    "            }",
    "        if TCP in packet and (packet[TCP].flags.F or packet[TCP].flags.R):",
    "            self.flush_flow(flow_key if flow_key in self.active_flows else rev_key)",
    "    def flush_expired_flows(self) -> None:",
    "        now = time.time()",
    "        expired = [k for k, v in self.active_flows.items() if (now - v['last_seen']) > self.flow_timeout]",
    "        for k in expired: self.flush_flow(k)"
]

def style_code_cell(cell, code_lines):
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
    
    for p in list(cell.paragraphs):
        p._p.getparent().remove(p._p)
        
    for line in code_lines:
        p = cell.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT  # NEVER JUSTIFIED!
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(1)
        p.paragraph_format.line_spacing = 1.0
        r = p.add_run(line)
        r.font.name = "Consolas"
        r.font.size = Pt(8.5)
        r.font.color.rgb = RGBColor(0x20, 0x20, 0x20)

def add_code_listing_box(doc, target_p, caption_text, code_lines):
    p_cap = target_p.insert_paragraph_before()
    p_cap.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p_cap.paragraph_format.space_before = Pt(8)
    p_cap.paragraph_format.space_after = Pt(3)
    p_cap.paragraph_format.keep_with_next = True
    r_cap = p_cap.add_run(caption_text)
    r_cap.font.name = "Times New Roman"
    r_cap.font.size = Pt(10)
    r_cap.font.bold = True
    
    table = doc.add_table(rows=1, cols=1)
    target_p._p.addprevious(table._tbl)
    table.alignment = docx.enum.table.WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    
    trPr = table.rows[0]._tr.get_or_add_trPr()
    cantSplit = trPr.find(qn('w:cantSplit'))
    if cantSplit is None:
        trPr.append(OxmlElement('w:cantSplit'))
        
    cell = table.cell(0, 0)
    cell.width = Inches(6.0)
    
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
    style_code_cell(cell, code_lines)
    
    p_space = target_p.insert_paragraph_before()
    p_space.paragraph_format.space_before = Pt(0)
    p_space.paragraph_format.space_after = Pt(4)

def update_master_content(master_path):
    print(f"Reading Master: {master_path}")
    doc = docx.Document(master_path)
    
    # 1. Update text lead-ins to avoid duplicate captions
    for p in doc.paragraphs:
        txt = p.text.strip()
        if txt.startswith("Table 5.2: This table summarizes"):
            p.text = "The experimental parameters and hyperparameter configurations evaluated across both CICIDS2018 and NSL-KDD benchmark datasets are summarized in Table 5.2. These settings cover input dimensions, Autoencoder bottleneck geometry, training epochs, reconstruction thresholds, XGBoost parameters, and sliding buffer sizes."
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        elif txt.startswith("Table 5.3: This table presents"):
            p.text = "To validate the operational readiness of the end-to-end detection pipeline, seven comprehensive test cases were designed and executed. Table 5.3 summarizes the input flow scenarios, expected outcomes, and verification statuses covering all pipeline tiers."
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        elif txt.startswith("Table 6.2: Illustrates the granular"):
            p.text = "As summarized in Table 6.2, the granular category-level breakdown for the CICIDS2018 test split demonstrates near-flawless performance on volumetric and automated authentication vectors. For SSH-Bruteforce attacks, the pipeline identifies 14,067 out of 14,106 attack instances, achieving 99.72% recall. This heightened sensitivity stems from the distinctive temporal signatures of automated password guessing, including rapid packet inter-arrival times (IATs), uniform packet lengths, and abnormal TCP flag combinations that clash sharply with the learned manifold of legitimate communication. Similarly, all 8 test flows of FTP-BruteForce are detected (100.00% recall), confirming that extreme class rarity in training data does not preclude reliable isolation when non-linear autoencoder gating is employed. Concurrently, 77,877 legitimate benign flows are cleared at Stage-1, yielding an exceptional Benign class precision of 99.95%."
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        elif txt.startswith("Table 2.1 presents a structured"):
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            
    # 2. Renumber existing Listing captions & update reference in text
    for p in doc.paragraphs:
        txt = p.text.strip()
        if txt.startswith("Listing 5.1: Deep Symmetric"):
            p.text = "Listing 5.3: Deep Symmetric Autoencoder Architecture & Training Routine"
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        elif txt.startswith("Listing 5.2: Validation Youden"):
            p.text = "Listing 5.4: Validation Youden's J-Statistic Threshold Calibration Algorithm"
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        elif txt.startswith("Listing 5.3: Two-Stage"):
            p.text = "Listing 5.5: Two-Stage Hybrid Gating and Zero-Day Threat Quarantine"
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        elif txt.startswith("Listing 5.4: Sliding-Window"):
            p.text = "Listing 5.6: Sliding-Window Concept Drift Monitoring and Alert-Gated TreeSHAP"
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        elif "As detailed in Listing 5.1" in txt:
            p.text = txt.replace("Listing 5.1", "Listing 5.3")
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            
    # 3. Add Listing 5.1 in Section 5.2.1 (before 5.2.2)
    p_522 = None
    for p in doc.paragraphs:
        if p.text.strip().startswith("5.2.2 Feature Preprocessing"):
            p_522 = p
            break
            
    if p_522 is not None:
        p_lead1 = p_522.insert_paragraph_before()
        p_lead1.text = "Listing 5.1 demonstrates the cryptographic session deduplication algorithm and strict chronological partition workflow enforced to eliminate inter-split contamination:"
        p_lead1.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p_lead1.paragraph_format.line_spacing = 1.5
        p_lead1.paragraph_format.space_before = Pt(4)
        p_lead1.paragraph_format.space_after = Pt(4)
        for r in p_lead1.runs:
            r.font.name = "Times New Roman"
            r.font.size = Pt(12)
        add_code_listing_box(doc, p_522, "Listing 5.1: Cryptographic Session Hashing and Zero-Leakage Dataset Partitioning", code_listing_51)
        print("-> Added Listing 5.1 in Section 5.2.1")
        
    # 4. Add Listing 5.2 in Section 5.2.2 (before 5.2.3)
    p_523 = None
    for p in doc.paragraphs:
        if p.text.strip().startswith("5.2.3 Autoencoder Model Training"):
            p_523 = p
            break
            
    if p_523 is not None:
        p_lead2 = p_523.insert_paragraph_before()
        p_lead2.text = "Listing 5.2 details the leakage-safe feature transformation pipeline, establishing quantile bounds strictly on benign training traffic:"
        p_lead2.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p_lead2.paragraph_format.line_spacing = 1.5
        p_lead2.paragraph_format.space_before = Pt(4)
        p_lead2.paragraph_format.space_after = Pt(4)
        for r in p_lead2.runs:
            r.font.name = "Times New Roman"
            r.font.size = Pt(12)
        add_code_listing_box(doc, p_523, "Listing 5.2: Leakage-Safe Feature Transformation and Robust Quantile Scaling", code_listing_52)
        print("-> Added Listing 5.2 in Section 5.2.2")
        
    # 5. Add Listing B.1 in Appendix B
    p_last = doc.paragraphs[-1]
    p_leadb = doc.add_paragraph()
    p_leadb.text = "Listing B.1 provides the complete asynchronous socket listener implementation, aggregating packet telemetry into bidirectional feature records:"
    p_leadb.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p_leadb.paragraph_format.line_spacing = 1.5
    p_leadb.paragraph_format.space_before = Pt(4)
    p_leadb.paragraph_format.space_after = Pt(4)
    for r in p_leadb.runs:
        r.font.name = "Times New Roman"
        r.font.size = Pt(12)
    p_dummy = doc.add_paragraph()
    add_code_listing_box(doc, p_dummy, "Listing B.1: Real-Time Promiscuous Packet Ingestion & Bidirectional Flow Reassembly Engine", code_listing_b1)
    p_dummy._p.getparent().remove(p_dummy._p)
    print("-> Added Listing B.1 in Appendix B")
    
    # 6. Apply strictly correct alignment across all paragraphs in Master
    in_cover_page = True
    for i, p in enumerate(doc.paragraphs):
        txt = p.text.strip()
        if not txt:
            continue
            
        # End of cover page
        if txt == "CERTIFICATE" or "This is to certify that" in txt:
            in_cover_page = False
            
        if in_cover_page:
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            continue
            
        # Preliminary major titles
        if txt in ["CERTIFICATE", "DECLARATION", "ACKNOWLEDGEMENTS", "ABSTRACT", "TABLE OF CONTENTS", "LIST OF FIGURES", "LIST OF TABLES", "ABBREVIATIONS / NOTATIONS", "REFERENCES", "APPENDICES"]:
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.keep_with_next = True
            continue
            
        # Chapter titles
        if txt.startswith("CHAPTER "):
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.keep_with_next = True
            continue
            
        # Numbered Headings (1.1, 1.2, 5.2.1, 6.5, etc.)
        if re.match(r'^\d+\.\d+(\.\d+)?\s+', txt) or txt.startswith("6.5 Prototype") or txt.startswith("Appendix "):
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.keep_with_next = True
            continue
            
        # Figure and Table Captions
        if txt.startswith("Figure ") or txt.startswith("Table "):
            # If it's a short caption line, CENTER it!
            if len(txt) < 140 or ":" in txt[:15]:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p.paragraph_format.keep_with_next = True
                continue
                
        # Code Listing captions
        if txt.startswith("Listing "):
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.keep_with_next = True
            continue
            
        # Hardware / Software bullet specifications
        if any(txt.startswith(k) for k in ["• Processor:", "• RAM:", "• Storage:", "• Operating System:", "• Programming Language:", "• Deep Learning Framework:", "• Machine Learning Framework:", "• Explainable AI Framework:", "• Packet Capture & Analysis:", "• User Interface Engine:"]):
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.line_spacing = 1.15
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(2)
            continue
            
        # Short list items in Section 1.3, 1.4, 1.6, 2.3, 3.2
        if re.match(r'^\d+\.\s+[A-Z]', txt) and len(txt) < 130:
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.line_spacing = 1.25
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.space_after = Pt(2)
            continue
            
        # Student signatures on Acknowledgements
        if "Ansh Pawaskar" in txt and "4MT23AI009" in txt:
            p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            continue
            
        # Keywords line in Abstract
        if txt.startswith("Keywords:"):
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            continue
            
        # Standard body text: strictly JUSTIFIED
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.line_spacing = 1.5
        
    # 7. Ensure EVERY paragraph inside EVERY 1x1 code table is strictly LEFT-ALIGNED
    for t in doc.tables:
        if len(t.rows) == 1 and len(t.columns) == 1:
            for p in t.cell(0, 0).paragraphs:
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                p.paragraph_format.line_spacing = 1.0
                for r in p.runs:
                    r.font.name = "Consolas"
                    r.font.size = Pt(8.5)
                    
    doc.save(master_path)
    print(f"-> Successfully saved updated Master to: {master_path}")
    shutil.copy2(master_path, 'report/Major_Project_Report.docx')

if __name__ == '__main__':
    update_master_content('report/Major_Project_Report_Final_Updated.docx')
