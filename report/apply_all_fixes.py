import re

with open('report/major_project_report.tex', 'r', encoding='utf-8') as f:
    text = f.read()

# Normalize line endings
text = text.replace('\r\n', '\n')

# 1. Update Chapter Divider Macro to constrain width and center mathematically
old_div_pattern = r'\\newcommand\{\\chapterdivider\}\[2\]\{.*?\n\}'
new_div_code = r'''\newcommand{\chapterdivider}[2]{%
  \clearpage
  \thispagestyle{empty}
  \noindent
  \begin{tikzpicture}[remember picture, overlay]
    \draw[line width=1.8pt, color=black] ($(current page.north west) + (1.2cm,-1.2cm)$) rectangle ($(current page.south east) + (-1.2cm,1.2cm)$);
    \draw[line width=0.6pt, color=black] ($(current page.north west) + (1.35cm,-1.35cm)$) rectangle ($(current page.south east) + (-1.35cm,1.35cm)$);
    \node[align=center, anchor=center, text width=14.0cm] at (current page.center) {
      {\fontsize{22}{28}\selectfont\textbf{#1}}\\[1.0cm]
      {\fontsize{22}{28}\selectfont\textbf{#2}}
    };
  \end{tikzpicture}%
  \null
  \clearpage
}'''
text = re.sub(old_div_pattern, lambda m: new_div_code, text, flags=re.DOTALL)
print("Updated chapterdivider macro.")

# 2. Update specific chapter divider calls with linebreaks for long titles
text = text.replace(
    r'\chapterdivider{CHAPTER -- 3}{SYSTEM REQUIREMENT SPECIFICATION}',
    r'\chapterdivider{CHAPTER -- 3}{SYSTEM REQUIREMENT\\SPECIFICATION}'
)
text = text.replace(
    r'\chapterdivider{CHAPTER -- 9}{CONCLUSION AND FUTURE WORK}',
    r'\chapterdivider{CHAPTER -- 9}{CONCLUSION AND\\FUTURE WORK}'
)
text = text.replace(
    r'\chapterdivider{CHAPTER -- 11}{VISIBLE RESEARCH OUTPUT}',
    r'\chapterdivider{CHAPTER -- 11}{VISIBLE RESEARCH\\OUTPUT}'
)
print("Updated chapterdivider title line breaks.")

# 3. Update Preamble: Define plain pagestyle for frontmatter (NO header, only roman footer)
old_hf_pattern = r'% ==================== HEADER & FOOTER SETUP ====================.*?(?=\\begin\{document\})'
new_hf_code = r'''% ==================== HEADER & FOOTER SETUP ====================
% Default plain style for Front Matter (Title, Cert, Decl, Abstract, Ack, TOC, LOF, LOT)
% Has NO header, NO header rule, only footer page number!
\fancypagestyle{plain}{%
  \fancyhf{}%
  \renewcommand{\headrulewidth}{0pt}%
  \renewcommand{\footrulewidth}{0pt}%
  \fancyfoot[C]{\small\textsf{\thepage}}%
}

% Main fancy style for Chapters 1-11
\fancypagestyle{mainfancy}{%
  \fancyhf{}%
  \renewcommand{\headrulewidth}{1.8pt}%
  \renewcommand{\headrule}{\hbox to\headwidth{\color{mitecrimson}\leaders\hrule height \headrulewidth\hfill}}%
  \fancyhead[L]{\small\textbf{\textsf{AI-based Network Intrusion Detection System using HYBRID AE \& XGBOOST}}}%
  \fancyfoot[L]{\small\textsf{Dept. of AI\&ML, MITE, Moodbidri}}%
  \fancyfoot[R]{\small\textsf{Page \textbar\ \thepage}}%
  \renewcommand{\footrulewidth}{0.8pt}%
}

% Start document with plain frontmatter style (NO headers before Chapter 1)
\pagestyle{plain}
'''
text = re.sub(old_hf_pattern, lambda m: new_hf_code, text, flags=re.DOTALL)
print("Updated header & footer preamble.")

# 4. Update Abstract to be concise
old_abstract_pattern = r'\\begin\{center\}\s*\{\\Large \\textbf\{ABSTRACT\}\}\\\\\[0\.6cm\]\s*\\end\{center\}.*?(?=% -+\n% 5\. ACKNOWLEDGEMENT)'
new_abstract_code = r'''\begin{center}
{\Large \textbf{ABSTRACT}}\\[0.6cm]
\end{center}

Modern cloud and enterprise networks face an evolving landscape of high-velocity cyber threats, including volumetric Denial of Service (DoS) floods, stealthy reconnaissance scans, and credential-stuffing exploits. While machine learning and deep learning offer promising diagnostic capabilities, existing Network Intrusion Detection Systems (NIDSs) suffer from an enduring trade-off: supervised classifiers fail against unseen zero-day attacks, whereas unsupervised anomaly detectors suffer from elevated false alarms and arbitrary Gaussian threshold collapse ($\mu + 3\sigma$). Furthermore, cross-partition data leakage frequently inflates published laboratory accuracy while concealing operational blindspots.

This major project develops a leakage-free, two-stage hybrid NIDS that unifies unsupervised anomaly screening with multi-class attack classification and alert-gated explainability. In the first stage, a deep symmetric Autoencoder ($d \rightarrow 128 \rightarrow 64 \rightarrow 32 \rightarrow 16 \rightarrow 32 \rightarrow 64 \rightarrow 128 \rightarrow d$) is trained exclusively on legitimate benign traffic to establish a non-parametric normal boundary. Records exceeding a validation-calibrated Youden's $J$ threshold ($\tau^* = 0.1973$ for CICIDS2018; $\tau^* = 0.0840$ for NSL-KDD) are flagged as anomalies and classified by an Extreme Gradient Boosted tree ensemble (XGBoost). Explainable AI (TreeSHAP) is invoked strictly for flagged alerts to maintain line-rate throughput, while a sliding buffer ($W=500, q=95\%$) adapts to concept drift.

Evaluated on strictly deduplicated partitions of CSE-CIC-IDS2018 ($671{,}131$ flows) and NSL-KDD ($147{,}790$ instances), the hybrid pipeline achieves \textbf{99.70\% attack recall}, flags \textbf{93.11\% of unseen DoS} and \textbf{82.22\% of unseen Probe} attacks under Leave-One-Attack-Out validation, and delivers a sub-millisecond inference latency of \textbf{0.1830~ms per flow} ($5{,}464$~flows/s) on commodity CPU hardware with a peak memory footprint of \textbf{527.0~MB RSS}. A real-time web dashboard supports live packet sniffing and threat analytics.\\[0.6cm]

\noindent
\textbf{Keywords:} Network Intrusion Detection, Autoencoder, XGBoost, Anomaly Screening, Youden's $J$-Statistic, TreeSHAP, Concept Drift, Zero-Day Generalization, Streamlit.

'''
text = re.sub(old_abstract_pattern, lambda m: new_abstract_code, text, flags=re.DOTALL)
print("Updated abstract to concise version.")

# 5. Ensure Chapter 1 activates mainfancy style (running headers start HERE)
old_ch1_pattern = r'% ------------------------------------------------------------\s*% CHAPTER 1 DIVIDER & BODY\s*% ------------------------------------------------------------\s*\\chapterdivider\{CHAPTER -- 1\}\{INTRODUCTION\}\s*\\chapter\{INTRODUCTION\}'
new_ch1_code = r'''% ------------------------------------------------------------
% CHAPTER 1 DIVIDER & BODY
% ------------------------------------------------------------
\chapterdivider{CHAPTER -- 1}{INTRODUCTION}

% Activate running header from Chapter 1 onwards
\pagestyle{mainfancy}
% Also let plain pagestyle (first page of chapters) use mainfancy headers and footers
\fancypagestyle{plain}{%
  \fancyhf{}%
  \renewcommand{\headrulewidth}{1.8pt}%
  \renewcommand{\headrule}{\hbox to\headwidth{\color{mitecrimson}\leaders\hrule height \headrulewidth\hfill}}%
  \fancyhead[L]{\small\textbf{\textsf{AI-based Network Intrusion Detection System using HYBRID AE \& XGBOOST}}}%
  \fancyfoot[L]{\small\textsf{Dept. of AI\&ML, MITE, Moodbidri}}%
  \fancyfoot[R]{\small\textsf{Page \textbar\ \thepage}}%
  \renewcommand{\footrulewidth}{0.8pt}%
}

\chapter{INTRODUCTION}'''
text = re.sub(old_ch1_pattern, lambda m: new_ch1_code, text, flags=re.DOTALL)
print("Updated Chapter 1 header activation.")

# 6. Ensure LOF and LOT are on ONE single page with clean title spacing
old_lof_lot_pattern = r'% ------------------------------------------------------------\s*% 7\. LIST OF FIGURES & LIST OF TABLES.*?\\clearpage\s*(?=% =+)'
new_lof_lot_code = r'''% ------------------------------------------------------------
% 7. LIST OF FIGURES & LIST OF TABLES (ON ONE SINGLE PAGE)
% ------------------------------------------------------------
\clearpage
\begingroup
\let\clearpage\relax
\let\cleardoublepage\relax
\listoffigures
\vspace{0.8cm}
\listoftables
\endgroup
\clearpage
'''
text = re.sub(old_lof_lot_pattern, lambda m: new_lof_lot_code, text, flags=re.DOTALL)
print("Updated LOF & LOT single page block.")

with open('report/major_project_report.tex', 'w', encoding='utf-8') as f:
    f.write(text)

print("All modifications applied successfully.")
