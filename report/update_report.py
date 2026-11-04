import re

with open('report/major_project_report.tex', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Update Chapter Divider
old_divider = """% ==================== CHAPTER DIVIDER PAGE ====================
\\newcommand{\\chapterdivider}[2]{%
  \\clearpage
  \\thispagestyle{empty}
  \\vspace*{\\fill}
  \\begin{center}
    \\begin{tikzpicture}[remember picture, overlay]
      \\draw[line width=1.8pt, color=black] ($(current page.north west) + (1.2cm,-1.2cm)$) rectangle ($(current page.south east) + (-1.2cm,1.2cm)$);
      \\draw[line width=0.6pt, color=black] ($(current page.north west) + (1.35cm,-1.35cm)$) rectangle ($(current page.south east) + (-1.35cm,1.35cm)$);
    \\end{tikzpicture}
    {\\fontsize{24}{28}\\selectfont\\textbf{#1}}\\\\[1.5cm]
    {\\fontsize{26}{32}\\selectfont\\textbf{#2}}
  \\end{center}
  \\vspace*{\\fill}
  \\clearpage
}"""

new_divider = """% ==================== CHAPTER DIVIDER PAGE ====================
\\newcommand{\\chapterdivider}[2]{%
  \\clearpage
  \\thispagestyle{empty}
  \\noindent
  \\begin{tikzpicture}[remember picture, overlay]
    \\draw[line width=1.8pt, color=black] ($(current page.north west) + (1.2cm,-1.2cm)$) rectangle ($(current page.south east) + (-1.2cm,1.2cm)$);
    \\draw[line width=0.6pt, color=black] ($(current page.north west) + (1.35cm,-1.35cm)$) rectangle ($(current page.south east) + (-1.35cm,1.35cm)$);
    \\node[align=center, anchor=center] at (current page.center) {
      {\\fontsize{24}{28}\\selectfont\\textbf{#1}}\\\\[1.4cm]
      {\\fontsize{24}{30}\\selectfont\\textbf{#2}}
    };
  \\end{tikzpicture}%
  \\null
  \\clearpage
}"""

if old_divider in text:
    text = text.replace(old_divider, new_divider)
    print("Chapter divider updated successfully.")
else:
    print("Warning: old_divider exact match not found, checking with regex.")

# 2. Update Header & Footer
old_header = """% ==================== HEADER & FOOTER SETUP ====================
\\pagestyle{fancy}
\\fancyhf{}
\\renewcommand{\\headrulewidth}{1.8pt}
\\renewcommand{\\headrule}{\\hbox to\\headwidth{\\color{mitecrimson}\\leaders\\hrule height \\headrulewidth\\hfill}}
\\fancyhead[L]{\\small\\textbf{\\textsf{AI-BASED CLOUD NIDS USING HYBRID AE \\& XGBOOST}}}
\\fancyfoot[L]{\\small\\textsf{Dept. of CSE(AI\\&ML), MITE, Moodbidri}}
\\fancyfoot[R]{\\small\\textsf{Page \\textbar\\ \\thepage}}
\\renewcommand{\\footrulewidth}{0.8pt}

% Redefine plain page style for chapter first pages
\\fancypagestyle{plain}{%
  \\fancyhf{}%
  \\renewcommand{\\headrulewidth}{1.8pt}%
  \\renewcommand{\\headrule}{\\hbox to\\headwidth{\\color{mitecrimson}\\leaders\\hrule height \\headrulewidth\\hfill}}%
  \\fancyhead[L]{\\small\\textbf{\\textsf{AI-BASED CLOUD NIDS USING HYBRID AE \\& XGBOOST}}}%
  \\fancyfoot[L]{\\small\\textsf{Dept. of CSE(AI\\&ML), MITE, Moodbidri}}%
  \\fancyfoot[R]{\\small\\textsf{Page \\textbar\\ \\thepage}}%
  \\renewcommand{\\footrulewidth}{0.8pt}%
}"""

new_header = """% ==================== HEADER & FOOTER SETUP ====================
\\pagestyle{fancy}
\\fancyhf{}
\\renewcommand{\\headrulewidth}{1.8pt}
\\renewcommand{\\headrule}{\\hbox to\\headwidth{\\color{mitecrimson}\\leaders\\hrule height \\headrulewidth\\hfill}}
\\fancyhead[L]{\\small\\textbf{\\textsf{AI-based Network Intrusion Detection System using HYBRID AE \\& XGBOOST}}}
\\fancyfoot[L]{\\small\\textsf{Dept. of AI\\&ML, MITE, Moodbidri}}
\\fancyfoot[R]{\\small\\textsf{Page \\textbar\\ \\thepage}}
\\renewcommand{\\footrulewidth}{0.8pt}

% Redefine plain page style for chapter first pages (clean without header rule)
\\fancypagestyle{plain}{%
  \\fancyhf{}%
  \\renewcommand{\\headrulewidth}{0pt}%
  \\fancyfoot[L]{\\small\\textsf{Dept. of AI\\&ML, MITE, Moodbidri}}%
  \\fancyfoot[R]{\\small\\textsf{Page \\textbar\\ \\thepage}}%
  \\renewcommand{\\footrulewidth}{0.8pt}%
}"""

if old_header in text:
    text = text.replace(old_header, new_header)
    print("Header & Footer updated successfully.")
else:
    print("Warning: old_header exact match not found.")

# 3. Update Title Page
old_title_snippet = """\\begin{titlepage}
\\begin{tikzpicture}[remember picture, overlay]
  \\draw[line width=1.8pt, color=black] ($(current page.north west) + (1.2cm,-1.2cm)$) rectangle ($(current page.south east) + (-1.2cm,1.2cm)$);
  \\draw[line width=0.6pt, color=black] ($(current page.north west) + (1.35cm,-1.35cm)$) rectangle ($(current page.south east) + (-1.35cm,1.35cm)$);
\\end{tikzpicture}
\\centering

{\\large \\textbf{VISVESVARAYA TECHNOLOGICAL UNIVERSITY}}\\\\[2pt]
{\\small Jnana Sangama, Belagavi -- 590018}\\\\[0.6cm]

\\insertlogo{vtu_logo.png}{2.4cm}\\\\[0.3cm]

{\\large \\textbf{Project Report}}\\\\[4pt]
{\\small on}\\\\[0.3cm]

{\\large \\textbf{``AI-Based Cloud Network Intrusion Detection System Using Lightweight Hybrid Autoencoder and XGBoost with Real-Time Drift Adaptation''}}\\\\[0.5cm]

{\\footnotesize Submitted in partial fulfillment of the requirements for the award of the degree of}\\\\[4pt]
{\\textbf{BACHELOR OF ENGINEERING}}\\\\[2pt]
{\\footnotesize in}\\\\[2pt]
{\\textbf{COMPUTER SCIENCE AND ENGINEERING\\\\(ARTIFICIAL INTELLIGENCE AND MACHINE LEARNING)}}\\\\[0.5cm]

{\\small \\textbf{by}}\\\\[3pt]
\\begin{tabular}{ll}
\\textbf{ANSH PAWASKAR} & \\textbf{4MT22AI012} \\\\
\\textbf{NESAR NAIK} & \\textbf{4MT22AI034} \\\\
\\textbf{TEJASWINI} & \\textbf{4MT22AI058} \\\\
\\end{tabular}\\\\[0.5cm]

{\\small \\textbf{Under the Guidance of}}\\\\[2pt]
\\textbf{Dr. Maryjo M George}\\\\[2pt]
{\\footnotesize Assistant Professor, Department of AI \\& ML}\\\\[0.4cm]

\\insertlogo{mite_logo.png}{2.2cm}\\\\[0.2cm]

{\\footnotesize \\textbf{DEPARTMENT OF COMPUTER SCIENCE AND ENGINEERING\\\\(ARTIFICIAL INTELLIGENCE AND MACHINE LEARNING)}}\\\\[3pt]
{\\normalsize \\textbf{MANGALORE INSTITUTE OF TECHNOLOGY \\& ENGINEERING}}\\\\[2pt]
{\\scriptsize (A unit of Rajalaxmi Education Trust \\textregistered, Mangalore)}\\\\[2pt]
{\\scriptsize Autonomous Institute Affiliated to V.T.U., Belagavi, Approved by AICTE, New Delhi}\\\\[2pt]
{\\scriptsize Accredited by NAAC with A+ Grade \\& ISO 9001:2015 Certified Institution}\\\\[2pt]
{\\scriptsize Badaga Mijar, Moodabidri--574225, Karnataka}\\\\[4pt]
{\\small \\textbf{2025--26}}

\\end{titlepage}"""

new_title_snippet = """\\begin{titlepage}
\\begin{tikzpicture}[remember picture, overlay]
  \\draw[line width=1.8pt, color=black] ($(current page.north west) + (1.2cm,-1.2cm)$) rectangle ($(current page.south east) + (-1.2cm,1.2cm)$);
  \\draw[line width=0.6pt, color=black] ($(current page.north west) + (1.35cm,-1.35cm)$) rectangle ($(current page.south east) + (-1.35cm,1.35cm)$);
\\end{tikzpicture}
\\centering

{\\large \\textbf{VISVESVARAYA TECHNOLOGICAL UNIVERSITY}}\\\\[2pt]
{\\small Jnana Sangama, Belagavi -- 590018}\\\\[0.4cm]

\\insertlogo{vtu_logo.png}{2.0cm}\\\\[0.3cm]

{\\large \\textbf{Project Report}}\\\\[3pt]
{\\small on}\\\\[0.25cm]

{\\large \\textbf{``AI-Based Cloud Network Intrusion Detection System Using Lightweight Hybrid Autoencoder and XGBoost with Real-Time Drift Adaptation''}}\\\\[0.4cm]

{\\footnotesize Submitted in partial fulfillment of the requirements for the award of the degree of}\\\\[3pt]
{\\textbf{BACHELOR OF ENGINEERING}}\\\\[2pt]
{\\footnotesize in}\\\\[2pt]
{\\textbf{ARTIFICIAL INTELLIGENCE AND MACHINE LEARNING}}\\\\[0.4cm]

{\\small \\textbf{by}}\\\\[3pt]
\\begin{tabular}{ll}
\\textbf{ANSH PAWASKAR} & \\textbf{4MT22AI009} \\\\
\\textbf{NESAR NAIK} & \\textbf{4MT22AI036} \\\\
\\textbf{TEJESWINI} & \\textbf{4MT22AI057} \\\\
\\end{tabular}\\\\[0.4cm]

{\\small \\textbf{Under the Guidance of}}\\\\[2pt]
\\textbf{Mr. Srivatsa Upadhya P}\\\\[2pt]
{\\footnotesize Assistant Professor, Department of AI \\& ML}\\\\[0.3cm]

\\insertlogo{mite_logo.png}{1.8cm}\\\\[0.2cm]

{\\footnotesize \\textbf{DEPARTMENT OF ARTIFICIAL INTELLIGENCE AND MACHINE LEARNING}}\\\\[2pt]
{\\normalsize \\textbf{MANGALORE INSTITUTE OF TECHNOLOGY \\& ENGINEERING}}\\\\[2pt]
{\\scriptsize (A unit of Rajalaxmi Education Trust \\textregistered, Mangalore)}\\\\[2pt]
{\\scriptsize Autonomous Institute Affiliated to V.T.U., Belagavi, Approved by AICTE, New Delhi}\\\\[2pt]
{\\scriptsize Accredited by NAAC with A+ Grade \\& ISO 9001:2015 Certified Institution}\\\\[2pt]
{\\scriptsize Badaga Mijar, Moodabidri--574225, Karnataka}\\\\[3pt]
{\\small \\textbf{2025--26}}

\\end{titlepage}"""

if old_title_snippet in text:
    text = text.replace(old_title_snippet, new_title_snippet)
    print("Title page updated successfully.")
else:
    print("Warning: old_title_snippet exact match not found.")

# 4. Update Certificate Page (FIT ON ONE PAGE GUARANTEED)
old_cert_snippet = """\\clearpage
\\thispagestyle{empty}
\\begin{tikzpicture}[remember picture, overlay]
  \\draw[line width=1.8pt, color=black] ($(current page.north west) + (1.2cm,-1.2cm)$) rectangle ($(current page.south east) + (-1.2cm,1.2cm)$);
  \\draw[line width=0.6pt, color=black] ($(current page.north west) + (1.35cm,-1.35cm)$) rectangle ($(current page.south east) + (-1.35cm,1.35cm)$);
\\end{tikzpicture}

\\begin{center}
{\\normalsize \\textbf{MANGALORE INSTITUTE OF TECHNOLOGY \\& ENGINEERING}}\\\\[2pt]
{\\scriptsize (A unit of Rajalaxmi Education Trust \\textregistered, Mangalore)}\\\\[2pt]
{\\scriptsize Autonomous Institute Affiliated to V.T.U., Belagavi, Approved by AICTE, New Delhi}\\\\[2pt]
{\\scriptsize Accredited by NAAC with A+ Grade \\& ISO 9001:2015 Certified Institution}\\\\[2pt]
{\\scriptsize Badaga Mijar, Moodabidri--574225, Karnataka}\\\\[0.3cm]

{\\footnotesize \\textbf{DEPARTMENT OF COMPUTER SCIENCE AND ENGINEERING\\\\(ARTIFICIAL INTELLIGENCE AND MACHINE LEARNING)}}\\\\[0.3cm]

\\insertlogo{mite_logo.png}{1.8cm}\\\\[0.2cm]

{\\large \\textbf{CERTIFICATE}}\\\\[0.3cm]
\\end{center}

\\setstretch{1.3}
{\\small This is to certify that the project work entitled \\textbf{``AI-Based Cloud Network Intrusion Detection System Using Lightweight Hybrid Autoencoder and XGBoost with Real-Time Drift Adaptation''} is a bonafide work carried out by \\textbf{Ansh Pawaskar (4MT22AI012)}, \\textbf{Nesar Naik (4MT22AI034)}, and \\textbf{Tejaswini (4MT22AI058)} in partial fulfillment for the award of the degree of \\textbf{Bachelor of Engineering in Computer Science and Engineering (Artificial Intelligence and Machine Learning)} of the Visvesvaraya Technological University, Belagavi, during the academic year 2025--26. It is certified that all corrections and suggestions indicated for Internal Assessment have been incorporated in the report deposited in the departmental library. The project report has been approved as it satisfies the academic requirements in respect of project work prescribed for the Bachelor of Engineering degree.}\\\\[1.0cm]

\\noindent
\\begin{tabularx}{\\textwidth}{X c X}
\\textbf{Dr. Maryjo M George} & \\textbf{Dr. Sunil Kumar S} & \\textbf{Dr. Prashanth C M} \\\\
Project Guide & Head of the Department & Principal
\\end{tabularx}

\\vspace{1.2cm}
\\begin{center}
\\textbf{External Viva}
\\end{center}

\\vspace{0.3cm}
\\noindent
\\begin{tabularx}{\\textwidth}{X X}
\\textbf{Name of the Examiners} & \\textbf{Signature with Date} \\\\[0.8cm]
1) \\hrulefill & \\hrulefill \\\\[0.8cm]
2) \\hrulefill & \\hrulefill
\\end{tabularx}"""

new_cert_snippet = """\\clearpage
\\thispagestyle{empty}
\\begin{tikzpicture}[remember picture, overlay]
  \\draw[line width=1.8pt, color=black] ($(current page.north west) + (1.2cm,-1.2cm)$) rectangle ($(current page.south east) + (-1.2cm,1.2cm)$);
  \\draw[line width=0.6pt, color=black] ($(current page.north west) + (1.35cm,-1.35cm)$) rectangle ($(current page.south east) + (-1.35cm,1.35cm)$);
\\end{tikzpicture}

\\begin{center}
{\\normalsize \\textbf{MANGALORE INSTITUTE OF TECHNOLOGY \\& ENGINEERING}}\\\\[2pt]
{\\scriptsize (A unit of Rajalaxmi Education Trust \\textregistered, Mangalore)}\\\\[2pt]
{\\scriptsize Autonomous Institute Affiliated to V.T.U., Belagavi, Approved by AICTE, New Delhi}\\\\[2pt]
{\\scriptsize Accredited by NAAC with A+ Grade \\& ISO 9001:2015 Certified Institution}\\\\[2pt]
{\\scriptsize Badaga Mijar, Moodabidri--574225, Karnataka}\\\\[0.25cm]

{\\footnotesize \\textbf{DEPARTMENT OF ARTIFICIAL INTELLIGENCE AND MACHINE LEARNING}}\\\\[0.25cm]

\\insertlogo{mite_logo.png}{1.5cm}\\\\[0.15cm]

{\\large \\textbf{CERTIFICATE}}\\\\[0.25cm]
\\end{center}

\\setstretch{1.18}
{\\small This is to certify that the project work entitled \\textbf{``AI-Based Cloud Network Intrusion Detection System Using Lightweight Hybrid Autoencoder and XGBoost with Real-Time Drift Adaptation''} is a bonafide work carried out by \\textbf{Ansh Pawaskar (4MT22AI009)}, \\textbf{Nesar Naik (4MT22AI036)}, and \\textbf{Tejeswini (4MT22AI057)} in partial fulfillment for the award of the degree of \\textbf{Bachelor of Engineering in Artificial Intelligence and Machine Learning} of the Visvesvaraya Technological University, Belagavi, during the academic year 2025--26. It is certified that all corrections and suggestions indicated for Internal Assessment have been incorporated in the report deposited in the departmental library. The project report has been approved as it satisfies the academic requirements in respect of project work prescribed for the Bachelor of Engineering degree.}\\\\[0.45cm]

\\noindent
\\begin{tabularx}{\\textwidth}{>{\\raggedright\\arraybackslash}p{4.8cm} >{\\centering\\arraybackslash}X >{\\raggedleft\\arraybackslash}p{4.2cm}}
\\textbf{Mr. Srivatsa Upadhya P} & \\textbf{Dr. Sunil Kumar S} & \\textbf{Dr. Prashanth C M} \\\\
Project Guide & Head of the Department & Principal
\\end{tabularx}

\\vspace{0.4cm}
\\begin{center}
\\textbf{External Viva}
\\end{center}

\\vspace{0.2cm}
\\noindent
\\begin{tabularx}{\\textwidth}{X X}
\\textbf{Name of the Examiners} & \\textbf{Signature with Date} \\\\[0.55cm]
1) \\hrulefill & \\hrulefill \\\\[0.55cm]
2) \\hrulefill & \\hrulefill
\\end{tabularx}"""

if old_cert_snippet in text:
    text = text.replace(old_cert_snippet, new_cert_snippet)
    print("Certificate page updated successfully.")
else:
    print("Warning: old_cert_snippet exact match not found.")

# 5. Update Declaration Page
old_decl_snippet = """\\clearpage
\\thispagestyle{empty}
\\begin{tikzpicture}[remember picture, overlay]
  \\draw[line width=1.8pt, color=black] ($(current page.north west) + (1.2cm,-1.2cm)$) rectangle ($(current page.south east) + (-1.2cm,1.2cm)$);
  \\draw[line width=0.6pt, color=black] ($(current page.north west) + (1.35cm,-1.35cm)$) rectangle ($(current page.south east) + (-1.35cm,1.35cm)$);
\\end{tikzpicture}

\\begin{center}
{\\normalsize \\textbf{MANGALORE INSTITUTE OF TECHNOLOGY \\& ENGINEERING}}\\\\[2pt]
{\\scriptsize (A unit of Rajalaxmi Education Trust \\textregistered, Mangalore)}\\\\[2pt]
{\\scriptsize Autonomous Institute Affiliated to V.T.U., Belagavi, Approved by AICTE, New Delhi}\\\\[2pt]
{\\scriptsize Accredited by NAAC with A+ Grade \\& ISO 9001:2015 Certified Institution}\\\\[2pt]
{\\scriptsize Badaga Mijar, Moodabidri--574225, Karnataka}\\\\[0.3cm]

{\\footnotesize \\textbf{DEPARTMENT OF COMPUTER SCIENCE AND ENGINEERING\\\\(ARTIFICIAL INTELLIGENCE AND MACHINE LEARNING)}}\\\\[0.3cm]

\\insertlogo{mite_logo.png}{1.8cm}\\\\[0.2cm]

{\\large \\textbf{DECLARATION}}\\\\[0.3cm]
\\end{center}

\\setstretch{1.3}
{\\small We, \\textbf{Ansh Pawaskar (4MT22AI012)}, \\textbf{Nesar Naik (4MT22AI034)}, and \\textbf{Tejaswini (4MT22AI058)}, students of $8^{\\text{th}}$ semester B.E.\\ in Computer Science and Engineering (Artificial Intelligence and Machine Learning), Mangalore Institute of Technology \\& Engineering, Moodbidri, hereby declare that the project work entitled \\textbf{``AI-Based Cloud Network Intrusion Detection System Using Lightweight Hybrid Autoencoder and XGBoost with Real-Time Drift Adaptation''}, submitted to the Visvesvaraya Technological University, Belagavi during the academic year 2025--26, is a record of an original work done by us under the guidance of \\textbf{Dr. Maryjo M George}, Assistant Professor, Department of Artificial Intelligence and Machine Learning, Mangalore Institute of Technology \\& Engineering, Moodbidri.

This project work is submitted in partial fulfillment of the requirements for the award of the degree of Bachelor of Engineering in Computer Science and Engineering (Artificial Intelligence and Machine Learning). The results embodied in this report have not been submitted to any other University or Institute for the award of any degree.}\\\\[1.5cm]

\\noindent
\\begin{tabularx}{\\textwidth}{l X r}
\\textbf{Date:} & & \\textbf{Ansh Pawaskar (4MT22AI012)} \\\\[0.5cm]
\\textbf{Place:} Moodabidri & & \\textbf{Nesar Naik (4MT22AI034)} \\\\[0.5cm]
& & \\textbf{Tejaswini (4MT22AI058)}
\\end{tabularx}"""

new_decl_snippet = """\\clearpage
\\thispagestyle{empty}
\\begin{tikzpicture}[remember picture, overlay]
  \\draw[line width=1.8pt, color=black] ($(current page.north west) + (1.2cm,-1.2cm)$) rectangle ($(current page.south east) + (-1.2cm,1.2cm)$);
  \\draw[line width=0.6pt, color=black] ($(current page.north west) + (1.35cm,-1.35cm)$) rectangle ($(current page.south east) + (-1.35cm,1.35cm)$);
\\end{tikzpicture}

\\begin{center}
{\\normalsize \\textbf{MANGALORE INSTITUTE OF TECHNOLOGY \\& ENGINEERING}}\\\\[2pt]
{\\scriptsize (A unit of Rajalaxmi Education Trust \\textregistered, Mangalore)}\\\\[2pt]
{\\scriptsize Autonomous Institute Affiliated to V.T.U., Belagavi, Approved by AICTE, New Delhi}\\\\[2pt]
{\\scriptsize Accredited by NAAC with A+ Grade \\& ISO 9001:2015 Certified Institution}\\\\[2pt]
{\\scriptsize Badaga Mijar, Moodabidri--574225, Karnataka}\\\\[0.25cm]

{\\footnotesize \\textbf{DEPARTMENT OF ARTIFICIAL INTELLIGENCE AND MACHINE LEARNING}}\\\\[0.25cm]

\\insertlogo{mite_logo.png}{1.5cm}\\\\[0.15cm]

{\\large \\textbf{DECLARATION}}\\\\[0.25cm]
\\end{center}

\\setstretch{1.22}
{\\small We, \\textbf{Ansh Pawaskar (4MT22AI009)}, \\textbf{Nesar Naik (4MT22AI036)}, and \\textbf{Tejeswini (4MT22AI057)}, students of $8^{\\text{th}}$ semester B.E.\\ in Artificial Intelligence and Machine Learning, Mangalore Institute of Technology \\& Engineering, Moodbidri, hereby declare that the project work entitled \\textbf{``AI-Based Cloud Network Intrusion Detection System Using Lightweight Hybrid Autoencoder and XGBoost with Real-Time Drift Adaptation''}, submitted to the Visvesvaraya Technological University, Belagavi during the academic year 2025--26, is a record of an original work done by us under the guidance of \\textbf{Mr. Srivatsa Upadhya P}, Assistant Professor, Department of Artificial Intelligence and Machine Learning, Mangalore Institute of Technology \\& Engineering, Moodbidri.

This project work is submitted in partial fulfillment of the requirements for the award of the degree of Bachelor of Engineering in Artificial Intelligence and Machine Learning. The results embodied in this report have not been submitted to any other University or Institute for the award of any degree.}\\\\[1.0cm]

\\noindent
\\begin{tabularx}{\\textwidth}{l X r}
\\textbf{Date:} & & \\textbf{Ansh Pawaskar (4MT22AI009)} \\\\[0.5cm]
\\textbf{Place:} Moodabidri & & \\textbf{Nesar Naik (4MT22AI036)} \\\\[0.5cm]
& & \\textbf{Tejeswini (4MT22AI057)}
\\end{tabularx}"""

if old_decl_snippet in text:
    text = text.replace(old_decl_snippet, new_decl_snippet)
    print("Declaration page updated successfully.")
else:
    print("Warning: old_decl_snippet exact match not found.")

# 6. Update Acknowledgement Page
old_ack_snippet = """We express our sincere and heartfelt gratitude to our project guide, \\textbf{Dr. Maryjo M George}, Assistant Professor, Department of Artificial Intelligence and Machine Learning, for her patient guidance, insightful suggestions, and continuous encouragement throughout every phase of the research, model development, and manuscript authoring.

We express our sincere appreciation to \\textbf{Dr. Sunil Kumar S}, Associate Professor and Head, Department of Artificial Intelligence and Machine Learning, for providing state-of-the-art computational facilities, technical resources, and overall administrative support.

We extend our profound thanks to our respected Principal, \\textbf{Dr. Prashanth C M}, for his visionary leadership, academic encouragement, and for providing a supportive environment to accomplish this challenging project.

We also take this opportunity to thank the management of \\textbf{Mangalore Institute of Technology \\& Engineering} and the \\textbf{Rajalaxmi Education Trust \\textregistered}, Mangalore, for their unwavering commitment to academic excellence and research innovation.

Our special thanks go to all teaching and non-teaching faculty members of the Department of AI \\& ML for their continuous support and cooperation.

Above all, we express our profound gratitude to our parents, family members, and friends for their unconditional moral support, sacrifices, and belief in our abilities throughout our undergraduate tenure.\\\\[1.5cm]

\\noindent
\\begin{tabularx}{\\textwidth}{X r}
& \\textbf{Ansh Pawaskar (4MT22AI012)} \\\\
& \\textbf{Nesar Naik (4MT22AI034)} \\\\
& \\textbf{Tejaswini (4MT22AI058)}
\\end{tabularx}"""

new_ack_snippet = """We express our sincere and heartfelt gratitude to our project guide, \\textbf{Mr. Srivatsa Upadhya P}, Assistant Professor, Department of Artificial Intelligence and Machine Learning, for his patient guidance, insightful suggestions, and continuous encouragement throughout every phase of the research, model development, and manuscript authoring.

We would like to thank our project coordinator, \\textbf{Mr. Raghavendra Sooda}, Assistant Professor, Department of Artificial Intelligence and Machine Learning, for his cordial support, valuable feedback, and constructive critiques during internal reviews.

We express our sincere appreciation to \\textbf{Dr. Sunil Kumar S}, Associate Professor and Head, Department of Artificial Intelligence and Machine Learning, for providing state-of-the-art computational facilities, technical resources, and overall administrative support.

We extend our profound thanks to our respected Principal, \\textbf{Dr. Prashanth C M}, for his visionary leadership, academic encouragement, and for providing a supportive environment to accomplish this challenging project.

We also take this opportunity to thank the management of \\textbf{Mangalore Institute of Technology \\& Engineering} and the \\textbf{Rajalaxmi Education Trust \\textregistered}, Mangalore, for their unwavering commitment to academic excellence and research innovation.

Our special thanks go to all teaching and non-teaching faculty members of the Department of AI \\& ML for their continuous support and cooperation.

Above all, we express our profound gratitude to our parents, family members, and friends for their unconditional moral support, sacrifices, and belief in our abilities throughout our undergraduate tenure.\\\\[1.2cm]

\\noindent
\\begin{tabularx}{\\textwidth}{X r}
& \\textbf{Ansh Pawaskar (4MT22AI009)} \\\\
& \\textbf{Nesar Naik (4MT22AI036)} \\\\
& \\textbf{Tejeswini (4MT22AI057)}
\\end{tabularx}"""

if old_ack_snippet in text:
    text = text.replace(old_ack_snippet, new_ack_snippet)
    print("Acknowledgement page updated successfully.")
else:
    print("Warning: old_ack_snippet exact match not found.")

# 7. Update List of Figures & Tables on ONE page
old_lof_lot = """% ------------------------------------------------------------
% 7. LIST OF FIGURES (ROMAN PAGE ix)
% ------------------------------------------------------------
\\clearpage
\\listoffigures

% ------------------------------------------------------------
% 8. LIST OF TABLES (ROMAN PAGE x)
% ------------------------------------------------------------
\\clearpage
\\listoftables"""

new_lof_lot = """% ------------------------------------------------------------
% 7. LIST OF FIGURES & LIST OF TABLES (SINGLE PAGE)
% ------------------------------------------------------------
\\clearpage
\\begingroup
\\let\\clearpage\\relax
\\let\\cleardoublepage\\relax
\\listoffigures
\\vspace{0.9cm}
\\listoftables
\\endgroup
\\clearpage"""

if old_lof_lot in text:
    text = text.replace(old_lof_lot, new_lof_lot)
    print("LOF and LOT combined onto single page.")
else:
    print("Warning: old_lof_lot exact match not found.")

# 8. Update all \\begin{figure}[!t] to \\begin{figure}[H]
# to prevent images from ever floating before sections
count_fig = text.count('\\begin{figure}[!t]')
text = text.replace('\\begin{figure}[!t]', '\\begin{figure}[H]')
print(f"Replaced {count_fig} instances of \\begin{{figure}}[!t] with [H].")

# 9. Update Dashboard snapshots to be stacked vertically on ONE page, large size
old_dash = """\\begin{figure}[H]
\\centering
\\begin{subfigure}[t]{0.48\\textwidth}
\\centering
\\insertfigure{dashboard_home.png}{Dashboard Main View}
\\caption{Telemetry and Live Sniffing Monitor}
\\label{fig:dash_main}
\\end{subfigure}
\\hfill
\\begin{subfigure}[t]{0.48\\textwidth}
\\centering
\\insertfigure{dashboard_alert.png}{Dashboard Threat Analysis View}
\\caption{Threat Diagnosis and SHAP Waterfall Display}
\\label{fig:dash_threat}
\\end{subfigure}
\\caption{Streamlit Web Dashboard Snapshots: (a) Real-Time Flow Telemetry, and (b) Threat Alert View with Local SHAP Feature Explanations.}
\\label{fig:dashboard_snapshots}
\\end{figure}"""

new_dash = """\\begin{figure}[H]
\\centering
\\begin{subfigure}[b]{0.96\\linewidth}
  \\centering
  \\insertfigure{dashboard_home.png}{Dashboard Main View}
  \\caption{Real-Time Network Flow Telemetry and Live Sniffing Monitor}
  \\label{fig:dash_main}
\\end{subfigure}
\\\\[0.4cm]
\\begin{subfigure}[b]{0.96\\linewidth}
  \\centering
  \\insertfigure{dashboard_alert.png}{Dashboard Threat Analysis View}
  \\caption{Threat Diagnosis, Anomaly Alerts, and Local TreeSHAP Waterfall Explanation}
  \\label{fig:dash_threat}
\\end{subfigure}
\\caption{Streamlit Web Dashboard Snapshots: Real-Time Flow Telemetry (Top) and Threat Alert Analysis View with Local SHAP Feature Explanations (Bottom).}
\\label{fig:dashboard_snapshots}
\\end{figure}"""

if old_dash in text:
    text = text.replace(old_dash, new_dash)
    print("Dashboard snapshots updated to stacked full-width layout.")
else:
    print("Warning: old_dash exact match not found.")

# 10. Update Chapter 11 metadata table authors
text = text.replace(
    "\\textbf{Authors} & \\textbf{Ansh Pawaskar, Nesar Naik, and Tejaswini} \\\\",
    "\\textbf{Authors} & \\textbf{Ansh Pawaskar, Nesar Naik, and Tejeswini} \\\\"
)

with open('report/major_project_report.tex', 'w', encoding='utf-8') as f:
    f.write(text)

print("All updates written to report/major_project_report.tex successfully.")
