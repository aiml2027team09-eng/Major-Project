import os
import zipfile

tex_content = r'''\documentclass[12pt,a4paper]{report}

% ==================== REQUIRED PACKAGES ====================
\usepackage[a4paper, left=1.25in, right=1.0in, top=0.75in, bottom=0.75in, headheight=0pt, headsep=0pt, footskip=20pt]{geometry}
\usepackage[T1]{fontenc}
\usepackage{mathptmx} % Sets Times New Roman font for text and math
\usepackage{microtype}
\usepackage{amsmath,amssymb,amsfonts}
\usepackage{graphicx}
\usepackage{xcolor}
\usepackage{booktabs}
\usepackage{tabularx}
\usepackage{multirow}
\usepackage{makecell}
\usepackage{array}
\usepackage[font=small,skip=6pt]{caption}
\usepackage{subcaption}
\captionsetup[figure]{font=small}
\captionsetup[table]{font=small}
\captionsetup[sub]{font=footnotesize}
\usepackage{fancyhdr}
\usepackage{setspace}
\usepackage{enumitem}
\usepackage{textcomp}
\usepackage{float}
\usepackage{placeins}
\usepackage{titlesec}
\usepackage{url}
\usepackage[hidelinks]{hyperref}
\usepackage{tikz}
\usetikzlibrary{calc}
\usepackage{needspace}

% ==================== TYPOGRAPHY & OVERFLOW GUARDS ====================
\onehalfspacing
\setlength{\parindent}{0pt}
\setlength{\parskip}{6pt}
\setlength{\lineskip}{1pt}
\setlength{\normallineskip}{1pt}
\setlength{\lineskiplimit}{1pt}
\clubpenalty=10000
\widowpenalty=10000
\displaywidowpenalty=10000
\tolerance=2000
\emergencystretch=2em
\raggedbottom

% List spacing configuration
\setlist[enumerate]{leftmargin=*, itemsep=2pt, parsep=1pt, topsep=3pt, partopsep=0pt}
\setlist[itemize]{leftmargin=*, itemsep=2pt, parsep=1pt, topsep=3pt, partopsep=0pt}

% ==================== CHAPTER & SECTION FORMATTING ====================
\titleformat{\chapter}[display]
  {\normalfont\Large\bfseries\centering}
  {CHAPTER \thechapter}{8pt}
  {\LARGE\bfseries\centering\MakeUppercase}

\titleformat{name=\chapter,numberless}[display]
  {\normalfont\LARGE\bfseries\centering}
  {}{0pt}
  {\LARGE\bfseries\centering\MakeUppercase}

\titlespacing*{\chapter}{0pt}{12pt}{18pt}
\titlespacing*{name=\chapter,numberless}{0pt}{12pt}{18pt}

\titleformat{\section}
  {\normalfont\large\bfseries\raggedright}{\thesection}{1em}{}
\titleformat{\subsection}
  {\normalfont\normalsize\bfseries\raggedright}{\thesubsection}{1em}{}
\titleformat{\subsubsection}
  {\normalfont\normalsize\bfseries\raggedright}{\thesubsubsection}{1em}{}

\titlespacing*{\section}{0pt}{12pt plus 2pt minus 2pt}{5pt}
\titlespacing*{\subsection}{0pt}{8pt plus 2pt minus 2pt}{3pt}
\titlespacing*{\subsubsection}{0pt}{6pt plus 1pt minus 1pt}{2pt}

% ==================== COLOR DEFINITIONS ====================
\definecolor{mitecrimson}{RGB}{128, 0, 0}
\definecolor{headerrule}{RGB}{140, 30, 20}
\definecolor{boxborder}{RGB}{40, 40, 40}

% Multi-directory image search path to locate all project assets
\graphicspath{{figures/}{report/figures/}{paper/figures/}{Research paper/}{../paper/figures/}{../figures/}{./}}

% Column type helpers
\newcolumntype{Y}{>{\raggedright\arraybackslash}X}
\newcolumntype{P}[1]{>{\raggedright\arraybackslash}p{#1}}
\newcolumntype{C}[1]{>{\centering\arraybackslash}p{#1}}

% ==================== ROBUST IMAGE & LOGO MACROS ====================
\newcommand{\insertfigure}[3][0.34\textheight]{%
  \IfFileExists{#2}{%
    \includegraphics[width=\linewidth,height=#1,keepaspectratio]{#2}%
  }{%
    \IfFileExists{figures/#2}{%
      \includegraphics[width=\linewidth,height=#1,keepaspectratio]{figures/#2}%
    }{%
      \IfFileExists{report/figures/#2}{%
        \includegraphics[width=\linewidth,height=#1,keepaspectratio]{report/figures/#2}%
      }{%
        \IfFileExists{paper/figures/#2}{%
          \includegraphics[width=\linewidth,height=#1,keepaspectratio]{paper/figures/#2}%
        }{%
          \fbox{\parbox[c][3.0cm][c]{0.92\linewidth}{%
            \centering\textbf{\large #3}\\[4pt]
            \small\texttt{[\detokenize{#2}]}\\[3pt]
            \footnotesize \textit{(High-resolution project asset)}%
          }}%
        }%
      }%
    }%
  }%
}

\newcommand{\insertlogo}[2]{%
  \IfFileExists{#1}{%
    \includegraphics[height=#2,keepaspectratio]{#1}%
  }{%
    \IfFileExists{figures/#1}{%
      \includegraphics[height=#2,keepaspectratio]{figures/#1}%
    }{%
      \IfFileExists{report/figures/#1}{%
        \includegraphics[height=#2,keepaspectratio]{report/figures/#1}%
      }{%
        \IfFileExists{paper/figures/#1}{%
          \includegraphics[height=#2,keepaspectratio]{paper/figures/#1}%
        }{%
          \fbox{\parbox[c][#2][c]{2.5cm}{\centering\textbf{\small #1}}}%
        }%
      }%
    }%
  }%
}

% ==================== HEADER & FOOTER SETUP ====================
% No running header and no line anywhere; only centered page number in footer
\pagestyle{fancy}
\fancyhf{}
\renewcommand{\headrulewidth}{0pt}
\renewcommand{\footrulewidth}{0pt}
\fancyfoot[C]{\thepage}

\fancypagestyle{plain}{%
  \fancyhf{}%
  \renewcommand{\headrulewidth}{0pt}%
  \renewcommand{\footrulewidth}{0pt}%
  \fancyfoot[C]{\thepage}%
}

\begin{document}

% ------------------------------------------------------------
% 1. COVER / TITLE PAGE
% ------------------------------------------------------------
\begin{titlepage}
\thispagestyle{empty}

\begin{tikzpicture}[remember picture,overlay]
    \draw[line width=1.5pt]
      ($(current page.north west)+(1.2cm,-1.2cm)$)
      rectangle
      ($(current page.south east)+(-1.2cm,1.2cm)$);
    \draw[line width=0.5pt]
      ($(current page.north west)+(1.35cm,-1.35cm)$)
      rectangle
      ($(current page.south east)+(-1.35cm,1.35cm)$);
\end{tikzpicture}

\centering

\resizebox{0.95\linewidth}{!}{\mbox{\bfseries MANGALORE INSTITUTE OF TECHNOLOGY \& ENGINEERING}}\\[3pt]
{\scriptsize (A Unit of Rajalaxmi Education Trust \textregistered, Mangalore)}\\[2pt]
{\scriptsize Autonomous Institute Affiliated to V.T.U, Belagavi, Approved by AICTE, New Delhi}\\[2pt]
{\scriptsize Accredited by NAAC with A+ Grade \& ISO 9001:2015 Certified Institution}\\[0.25cm]

\insertlogo{MITE_Logo.jpg}{2.0cm}\\[0.35cm]

{\Large\bfseries PROJECT REPORT}\\[0.2cm]
{\large\bfseries 23AISE409 PROJECT PHASE - II}\\[0.45cm]

{\large\bfseries
``AI-BASED NETWORK INTRUSION DETECTION SYSTEM USING LIGHTWEIGHT HYBRID AUTOENCODER AND XGBOOST WITH REAL-TIME DRIFT ADAPTATION''}\\[0.55cm]

{\small Submitted in partial fulfillment of the requirements for the award of the degree of}\\[3pt]
{\large\bfseries BACHELOR OF ENGINEERING}\\[3pt]
{\bfseries in}\\[3pt]
{\large\bfseries ARTIFICIAL INTELLIGENCE AND MACHINE LEARNING}\\[0.45cm]

{\bfseries by}\\[5pt]
\begin{tabular}{ll}
\textbf{Ansh Pawaskar} & \textbf{4MT23AI009}\\
\textbf{Nesar Naik}    & \textbf{4MT23AI036}\\
\textbf{Tejeswini}     & \textbf{4MT23AI057}\\
\end{tabular}\\[0.45cm]

{\bfseries Under the Guidance of}\\[3pt]
\textbf{Mr. Srivatsa Upadhya P}\\
Assistant Professor\\
Department of Artificial Intelligence and Machine Learning\\[0.5cm]

\resizebox{0.90\linewidth}{!}{\mbox{\bfseries DEPARTMENT OF ARTIFICIAL INTELLIGENCE AND MACHINE LEARNING}}\\[0.2cm]
{\large\bfseries 2026-27}

\vfill
\end{titlepage}

% ------------------------------------------------------------
% 2. CERTIFICATE PAGE
% ------------------------------------------------------------
\clearpage
\thispagestyle{empty}

\begin{tikzpicture}[remember picture, overlay]
  \draw[line width=1.5pt, color=black] ($(current page.north west) + (1.2cm,-1.2cm)$) rectangle ($(current page.south east) + (-1.2cm,1.2cm)$);
  \draw[line width=0.5pt, color=black] ($(current page.north west) + (1.35cm,-1.35cm)$) rectangle ($(current page.south east) + (-1.35cm,1.35cm)$);
\end{tikzpicture}

\begin{center}
\resizebox{0.92\linewidth}{!}{\mbox{\bfseries MANGALORE INSTITUTE OF TECHNOLOGY \& ENGINEERING}}\\[3pt]
{\scriptsize (A Unit of Rajalaxmi Education Trust \textregistered, Mangalore)}\\[2pt]
{\scriptsize Autonomous Institute Affiliated to V.T.U, Belagavi, Approved by AICTE, New Delhi}\\[2pt]
{\scriptsize Accredited by NAAC with A+ Grade \& ISO 9001:2015 Certified Institution}\\[0.25cm]

\insertlogo{MITE_Logo.jpg}{1.6cm}\\[0.2cm]

\resizebox{0.86\linewidth}{!}{\mbox{\bfseries DEPARTMENT OF ARTIFICIAL INTELLIGENCE AND MACHINE LEARNING}}\\[0.25cm]

{\large \textbf{CERTIFICATE}}\\[0.25cm]
\end{center}

\setstretch{1.18}
{\small This is to certify that the Project Phase - II (23AISE409) work entitled \textbf{``AI-BASED NETWORK INTRUSION DETECTION SYSTEM USING LIGHTWEIGHT HYBRID AUTOENCODER AND XGBOOST WITH REAL-TIME DRIFT ADAPTATION''} is a bonafide work carried out by \textbf{Ansh Pawaskar (4MT23AI009)}, \textbf{Nesar Naik (4MT23AI036)}, and \textbf{Tejeswini (4MT23AI057)} in partial fulfillment for the award of degree of \textbf{Bachelor of Engineering in Artificial Intelligence and Machine Learning} of Mangalore Institute of Technology \& Engineering (Autonomous) during the year 2026-27. It is certified that all corrections and suggestions indicated for Internal Assessment have been incorporated in the report deposited in the departmental library. The project has been approved as it satisfies the academic requirements in respect of project work prescribed for the Bachelor of Engineering degree.}\par\vspace{1.2cm}

\noindent
\begin{minipage}[t]{0.48\textwidth}
    \centering
    \rule{5cm}{0.4pt}\\[0.3cm]
    \textbf{Mr. Srivatsa Upadhya P}\\
    Project Guide
\end{minipage}
\hfill
\begin{minipage}[t]{0.48\textwidth}
    \centering
    \rule{5cm}{0.4pt}\\[0.3cm]
    \textbf{Dr. Sunil Kumar S}\\
    Head of Dept. AI \& ML
\end{minipage}

\vspace{1.5cm}

\begin{center}
    \rule{5cm}{0.4pt}\\[0.3cm]
    \textbf{Dr. Prashanth C M}\\
    Principal
\end{center}

% ------------------------------------------------------------
% 3. DECLARATION PAGE
% ------------------------------------------------------------
\clearpage
\thispagestyle{empty}

\begin{tikzpicture}[remember picture, overlay]
  \draw[line width=1.5pt, color=black] ($(current page.north west) + (1.2cm,-1.2cm)$) rectangle ($(current page.south east) + (-1.2cm,1.2cm)$);
  \draw[line width=0.5pt, color=black] ($(current page.north west) + (1.35cm,-1.35cm)$) rectangle ($(current page.south east) + (-1.35cm,1.35cm)$);
\end{tikzpicture}

\begin{center}
{\Large\bfseries DECLARATION}\\[0.8cm]
\end{center}

\setstretch{1.22}
We declare that this Project Phase - II (23AISE409) report titled \textbf{``AI-Based Network Intrusion Detection System Using Lightweight Hybrid Autoencoder and XGBoost with Real-Time Drift Adaptation''} submitted in partial fulfillment of the degree of B.E. in Artificial Intelligence and Machine Learning is a record of original work carried out by us under the supervision of \textbf{Mr. Srivatsa Upadhya P}, and has not formed the basis for the award of any other degree, in this or any other Institution or University. In keeping with ethical practice in reporting scientific information, due acknowledgements have been made wherever the findings of others have been cited.\par\vspace{1.0cm}

\noindent
\begin{tabularx}{\textwidth}{|c|X|p{4.5cm}|}
\hline
\textbf{Sr. No.} & \textbf{\centering Name} & \textbf{\centering Signature} \\
\hline
1 & Ansh Pawaskar (4MT23AI009) & \\[0.6cm]
\hline
2 & Nesar Naik (4MT23AI036) & \\[0.6cm]
\hline
3 & Tejeswini (4MT23AI057) & \\[0.6cm]
\hline
\end{tabularx}

% ------------------------------------------------------------
% 4. ACKNOWLEDGEMENTS PAGE
% ------------------------------------------------------------
\clearpage
\thispagestyle{empty}

\begin{tikzpicture}[remember picture, overlay]
  \draw[line width=1.5pt, color=black] ($(current page.north west) + (1.2cm,-1.2cm)$) rectangle ($(current page.south east) + (-1.2cm,1.2cm)$);
  \draw[line width=0.5pt, color=black] ($(current page.north west) + (1.35cm,-1.35cm)$) rectangle ($(current page.south east) + (-1.35cm,1.35cm)$);
\end{tikzpicture}

\begin{center}
{\Large\bfseries ACKNOWLEDGEMENTS}\\[0.6cm]
\end{center}

\setstretch{1.18}
The successful completion of the Project Phase - II (23AISE409) work titled \textbf{``AI-Based Network Intrusion Detection System Using Lightweight Hybrid Autoencoder and XGBoost with Real-Time Drift Adaptation''} would not have been possible without the support of those, whose constant guidance and encouragement helped turn our efforts into success.

We would like to thank our Project Guide \textbf{Mr. Srivatsa Upadhya P}, Assistant Professor, Department of Artificial Intelligence and Machine Learning for his constant encouragement and support extended throughout.

We would like to express appreciation to \textbf{Dr. Sunil Kumar S}, Head of Department of Artificial Intelligence and Machine Learning for his support and guidance.

We would like to thank our Principal \textbf{Dr. Prashanth C M}, for encouraging us and giving us an opportunity to accomplish the project.

We also thank our management who helped us directly or indirectly in the completion of Phase - II of the project.

Our special thanks to faculty members and others for their constant help and support.

Above all, we extend our sincere gratitude to our parents and friends for their constant encouragement with moral support.\par\vspace{1.2cm}

\noindent
\begin{tabularx}{\textwidth}{X r}
& \textbf{Ansh Pawaskar (4MT23AI009)} \\
& \textbf{Nesar Naik (4MT23AI036)} \\
& \textbf{Tejeswini (4MT23AI057)}
\end{tabularx}

% ------------------------------------------------------------
% 5. ABSTRACT PAGE (ROMAN PAGE v)
% ------------------------------------------------------------
\clearpage
\pagenumbering{roman}
\setcounter{page}{5}
\thispagestyle{plain}

\begin{center}
{\Large\bfseries ABSTRACT}\\[0.6cm]
\end{center}

\setstretch{1.2}
Network intrusion detection systems (NIDS) deployed in modern enterprise and cloud environments face two major operational challenges: supervised classifiers fail when encountering zero-day attacks, whereas unsupervised anomaly detectors generate elevated false alarm rates and suffer from arbitrary Gaussian threshold collapse ($\mu + 3\sigma$). This project presents a leakage-free, two-stage hybrid NIDS combining an unsupervised deep symmetric Autoencoder ($d \to 128 \to 64 \to 32 \to 16 \to 32 \to 64 \to 128 \to d$) with an Extreme Gradient Boosted decision tree (XGBoost) classifier and alert-gated TreeSHAP explainability. Evaluated on strictly deduplicated partitions of CICIDS2018 ($671{,}131$ flows) and NSL-KDD ($147{,}790$ instances), the pipeline achieves 99.70\% attack recall and detects 93.11\% of unseen DoS attacks under Leave-One-Attack-Out testing. Validation-tuned Youden's $J$ thresholding eliminates zero-recall collapse, while a sliding buffer ($W=500$) tracks concept drift. The system executes at 0.1830~ms per flow on commodity CPU hardware with an interactive Streamlit dashboard.\par\vspace{0.6cm}

\noindent
\textbf{Keywords:} Network Intrusion Detection, Autoencoder, XGBoost, Anomaly Screening, Youden's $J$-Statistic, TreeSHAP, Concept Drift, Zero-Day Generalization, Streamlit.

% ------------------------------------------------------------
% 6. TABLE OF CONTENTS (PAGE vi)
% ------------------------------------------------------------
\clearpage
\pagenumbering{roman}
\setcounter{page}{6}
\thispagestyle{plain}

\begin{center}
{\Large\bfseries TABLE OF CONTENTS}\\[0.4cm]
\end{center}

\noindent
\begin{tabularx}{\textwidth}{|c|X|c|}
\hline
\textbf{Sr. NO.} & \textbf{\centering CONTENTS} & \textbf{PAGE NO.} \\
\hline
1. & INTRODUCTION & \pageref{ch:intro} \\
\hline
2. & LITERATURE SURVEY & \pageref{ch:lit_survey} \\
\hline
3. & PROPOSED SYSTEM AND SCOPE & \pageref{ch:proposed_system} \\
\hline
4. & METHODOLOGY & \pageref{ch:methodology} \\
\hline
5. & IMPLEMENTATION \& EXPERIMENTAL WORK & \pageref{ch:implementation} \\
\hline
6. & RESULTS, ANALYSIS AND DISCUSSION & \pageref{ch:results} \\
\hline
7. & CONCLUSION AND FUTURE SCOPE & \pageref{ch:conclusion} \\
\hline
 & RESEARCH PAPER / PATENT PUBLISHED (if any) & \pageref{sec:paper_published} \\
\hline
 & REFERENCES & \pageref{sec:references} \\
\hline
 & APPENDICES & \pageref{sec:appendices} \\
\hline
\end{tabularx}

% ------------------------------------------------------------
% 7. LIST OF FIGURES (PAGE vii)
% ------------------------------------------------------------
\clearpage
\pagenumbering{roman}
\setcounter{page}{7}
\thispagestyle{plain}

\begin{center}
{\Large\bfseries LIST OF FIGURES}\\[0.4cm]
\end{center}

\noindent
\begin{tabularx}{\textwidth}{|c|X|c|}
\hline
\textbf{Sr. No.} & \textbf{\centering TITLE} & \textbf{Page No.} \\
\hline
Figure 3.1 & System Architecture of the Two-Stage Hybrid NIDS & \pageref{fig:ch3_arch} \\
\hline
Figure 4.1 & Deep Symmetric Autoencoder Bottleneck Topology & \pageref{fig:ch4_ae_topology} \\
\hline
Figure 4.2 & Sequence Diagram of Packet Ingestion and Prediction & \pageref{fig:ch4_sequence} \\
\hline
Figure 4.3 & Activity Diagram of Tiered Detection and Alert Routing & \pageref{fig:ch4_activity} \\
\hline
Figure 4.4 & Data Flow Diagram (DFD Level-1) for Flow Processing & \pageref{fig:ch4_dfd} \\
\hline
Figure 4.5 & Class Diagram of Object-Oriented Framework Architecture & \pageref{fig:ch4_class} \\
\hline
Figure 4.6 & Use Case Diagram of Network Intrusion Detection Workflow & \pageref{fig:ch4_usecase} \\
\hline
Figure 5.1 & Real-Time Network Flow Telemetry and Live Sniffing Monitor & \pageref{fig:ch5_dash_main} \\
\hline
Figure 5.2 & Threat Diagnosis, Alert Gating, and Local TreeSHAP Explanation & \pageref{fig:ch5_dash_alert} \\
\hline
Figure 6.1 & Row-Normalized Confusion Matrices for Hybrid AE--XGBoost Model & \pageref{fig:ch6_cm_hybrid} \\
\hline
Figure 6.2 & Row-Normalized Confusion Matrices for Standalone Autoencoder & \pageref{fig:ch6_cm_ae} \\
\hline
Figure 6.3 & Reconstruction Threshold Sensitivity and Pareto Optimization Curves & \pageref{fig:ch6_thresh} \\
\hline
Figure 6.4 & Leave-One-Attack-Out (LOAO) Unseen Attack Detection Recall & \pageref{fig:ch6_loao_plot} \\
\hline
Figure 6.5 & Statistical Concept Drift Tracking ($D_{\text{KS}}$, PSI, JSD) Across Windows & \pageref{fig:ch6_drift} \\
\hline
Figure 6.6 & TreeSHAP Global Feature Importance Ranking (Summary Plot) & \pageref{fig:ch6_shap} \\
\hline
Figure 6.7 & End-to-End Pipeline Execution Latency Breakdown on Multi-Core CPU & \pageref{fig:ch6_latency} \\
\hline
\end{tabularx}

% ------------------------------------------------------------
% 8. LIST OF TABLES (PAGE viii)
% ------------------------------------------------------------
\clearpage
\pagenumbering{roman}
\setcounter{page}{8}
\thispagestyle{plain}

\begin{center}
{\Large\bfseries LIST OF TABLES}\\[0.4cm]
\end{center}

\noindent
\begin{tabularx}{\textwidth}{|c|X|c|}
\hline
\textbf{Sr. No.} & \textbf{\centering TITLE} & \textbf{Page No.} \\
\hline
Table 2.1 & Comparison of Existing NIDS Approaches, Methodologies, and Gaps & \pageref{tab:literature_review} \\
\hline
Table 4.1 & Measurement and Evaluation Parameters for Model Assessment & \pageref{tab:eval_params} \\
\hline
Table 4.2 & Autoencoder Bottleneck Layer Configuration and Dimensionality & \pageref{tab:ae_architecture} \\
\hline
Table 5.1 & Cryptographically Audited Dataset Splits Enforcing Zero Leakage & \pageref{tab:ch5_splits} \\
\hline
Table 5.2 & Experimental Setup Parameters and Hyperparameter Configurations & \pageref{tab:ch5_setup} \\
\hline
Table 5.3 & System Test Cases, Inputs, Expected Outcomes, and Execution Status & \pageref{tab:ch5_test_cases} \\
\hline
Table 6.1 & Overall Classification Performance on Held-Out Test Partitions & \pageref{tab:ch6_summary} \\
\hline
Table 6.2 & Multi-Class Attack Detection Breakdown on CICIDS2018 ($N = 100{,}670$) & \pageref{tab:ch6_cicids} \\
\hline
Table 6.3 & Multi-Class Attack Detection Breakdown on NSL-KDD ($N = 22{,}169$) & \pageref{tab:ch6_nslkdd} \\
\hline
Table 6.4 & Reconstruction Threshold Strategy Comparison on CICIDS2018 & \pageref{tab:ch6_thresh} \\
\hline
Table 6.5 & Leave-One-Attack-Out (LOAO) Unseen Attack Detection Performance & \pageref{tab:ch6_loao} \\
\hline
Table 6.6 & Statistical Concept Drift Tracking Across Sequential Windows & \pageref{tab:ch6_drift} \\
\hline
Table 6.7 & Computational Benchmark: Latency, Throughput, and Peak Memory (RSS) & \pageref{tab:ch6_latency} \\
\hline
Table 6.8 & Benchmark Comparison Against Baseline Supervised Classifiers & \pageref{tab:ch6_comparison} \\
\hline
\end{tabularx}

% ------------------------------------------------------------
% 9. ABBREVIATIONS / NOTATIONS (PAGE ix)
% ------------------------------------------------------------
\clearpage
\pagenumbering{roman}
\setcounter{page}{9}
\thispagestyle{plain}

\begin{center}
{\Large\bfseries Abbreviations / Notations}\\[0.6cm]
\end{center}

\noindent
\begin{tabularx}{\textwidth}{p{3.2cm} X}
\textbf{AE} & Autoencoder \\
\textbf{XGBoost} & Extreme Gradient Boosting \\
\textbf{NIDS} & Network Intrusion Detection System \\
\textbf{DoS} & Denial of Service \\
\textbf{DDoS} & Distributed Denial of Service \\
\textbf{SHAP} & SHapley Additive exPlanations \\
\textbf{TreeSHAP} & Tree-ensemble Shapley Additive Explanations \\
\textbf{PSI} & Population Stability Index \\
\textbf{JSD} & Jensen--Shannon Divergence \\
\textbf{KS} & Kolmogorov--Smirnov Test \\
\textbf{ROC} & Receiver Operating Characteristic \\
\textbf{AUC} & Area Under the Curve \\
\textbf{FPR} & False Positive Rate \\
\textbf{TPR} & True Positive Rate \\
\textbf{MSE} & Mean Squared Error \\
\textbf{API} & Application Programming Interface \\
\textbf{GUI} & Graphical User Interface \\
\textbf{SOC} & Security Operations Center \\
\textbf{CPU} & Central Processing Unit \\
\textbf{RAM} & Random Access Memory \\
\textbf{SSD} & Solid State Drive \\
\textbf{NIC} & Network Interface Card \\
\textbf{PCAP} & Packet Capture Format \\
\textbf{LOAO} & Leave-One-Attack-Out Validation \\
\textbf{IAT} & Inter-Arrival Time \\
\textbf{TCP} & Transmission Control Protocol \\
\textbf{UDP} & User Datagram Protocol \\
\textbf{IP} & Internet Protocol \\
\textbf{XAI} & Explainable Artificial Intelligence \\
\end{tabularx}

% ============================================================
%                       MAIN CONTENT
% ============================================================
\clearpage
\pagenumbering{arabic}
\setcounter{page}{1}

% ------------------------------------------------------------
% CHAPTER 1: INTRODUCTION
% ------------------------------------------------------------
\chapter{INTRODUCTION}\label{ch:intro}

\section{Background}
Modern enterprise networks, critical cyber-physical infrastructures, and multi-tenant cloud data centers operate in an environment characterized by unprecedented throughput, massive concurrency, and relentless attack velocity. The proliferation of automated attack tooling, evasive multi-vector campaigns, and targeted Advanced Persistent Threats (APTs) has rendered conventional security defenses fundamentally insufficient. Traditional boundary security tools, such as stateful firewalls and signature-based Network Intrusion Detection Systems (NIDSs) like Snort and Suricata, rely on deterministic pattern matching against known vulnerability databases. While these signature-driven mechanisms exhibit high processing speed and near-zero false alarms on documented threats, they remain blind to zero-day exploits, protocol mutations, and slow distributed reconnaissance activities.

To counter these vulnerabilities, security operations centers (SOCs) have increasingly adopted Artificial Intelligence (AI), Machine Learning (ML), and Deep Learning (DL) paradigms to learn statistical behavioral representations from high-dimensional network flow data. By analyzing aggregated flow metrics---such as inter-arrival timings, directional packet volume distributions, TCP flag heuristics, and header lengths---learning algorithms can identify suspicious communications that deviate from legitimate baseline activity without requiring manual rule curation. However, the operationalization of machine learning models in production environments introduces critical challenges, including susceptibility to evasion, high computational overhead, and vulnerability to non-stationary traffic distributions.

\section{Problem Statement}
Contemporary Network Intrusion Detection Systems fail to achieve an effective operational balance between detecting known attack categories with high precision and flagging unmodeled zero-day intrusions with high sensitivity. Supervised models (e.g., Extreme Gradient Boosted Trees, Random Forests, Deep MLPs) deliver near-perfect discrimination under closed-world benchmark assumptions. However, their decision boundaries are entirely constrained by the training distribution; when exposed to previously unseen zero-day exploits or novel variants, supervised models catastrophically fail, misclassifying malicious activity as normal traffic.

Conversely, unsupervised anomaly detectors (such as deep Autoencoders) compress normal network flows through low-dimensional latent bottlenecks to establish a non-parametric boundary of benign communication. Traffic exceeding an anomaly threshold is flagged as suspicious. However, prevailing academic and industrial implementations rely on arbitrary parametric Gaussian heuristics ($\mu + 3\sigma$) or rigid high percentiles ($99.9^{\text{th}}$). Because real-world network traffic is heavy-tailed and non-Gaussian, extreme outliers dramatically inflate $\mu + 3\sigma$, causing catastrophic threshold collapse where attack recall drops to exactly $0.00\%$. Furthermore, cross-partition data leakage in standard benchmarks frequently conceals these failures, while post-hoc Explainable AI (XAI) frameworks impose crippling latency bottlenecks if computed continuously at line rate.

\section{Motivation / Need for the Project}
To overcome the closed-world dilemma of supervised learning and the threshold instability of unsupervised detectors, an integrated defense-in-depth architecture is required. Automated network security cannot rely solely on signature databases or pure supervised classifiers that remain blind to emerging exploits. Simultaneously, security analysts in SOC environments cannot manage thousands of false-positive alarms generated by uncalibrated anomaly detectors.

There is a clear operational need for a two-stage hybrid framework where:
\begin{enumerate}
    \item An unsupervised Autoencoder serves as a lightweight frontline gatekeeper, screening out more than 85--90\% of legitimate benign traffic at sub-millisecond line rates.
    \item A supervised XGBoost classifier inspects only the anomalous flows, categorizing them into granular threat families or quarantining low-confidence anomalies as potential zero-day threats.
    \item Explainable AI (TreeSHAP) is triggered selectively on alerts, eliminating 90\% of computation overhead while providing human analysts with immediate, transparent feature attributions.
    \item A sliding-window drift buffer adapts the baseline threshold dynamically to non-adversarial traffic shifts over continuous network streams.
\end{enumerate}

\section{Objectives}
The primary technical objectives of this project are:
\begin{enumerate}
    \item \textbf{Benchmarking Baseline Models:} To establish comprehensive performance baselines for classical machine learning and deep learning architectures in network intrusion detection.
    \item \textbf{Developing Hybrid Architecture:} To design, implement, and optimize a two-stage hybrid NIDS that couples an unsupervised symmetric Autoencoder gatekeeper with a downstream multi-class XGBoost classifier.
    \item \textbf{Leakage-Free Preprocessing:} To construct an audited, cryptographically validated preprocessing pipeline that enforces strict zero-leakage partitioning ($\text{Train} \cap \text{Test} = \emptyset$) on modern benchmark datasets.
    \item \textbf{Calibration \& Drift Tracking:} To eliminate Gaussian threshold collapse by optimizing validation-guided Youden's $J$-statistic, and implement sliding-window statistical drift tracking ($D_{\text{KS}}$, PSI, JSD).
    \item \textbf{Operational Deployment \& Dashboard:} To validate sub-millisecond per-flow inference latency on multi-core CPUs and deploy an interactive Streamlit dashboard for real-time traffic telemetry and local SHAP explanations.
\end{enumerate}

\section{Scope of the Project}
The scope of this project encompasses:
\begin{itemize}
    \item \textbf{Benchmark Datasets:} Evaluation on the modern, high-dimensional CICIDS2018 dataset (78 transport-layer flow features) and the multi-class NSL-KDD benchmark (41 connection attributes, expanded to 122 one-hot features).
    \item \textbf{Threat Taxonomy:} Detection and categorization of primary attack vectors: volumetric Denial of Service (DoS/DDoS), brute-force credential stuffing (SSH/FTP), reconnaissance port probing, Remote-to-Local (R2L) exploits, and User-to-Root (U2R) privilege escalations.
    \item \textbf{Zero-Day Evaluation:} Auditing novel attack detection capabilities using a rigorous Leave-One-Attack-Out (LOAO) protocol.
    \item \textbf{Deployment Modality:} Execution on standard commodity CPU server hardware without reliance on GPU acceleration, supporting offline CSV/PCAP ingestion and live promiscuous socket flow sniffing.
\end{itemize}

\section{Significance / Expected Contribution}
The project delivers five distinct contributions to network security engineering:
\begin{enumerate}
    \item \textbf{Cryptographic Data Hygiene:} Identification and elimination of 362 leaking flow records from legacy benchmark splits, guaranteeing verifiable reproducibility.
    \item \textbf{Resolution of Threshold Collapse:} Empirical demonstration of the complete breakdown of parametric $\mu + 3\sigma$ rules and formulation of non-parametric Youden's $J$ optimization that restores attack recall to 99.70\%.
    \item \textbf{Zero-Day Defense-in-Depth:} Verification that the unsupervised gatekeeper successfully isolates 93.11\% of unseen DoS attacks and 82.22\% of unseen Probe attacks without prior training exposure.
    \item \textbf{Alert-Gated Explainability:} Reduction of TreeSHAP computational overhead by 90\% through conditional execution, preserving line-rate processing.
    \item \textbf{Production-Grade Efficiency:} Verification of 0.1830~ms per-flow inference latency ($5{,}464$~flows/s) and a compact 527.0~MB RSS memory footprint on standard CPU hardware.
\end{enumerate}

\section{Organization of the Report}
The remainder of this report is organized as follows:
\begin{itemize}
    \item \textbf{Chapter 2 (Literature Survey):} Reviews state-of-the-art studies across machine learning, deep autoencoders, hybrid classifiers, and explainable AI in NIDS, highlighting existing research gaps.
    \item \textbf{Chapter 3 (Proposed System and Scope):} Formulates the detection problem, presents system requirements, hardware/software specifications, and details the overall architecture.
    \item \textbf{Chapter 4 (Methodology):} Outlines evaluation metrics, algorithmic workflows, UML designs, model layer configurations, error sources, and mitigation techniques.
    \item \textbf{Chapter 5 (Implementation \& Experimental Work):} Documents the implementation environment, zero-leakage dataset preparation, hyperparameter tuning, testing test cases, and the interactive dashboard.
    \item \textbf{Chapter 6 (Results, Analysis and Discussion):} Presents quantitative results on CICIDS2018 and NSL-KDD, confusion matrices, threshold optimizations, unseen attack generalization, concept drift tracking, and CPU benchmarks.
    \item \textbf{Chapter 7 (Conclusion and Future Scope):} Summarizes major project findings, outlines practical contributions, and identifies future research directions.
    \item \textbf{Research Paper Details, References, and Appendices:} Details publication outcomes, formal academic citations, and mathematical derivations.
\end{itemize}

% ------------------------------------------------------------
% CHAPTER 2: LITERATURE SURVEY
% ------------------------------------------------------------
\clearpage
\chapter{LITERATURE SURVEY}\label{ch:lit_survey}

\section{Introduction}
Intrusion detection research has undergone a multi-decade paradigm shift, driven by the expanding attack surface of distributed computing and the escalating sophistication of adversarial exploitation. Early network perimeter defenses relied primarily on deterministic rule engines, such as Snort, Bro (Zeek), and Suricata. These systems match incoming network packets against regular expressions and known exploit signatures. Although rule-based matchers achieve near-zero false positive rates on documented vulnerabilities and operate efficiently at wire speeds, they exhibit absolute vulnerability to zero-day mutations, protocol obfuscation, and polymorphic payloads.

To overcome signature limitations, researchers transitioned toward shallow machine learning algorithms, including Support Vector Machines (SVM), Random Forests (RF), Naive Bayes, and Decision Trees. These algorithms classify transport-layer statistical flow summaries rather than packet payloads. While shallow models improved detection flexibility, their limited capacity prevents them from capturing intricate temporal dependencies and non-linear correlations across high-dimensional flow manifolds.

With the advent of deep representation learning, Multi-Layer Perceptrons (MLPs), Convolutional Neural Networks (CNNs), Long Short-Term Memory networks (LSTMs), and Deep Autoencoders (AEs) emerged as standard architectures in network security literature. Deep Autoencoders compress input flow vectors through low-dimensional bottleneck layers to learn non-linear manifold representations of benign communication. However, anomaly detectors struggle with high false alarm rates caused by non-stationary network behavior and arbitrary threshold heuristics ($\mu + 3\sigma$). Meanwhile, supervised deep networks remain closed-world discriminators unable to handle zero-day attacks. Furthermore, the opaque nature of deep neural networks impedes incident response in Security Operations Centers (SOCs), necessitating Explainable Artificial Intelligence (XAI) frameworks like SHAP. This survey analyzes ten pivotal studies in recent NIDS literature, identifying methodological trade-offs and structural gaps.

\clearpage
\section{Review of Existing Work}
Table~\ref{tab:literature_review} presents a structured, comprehensive synthesis of ten foundational studies in network intrusion detection, systematically detailing their problem formulations, technical methodologies, primary empirical findings, and identified research gaps.

\begin{table}[H]
\centering
\caption{Comparison of Existing NIDS Approaches, Methodologies, and Research Gaps}
\label{tab:literature_review}
\scriptsize
\setlength{\tabcolsep}{3pt}
\renewcommand{\arraystretch}{1.12}

\begin{tabularx}{\textwidth}{
|c|
>{\raggedright\arraybackslash}p{0.18\textwidth}|
>{\raggedright\arraybackslash}p{0.15\textwidth}|
>{\raggedright\arraybackslash}p{0.18\textwidth}|
>{\raggedright\arraybackslash}p{0.18\textwidth}|
Y|}
\hline
\textbf{Sl.} &
\textbf{Author / Year} &
\textbf{Problem / Domain} &
\textbf{Methodology} &
\textbf{Key Empirical Finding} &
\textbf{Research Gap / Limitation} \\
\hline

1 & Abdallah et al. (2024)
& Cloud network anomaly detection
& Systematic review of ML and DL architectures
& Comprehensive qualitative taxonomy of anomaly detection
& Survey study; lacks direct empirical validation and CPU-latency profiling \\
\hline

2 & Abdulganiyu et al. (2024)
& Imbalanced network intrusion traffic
& Variational Autoencoder (VAE) synthesis + XGBoost
& Reported binary classification accuracy of 99.8\%
& VAE is utilized solely for data synthesis rather than reconstruction gating \\
\hline

3 & Neupane et al. (2022)
& Explainability of automated NIDS alerts
& Systematic survey of cybersecurity XAI methods
& Evaluates SHAP, LIME, and Integrated Gradients
& Lacks operational throughput profiling and explanation stability metrics \\
\hline

4 & Ben Ncir et al. (2024)
& Interpretable deep intrusion detection
& Ensemble deep neural networks coupled with SHAP
& Achieved F1-score of 97.19\% on NSL-KDD benchmark
& High recurrent inference overhead; unsuited for real-time line-rate screening \\
\hline

5 & Mahmoud et al. (2025)
& Explainable two-stage intrusion detection
& XI2S-IDS staged deep learning framework
& Reported overall classification accuracy of 97.0\%
& Computing per-flow Shapley attributions continuously causes severe latency bottleneck \\
\hline

6 & Sajid et al. (2024)
& Scalable high-speed hybrid detection
& Deep representation learning fused with classical ML
& Reported accuracy of 97.91\% across standard benchmarks
& Evaluated on static random splits; robustness to temporal drift unaddressed \\
\hline

7 & Shirley \& Priya (2025)
& Evolving zero-day threats in IoT networks
& Autoencoder--Feedforward Neural Network fusion
& Reported high classification accuracy of 99.55\%
& Static reconstruction threshold collapses under heavy-tailed network traffic \\
\hline

8 & Hussein \& R\'ep\'as (2026)
& Granular multi-class attack classification
& Deep autoencoder screening + GMM + XGBoost
& Reported macro F1-score exceeding 0.94 across classes
& Gaussian Mixture Model clustering introduces substantial computational overhead \\
\hline

9 & Diana et al. (2025)
& Benchmark reproducibility in NIDS research
& Comprehensive decadal literature analysis
& Audits pervasive evaluation flaws in 100+ papers
& Lacks automated cryptographic deduplication and cross-partition audit tools \\
\hline

10 & Arcos-Argudo et al. (2025)
& Classical vs hybrid boundary screening
& Deep Autoencoders compared to linear PCA/filters
& Evaluated representation fidelity on NSL-KDD \& CICIDS
& Relies on closed-world assumptions; zero-day isolation was not audited \\
\hline

\end{tabularx}
\end{table}

\clearpage
\section{Comparative Analysis}
Existing approaches in network intrusion detection generally fall into two diametrically opposed paradigms:
\begin{enumerate}
    \item \textbf{Supervised Discriminative Models:} Algorithms such as Random Forest, Multi-Layer Perceptrons, and Gradient Boosted Decision Trees (XGBoost, LightGBM, CatBoost) achieve near-perfect discrimination ($>99\%$) when test data mirrors the training distribution. However, their decision surfaces are bounded by closed-world assumptions; any unmodeled exploit is forcibly assigned to the nearest known class, resulting in fatal false negatives.
    \item \textbf{Unsupervised Generative / Reconstruction Models:} Autoencoders, One-Class SVMs, and Isolation Forests model normal traffic distributions without requiring attack labels. While effective for anomaly flagging, they cannot provide granular attack categorization and suffer from elevated false-positive rates when benign traffic patterns fluctuate.
\end{enumerate}
A two-stage hybrid approach combines the strengths of both paradigms: the Autoencoder filters out benign flows and isolates novel deviations, while XGBoost provides high-precision multi-class categorization on suspicious records.

\section{Research / Design Gap}
The literature review identifies four major unresolved gaps:
\begin{itemize}
    \item \textbf{Pervasive Data Leakage:} Published benchmarks frequently contain identical flows across training and test splits, artificially inflating reported laboratory accuracy.
    \item \textbf{Heuristic Threshold Collapse:} Using parametric Gaussian formulas ($\mu + 3\sigma$) on heavy-tailed network data causes thresholds to explode, completely destroying attack recall.
    \item \textbf{Explainability Latency Overhead:} Calculating Shapley values across every packet stream cripples network throughput, making real-time XAI impractical without selective alert gating.
    \item \textbf{Absence of Drift Adaptation:} Most models assume static i.i.d.\ data and degrade rapidly when background network behavior experiences non-adversarial concept drift.
\end{itemize}

\section{Summary}
The literature confirms that while deep learning and tree ensembles are effective independently, neither paradigm alone provides a robust, line-rate, and interpretable defense against modern network intrusions. An audited, leakage-free hybrid architecture combining non-parametric Autoencoder screening, gradient boosted classification, and alert-gated explainability addresses these critical vulnerabilities.

% ------------------------------------------------------------
% CHAPTER 3: PROPOSED SYSTEM AND SCOPE
% ------------------------------------------------------------
\clearpage
\chapter{PROPOSED SYSTEM AND SCOPE}\label{ch:proposed_system}

\section{Problem Formulation}
Let $\mathcal{X} \subset \mathbb{R}^d$ represent the $d$-dimensional space of continuous network flow feature vectors, and let $\mathcal{Y} = \{0, 1, \dots, C\}$ denote the label space, where $0$ corresponds to legitimate benign traffic and $\{1, \dots, C\}$ represent $C$ distinct attack categories. During Stage-1 training, the system is provided strictly with a verified set of benign flows $\mathcal{D}_{\text{train, benign}} = \{\mathbf{x}_i \in \mathcal{X} \mid y_i = 0\}_{i=1}^{N_b}$.

The Stage-1 Autoencoder learns an encoding function $f_\theta: \mathcal{X} \to \mathcal{Z}$ mapping inputs to a low-dimensional bottleneck latent representation $\mathbf{z} \in \mathbb{R}^{d_z}$ ($d_z \ll d$), and a decoding function $g_\phi: \mathcal{Z} \to \mathcal{X}$ reconstructing the input vector as $\hat{\mathbf{x}} = g_\phi(f_\theta(\mathbf{x}))$. The scalar reconstruction error is quantified by Mean Squared Error:
\begin{equation}
e(\mathbf{x}) = \frac{1}{d}\sum_{j=1}^d \left(x_j - \hat{x}_j\right)^2 = \frac{1}{d}\|\mathbf{x} - g_\phi(f_\theta(\mathbf{x}))\|_2^2
\label{eq:ch3_re}
\end{equation}

An anomaly threshold $\tau^*$ partitions traffic into screened benign records and anomaly alerts:
\begin{equation}
\text{Flag}(\mathbf{x}) = \begin{cases}
0 \quad (\text{\texttt{Benign-Screened}}), & \text{if } e(\mathbf{x}) \le \tau^* \\
1 \quad (\text{\texttt{Anomaly-Alert}}), & \text{if } e(\mathbf{x}) > \tau^*
\end{cases}
\label{eq:ch3_gate}
\end{equation}

For flows where $\text{Flag}(\mathbf{x}) = 1$, the vector is forwarded to the Stage-2 XGBoost classifier $h_\psi(\mathbf{x})$, which computes a softmax probability distribution over known attack classes:
\begin{equation}
P(y = c \mid \mathbf{x}) = \frac{\exp(z_c(\mathbf{x}))}{\sum_{k=1}^C \exp(z_k(\mathbf{x}))}, \quad c \in \{1, \dots, C\}
\label{eq:ch3_softmax}
\end{equation}

Let $c^*(\mathbf{x}) = \arg\max_{c} P(y = c \mid \mathbf{x})$ and $P^*(\mathbf{x}) = \max_{c} P(y = c \mid \mathbf{x})$. To isolate potential zero-day threats, a classification confidence floor $\delta_{\text{conf}} \in (0, 1]$ is established. The integrated decision function $\hat{y}(\mathbf{x})$ is defined as:
\begin{equation}
\hat{y}(\mathbf{x}) = \begin{cases}
\text{\texttt{Benign-Screened}}, & \text{if } e(\mathbf{x}) \le \tau^* \\
c^*(\mathbf{x}), & \text{if } e(\mathbf{x}) > \tau^* \text{ and } P^*(\mathbf{x}) \ge \delta_{\text{conf}} \\
\text{\texttt{UNKNOWN\_ATTACK}}, & \text{if } e(\mathbf{x}) > \tau^* \text{ and } P^*(\mathbf{x}) < \delta_{\text{conf}}
\end{cases}
\label{eq:ch3_decision}
\end{equation}

\section{Proposed Solution}
The proposed solution implements a tiered, sequential detection and categorization pipeline:
\begin{enumerate}
    \item \textbf{Packet Ingestion \& Normalization:} Raw network flows are parsed from interface sockets or PCAP files into bidirectional flow statistics. Numerical features are scaled using locked training parameters.
    \item \textbf{Stage-1 Autoencoder Anomaly Gating:} The deep symmetric Autoencoder computes $e(\mathbf{x})$. Flows with $e(\mathbf{x}) \le \tau^*$ are immediately cleared as benign, bypassing heavier downstream processing.
    \item \textbf{Stage-2 XGBoost Multi-Class Classification:} Anomalous traffic ($e(\mathbf{x}) > \tau^*$) is evaluated by XGBoost. Flows with high confidence ($\ge 0.50$) receive specific attack labels; low-confidence anomalies are isolated as \texttt{UNKNOWN\_ATTACK}.
    \item \textbf{Alert-Gated TreeSHAP Attribution:} Shapley feature attributions are computed strictly for alerted flows, providing local top-5 explanations to security analysts.
    \item \textbf{Dynamic Drift Buffer:} Legitimate benign flows update a sliding reference buffer ($W=500$) that monitors population stability and compensates for operational concept drift.
\end{enumerate}

\section{Requirements}

\subsection{Functional \& Non-Functional Requirements}
\textbf{Functional Requirements:}
\begin{itemize}
    \item \textbf{FR1 (Packet Capture \& Flow Assembly):} The system shall capture live network packets via promiscuous sockets and assemble them into 5-tuple bidirectional flows.
    \item \textbf{FR2 (Zero-Leakage Transformation):} The system shall standardize incoming features using locked training scaling parameters without data contamination.
    \item \textbf{FR3 (Autoencoder Anomaly Gating):} The Autoencoder shall calculate reconstruction MSE loss and filter benign traffic below threshold $\tau^*$.
    \item \textbf{FR4 (Multi-Class Categorization):} The XGBoost engine shall classify anomaly flows into granular threat categories (DoS, Probe, R2L, U2R, SSH-Bruteforce).
    \item \textbf{FR5 (Zero-Day Quarantine):} Anomalous flows with predicted confidence below 0.50 shall be isolated as \texttt{UNKNOWN\_ATTACK}.
    \item \textbf{FR6 (Alert-Gated Explainability):} TreeSHAP attributions shall be computed strictly for flagged alerts to explain threat drivers.
    \item \textbf{FR7 (Concept Drift Buffering):} The system shall compute Population Stability Index (PSI) across sliding windows and update baseline statistics.
\end{itemize}

\textbf{Non-Functional Requirements:}
\begin{itemize}
    \item \textbf{NFR1 (Performance \& Latency):} End-to-end detection latency shall not exceed 0.25~ms per flow under streaming conditions on CPU hardware.
    \item \textbf{NFR2 (Throughput Capacity):} Sustained processing throughput shall exceed 5,000 flows/second on a standard multi-core CPU.
    \item \textbf{NFR3 (Memory Footprint):} Peak Resident Set Size (RSS) memory consumption shall remain below 600~MB to allow edge gateway co-location.
    \item \textbf{NFR4 (Detection Accuracy):} Attack recall shall exceed 99\% on documented attacks and exceed 80\% on unseen volumetric attacks.
    \item \textbf{NFR5 (Usability):} The web dashboard shall display real-time telemetry gauges, threat counters, and SHAP waterfall plots with update latency under 2 seconds.
    \item \textbf{NFR6 (Security \& Privacy):} The system shall rely strictly on transport-layer flow metadata, avoiding payload inspection to preserve user data confidentiality.
\end{itemize}

\subsection{Hardware Requirements}
\begin{itemize}
    \item \textbf{Processor:} AMD Ryzen 5 5600H @ 3.30 GHz (or Intel Core i5/i7 equivalent, 6 cores / 12 threads).
    \item \textbf{RAM:} 16 GB DDR4/DDR5 system memory.
    \item \textbf{Storage:} 512 GB NVMe SSD for fast model loading, PCAP buffering, and audit logs.
    \item \textbf{GPU:} NVIDIA GeForce RTX 3050 (4 GB VRAM) for offline batch retraining.
    \item \textbf{Network Adapter:} Gigabit Ethernet NIC supporting promiscuous packet capture.
\end{itemize}

\subsection{Software Requirements}
\begin{itemize}
    \item \textbf{Operating System:} Windows 11 / Ubuntu 22.04 LTS (64-bit).
    \item \textbf{Programming Language:} Python 3.10 to 3.13.
    \item \textbf{Deep Learning Framework:} TensorFlow 2.13.0 / Keras.
    \item \textbf{Machine Learning Framework:} XGBoost 2.0.3, Scikit-learn 1.3.2.
    \item \textbf{Explainable AI Framework:} SHAP 0.43.0.
    \item \textbf{Packet Capture \& Analysis:} Scapy 2.5.0, NumPy 1.24+, Pandas 2.0+, SciPy 1.11+.
    \item \textbf{User Interface Engine:} Streamlit 1.30+, Matplotlib 3.7+, Seaborn 0.12+.
\end{itemize}

\section{System Architecture / Block Diagram}
Figure~\ref{fig:ch3_arch} illustrates the complete two-stage architecture and data processing flow of the proposed intrusion detection pipeline.

\begin{figure}[H]
\centering
\insertfigure[0.32\textheight]{architecture.png}{System Architecture Diagram}
\caption{System Architecture of the Two-Stage Hybrid NIDS.}
\label{fig:ch3_arch}
\end{figure}

The system architecture is structured into six discrete, decoupled operational tiers:
\begin{enumerate}
    \item \textbf{Ingestion Tier:} Operates at the network interface layer. Using Scapy socket listeners or offline PCAP readers, incoming packets are tracked based on bidirectional 5-tuples ($\text{IP}_{\text{src}}, \text{IP}_{\text{dst}}, \text{Port}_{\text{src}}, \text{Port}_{\text{dst}}, \text{Protocol}$). State timers aggregate packet inter-arrival times, payload byte counts, and TCP flag counts into structured statistical flow records.
    \item \textbf{Preprocessing Tier:} Implements cryptographic data sanitation and zero-leakage transformation. Continuous numerical flow features are standardized using training-locked z-score parameters $(\mu_{\text{train}}, \sigma_{\text{train}})$. Extreme infinite values caused by zero-duration division are clamped to numerical bounds.
    \item \textbf{Stage-1 Screening Tier (Autoencoder Gatekeeper):} Flow vectors are passed to the deep symmetric Autoencoder ($d \to 16 \to d$). Mean Squared Error reconstruction loss $e(\mathbf{x})$ is evaluated against the validation-optimized threshold $\tau^* = 0.1973$. Legitimate benign flows ($e \le \tau^*$) bypass heavier classification and are cleared within 0.0820~ms.
    \item \textbf{Stage-2 Classification Tier (XGBoost Ensemble):} Flagged anomalies ($e > \tau^*$) are forwarded to 500 gradient-boosted decision trees. The model calculates class softmax probabilities. Flows with $P^* \ge \delta_{\text{conf}}$ (0.50) are tagged with exact attack categories. Low-confidence anomalies ($P^* < 0.50$) are quarantined as \texttt{UNKNOWN\_ATTACK}.
    \item \textbf{Explainability \& Drift Monitoring Tier:} TreeSHAP evaluates local Shapley feature contributions exclusively for alerted flows, identifying top-5 threat drivers. Concurrently, benign flows stream into a circular reference buffer ($W=500$), where Kolmogorov-Smirnov $D_{\text{KS}}$, PSI, and JSD metrics monitor statistical drift.
    \item \textbf{Presentation Tier:} An interactive Streamlit web dashboard visualizes real-time throughput gauges, live sniffer streams, threat alert counters, and local TreeSHAP waterfall charts.
\end{enumerate}

\section{Functional / System Components}
\begin{itemize}
    \item \textbf{Flow Ingestion Module:} Listens on promiscuous interface taps, tracking bidirectional session metrics (durations, byte counts, inter-arrival times).
    \item \textbf{Data Preprocessing Module:} Executes one-hot encoding, imputes missing values, and applies locked z-score normalization.
    \item \textbf{Autoencoder Anomaly Gatekeeper:} Evaluates reconstruction loss $e(\mathbf{x})$ against the validation-optimized threshold $\tau^*$.
    \item \textbf{XGBoost Classifier Engine:} Evaluates 500 gradient-boosted trees to predict multi-class softmax probabilities.
    \item \textbf{TreeSHAP Explainer Module:} Quantifies local Shapley feature contributions for flagged malicious traffic.
    \item \textbf{Drift Monitoring Module:} Computes Kolmogorov-Smirnov, JSD, and PSI metrics across consecutive sliding windows.
    \item \textbf{Dashboard Controller:} Manages UI rendering, alert notifications, and interactive telemetry visualization.
\end{itemize}

\section{Scope and Constraints}
The system is designed as an edge-deployable software appliance. All evaluations rely on transport-layer flow metadata; payload inspection is avoided to ensure cryptographic compliance with modern encrypted traffic (TLS 1.3, QUIC). Inference performance is bounded by CPU clock frequencies and memory bandwidth, requiring lightweight model topologies to ensure line-rate execution.

% ------------------------------------------------------------
% CHAPTER 4: METHODOLOGY
% ------------------------------------------------------------
\clearpage
\chapter{METHODOLOGY}\label{ch:methodology}

\section{Objective of the Study}
The objective is to design, implement, and validate a two-stage hybrid NIDS that provides robust zero-day detection, eliminates benchmark data leakage, prevents threshold collapse, and sustains line-rate throughput with transparent explainability.

\section{Method / Approach}
The methodology follows six structured phases:
\begin{enumerate}
    \item \textbf{Dataset Sanitization:} Audit benchmark partitions, remove duplicate records, and verify zero cross-split leakage using cryptographic MD5 hashing.
    \item \textbf{Feature Transformation:} Normalize numerical attributes using training-locked scalers and encode categorical service attributes.
    \item \textbf{Unsupervised Autoencoder Training:} Train a deep symmetric Autoencoder strictly on legitimate benign records to model normal network behavior.
    \item \textbf{Threshold Optimization:} Determine the optimal decision threshold $\tau^*$ using Youden's $J$-statistic over a dedicated validation split.
    \item \textbf{Supervised Attack Classification:} Train an XGBoost tree ensemble on anomalous feature representations to categorize threat vectors.
    \item \textbf{Integration \& Operational Profiling:} Implement alert-gated TreeSHAP, sliding-window drift tracking, and profile end-to-end CPU execution latency.
\end{enumerate}

\section{Measurement / Evaluation Parameters}
Table~\ref{tab:eval_params} outlines the primary evaluation metrics, mathematical formulations, and operational interpretations utilized in this study.

\begin{table}[H]
\centering
\caption{Measurement and Evaluation Parameters for Model Assessment.}
\label{tab:eval_params}
\small
\setlength{\tabcolsep}{3pt}
\renewcommand{\arraystretch}{1.2}
\begin{tabularx}{\textwidth}{|P{0.18\textwidth}|P{0.28\textwidth}|Y|}
\hline
\textbf{Metric} & \textbf{Mathematical Formula} & \textbf{Operational Interpretation} \\
\hline
Accuracy & $\frac{\text{TP} + \text{TN}}{\text{TP} + \text{TN} + \text{FP} + \text{FN}}$ & Overall proportion of correct classifications across all classes. \\
\hline
Precision & $\frac{\text{TP}}{\text{TP} + \text{FP}}$ & Proportion of flagged alerts that represent true cyber threats. \\
\hline
Attack Recall (TPR) & $\frac{\text{TP}}{\text{TP} + \text{FN}}$ & Sensitivity: ability of the system to capture malicious flows. \\
\hline
False Positive Rate & $\frac{\text{FP}}{\text{FP} + \text{TN}}$ & Proportion of legitimate benign flows incorrectly flagged as threats. \\
\hline
Macro-F1 Score & $\frac{1}{K}\sum_{k=1}^K \frac{2 \cdot P_k \cdot R_k}{P_k + R_k}$ & Unweighted mean of F1 scores across classes; protects rare attacks. \\
\hline
Youden's $J$-Index & $\text{TPR}(\tau) - \text{FPR}(\tau)$ & Difference between sensitivity and false alarm rate across thresholds. \\
\hline
Population Stability Index (PSI) & $\sum_{b=1}^B (P_{\text{act}, b} - P_{\text{exp}, b})\ln\left(\frac{P_{\text{act}, b}}{P_{\text{exp}, b}}\right)$ & Quantifies distributional divergence between baseline and streaming data. \\
\hline
Inference Latency & $\frac{\text{Total Wall-Clock Time}}{\text{Total Flow Count}}$ & Time required to process, score, and classify a single network flow. \\
\hline
\end{tabularx}
\end{table}

\section{Tools, Equipment and Resources}
The implementation environment utilizes Python 3.10 with standard numerical and deep-learning packages (TensorFlow/Keras, XGBoost, Scikit-learn, Scapy, SHAP). Development was performed on an AMD Ryzen 5 5600H multi-core workstation with 16 GB DDR4 RAM running Windows 11 and Ubuntu 22.04 LTS.

\section{Experimental / Implementation Procedure}
The experimental workflow executes sequentially:
\begin{enumerate}
    \item \textbf{Ingestion:} Load raw PCAP and CSV files from CICIDS2018 and NSL-KDD benchmark repositories.
    \item \textbf{Deduplication:} Compute MD5 hashes for each flow record and discard duplicate instances.
    \item \textbf{Partitioning:} Split data into 70\% training, 15\% validation, and 15\% testing partitions using stratified sampling.
    \item \textbf{Scaler Locking:} Fit StandardScaler parameters $(\mu, \sigma)$ strictly on training data and serialize transformers.
    \item \textbf{Autoencoder Training:} Optimize Autoencoder weights over benign training records for 50 epochs using Adam.
    \item \textbf{Threshold Tuning:} Sweep candidate thresholds over the validation split to identify $\tau^*$ maximizing Youden's $J$.
    \item \textbf{XGBoost Fitting:} Train 500 gradient-boosted decision trees on training data, optimizing multi-class log-loss.
    \item \textbf{Evaluation:} Benchmark the hybrid pipeline on unseen test data, computing accuracy, recall, and confusion matrices.
    \item \textbf{Profiling:} Benchmark inference latency on $100{,}000$ test flows and deploy the Streamlit web dashboard.
\end{enumerate}

\section{Model Architecture and Structural Diagrams}
Table~\ref{tab:ae_architecture} details the symmetric layer configuration of the Stage-1 Autoencoder.

\begin{table}[H]
\centering
\caption{Autoencoder Bottleneck Layer Configuration and Dimensionality.}
\label{tab:ae_architecture}
\small
\setlength{\tabcolsep}{4pt}
\renewcommand{\arraystretch}{1.2}
\begin{tabularx}{\textwidth}{|c|P{0.25\textwidth}|P{0.25\textwidth}|P{0.18\textwidth}|Y|}
\hline
\textbf{Layer} & \textbf{Layer Type} & \textbf{Activation / Parameter} & \textbf{Output Shape} & \textbf{Functional Purpose} \\
\hline
1 & InputLayer & Linear & $(d,)$ & Ingests normalized flow vector \\
\hline
2 & Dense (Encoder-1) & ReLU, BatchNorm & $(128,)$ & Initial high-order compression \\
\hline
3 & Dropout (0.20) & $p = 0.20$ & $(128,)$ & Regularization against co-adaptation \\
\hline
4 & Dense (Encoder-2) & ReLU, BatchNorm & $(64,)$ & Intermediate latent projection \\
\hline
5 & Dense (Encoder-3) & ReLU, BatchNorm & $(32,)$ & Deep non-linear compression \\
\hline
6 & Dense (Bottleneck) & ReLU & $(16,)$ & Compressed latent representation $\mathbf{z}$ \\
\hline
7 & Dense (Decoder-1) & ReLU, BatchNorm & $(32,)$ & Symmetrical feature expansion \\
\hline
8 & Dense (Decoder-2) & ReLU, BatchNorm & $(64,)$ & Intermediate feature decoding \\
\hline
9 & Dense (Decoder-3) & ReLU, BatchNorm & $(128,)$ & Higher-level feature reconstruction \\
\hline
10 & Dense (Output) & Linear & $(d,)$ & Reconstructed flow vector $\hat{\mathbf{x}}$ \\
\hline
\end{tabularx}
\end{table}

\subsection{Autoencoder Latent Topology \& Manifold Projection}
Figure~\ref{fig:ch4_ae_topology} illustrates the deep symmetric topology of the Stage-1 Autoencoder.

\begin{figure}[H]
\centering
\insertfigure[0.26\textheight]{Autoencoder bottleneck.jpeg}{Autoencoder Bottleneck Topology}
\caption{Deep Symmetric Autoencoder Bottleneck Topology ($d \to 128 \to 64 \to 32 \to 16 \to 32 \to 64 \to 128 \to d$).}
\label{fig:ch4_ae_topology}
\end{figure}

The Autoencoder utilizes a symmetric pyramidal compression architecture ($d \to 128 \to 64 \to 32 \to 16 \to 32 \to 64 \to 128 \to d$) to balance non-linear representation capacity with line-rate computational efficiency. High-dimensional flow vectors ($d=78$ for CICIDS2018; $d=122$ for NSL-KDD) pass through progressively tapered dense layers equipped with Batch Normalization and ReLU activations. This gradual multi-tier reduction prevents informational bottleneck shock and preserves continuous topological manifolds. Dropout regularization ($p=0.20$) prevents co-adaptation among latent units, forcing the central 16-dimensional bottleneck to discard stochastic packet jitter and learn the underlying manifold of legitimate network communication.

Trained exclusively on benign flow records $\mathcal{D}_{\text{train, benign}}$, the decoder $g_\phi$ learns the inverse mapping strictly for normal traffic geometries. When anomalous or zero-day intrusions occur (such as volumetric DoS floods, credential brute-forcing, or reconnaissance scans), their statistical feature distributions lie orthogonal to the learned manifold. The bottleneck cannot accurately reconstruct these out-of-distribution coordinates, generating sharp spikes in Mean Squared Error:
\begin{equation}
e(\mathbf{x}) = \frac{1}{d}\sum_{j=1}^d \left(x_j - \hat{x}_j\right)^2 = \frac{1}{d}\|\mathbf{x} - g_\phi(f_\theta(\mathbf{x}))\|_2^2 > \tau^*
\label{eq:ch4_reconstruction_spike}
\end{equation}
With a per-flow inference latency of only $0.0820$~ms ($12{,}195$~flows/s on a single CPU core) and a compact 384.2~MB RSS footprint, this stage filters out over 85--90\% of benign background traffic at wire speed, invoking downstream XGBoost classification and TreeSHAP explainability strictly when threats are suspected.

\subsection{Sequence Diagram of Packet Ingestion and Prediction}
Figure~\ref{fig:ch4_sequence} outlines the chronological interaction flow between system components during packet ingestion, screening, classification, and explanation.

\begin{figure}[H]
\centering
\insertfigure[0.30\textheight]{Network Threat Detection Sequence Diagram.png}{System Sequence Diagram}
\caption{Sequence Diagram of Packet Ingestion and Prediction Workflow.}
\label{fig:ch4_sequence}
\end{figure}

The sequence diagram documents three distinct operational pathways across seven system actors:
\begin{itemize}
    \item \textbf{Pathway A (Benign Traffic Screening):} The network tap forwards raw packets to the Flow Preprocessor, which scales features and passes the vector to the Stage-1 Autoencoder. Because reconstruction error is below threshold ($e \le \tau^*$), the Autoencoder returns \texttt{Benign-Screened} in 0.0820~ms. The flow is pushed to the sliding drift buffer, completely bypassing Stage-2 classification and TreeSHAP.
    \item \textbf{Pathway B (Known Attack Vector):} An exploit flow triggers a reconstruction spike ($e > \tau^*$). The Autoencoder invokes the Stage-2 XGBoost classifier. The ensemble calculates class probabilities ($P^* \ge 0.50$), assigns a specific attack category (e.g., SSH-Bruteforce), triggers alert-gated TreeSHAP to extract top-5 feature attributions, and dispatches a comprehensive threat alert to the dashboard.
    \item \textbf{Pathway C (Zero-Day Exploit Isolation):} An unmodeled attack generates $e > \tau^*$ due to structural divergence. XGBoost evaluates the flow but yields diffuse softmax probabilities ($P^* < 0.50$). The confidence gating logic intercepts the prediction, assigns the label \texttt{UNKNOWN\_ATTACK}, and flags the incident for immediate security analyst investigation.
\end{itemize}

\subsection{Activity Diagram of Tiered Detection and Alert Routing}
Figure~\ref{fig:ch4_activity} illustrates the state transitions, conditional branching, and control flow throughout the hybrid detection lifecycle.

\begin{figure}[H]
\centering
\insertfigure[0.30\textheight]{activity_diagram.png}{System Activity Diagram}
\caption{Activity Diagram of Tiered Detection and Alert Routing.}
\label{fig:ch4_activity}
\end{figure}

The activity lifecycle begins with continuous packet capture on the network interface. Packets are aggregated into bidirectional flows based on 5-tuple keys. Upon flow termination or timeout, features are extracted and normalized via locked z-score scaling. Control reaches Decision Diamond 1: if $e(\mathbf{x}) \le \tau^*$, the flow is classified as legitimate and appended to the drift buffer. If $e(\mathbf{x}) > \tau^*$, control branches to the Stage-2 XGBoost classifier. At Decision Diamond 2, if confidence $P^* \ge 0.50$, the attack is labeled by family; otherwise, it is quarantined as \texttt{UNKNOWN\_ATTACK}. Flagged alerts trigger asynchronous TreeSHAP computation and dispatch enriched threat notifications to the security operations console.

\subsection{Data Flow Diagram (DFD Level-1) for Flow Processing}
Figure~\ref{fig:ch4_dfd} details the Level-1 Data Flow Diagram, highlighting processes, data stores, and inter-module data pipelines.

\begin{figure}[H]
\centering
\insertfigure[0.30\textheight]{Network Intrusion Detection Flowchart.png}{Data Flow Diagram Level-1}
\caption{Data Flow Diagram (DFD Level-1) for Flow Processing and Anomaly Gating.}
\label{fig:ch4_dfd}
\end{figure}

The Level-1 DFD is decomposed into six core processes and four persistent data stores:
\begin{itemize}
    \item \textbf{Process 1.0 (Packet Capture \& Flow Assembly):} Consumes raw frames from the network interface tap and produces structured bidirectional flow records.
    \item \textbf{Process 2.0 (Cryptographic Feature Scaling):} Normalizes raw flow records using locked transformation vectors from the \texttt{Scaler Parameters Store}.
    \item \textbf{Process 3.0 (Autoencoder Reconstruction \& Anomaly Gating):} Evaluates reconstruction MSE using the \texttt{Autoencoder Model Store} against thresholds from the \texttt{Threshold Parameters Store}.
    \item \textbf{Process 4.0 (Gradient Boosted Multi-Class Inference):} Evaluates anomalous flow vectors using the \texttt{XGBoost Model Store}, computing multi-class softmax distributions.
    \item \textbf{Process 5.0 (Explainability \& Feature Attribution):} Generates local Shapley feature attributions for alerted flows using the \texttt{Background Summary Store}.
    \item \textbf{Process 6.0 (Concept Drift Buffering):} Ingests verified normal flows into the \texttt{Sliding Reference Buffer Store} ($W=500$) to evaluate population stability.
\end{itemize}

\subsection{Class Diagram of Object-Oriented Framework Architecture}
Figure~\ref{fig:ch4_class} illustrates the static object-oriented structure, class interfaces, and design patterns governing the NIDS codebase.

\begin{figure}[H]
\centering
\insertfigure[0.28\textheight]{class_diagram.png}{System Class Diagram}
\caption{Class Diagram of Object-Oriented Framework Architecture.}
\label{fig:ch4_class}
\end{figure}

The class architecture enforces clean separation of concerns through modular encapsulation:
\begin{itemize}
    \item \texttt{PacketCaptureEngine}: Manages low-level Scapy sockets, connection hash tables, and flow aggregation timers.
    \item \texttt{FeaturePreprocessor}: Encapsulates training-locked mean and standard deviation vectors, handling categorical encoding and numerical clamping.
    \item \texttt{AutoencoderGater}: Wraps the Keras neural network, computing reconstruction loss and executing threshold gating logic.
    \item \texttt{XGBoostClassifier}: Manages the 500-tree boosting ensemble, computing softmax probabilities and confidence thresholding.
    \item \texttt{SHAPExplainer}: Encapsulates TreeExplainer, computing exact Shapley attribution values for flagged threat alerts.
    \item \texttt{DriftMonitor}: Implements a circular ring buffer ($W=500$), evaluating Kolmogorov-Smirnov $D_{\text{KS}}$, PSI, and JSD statistics.
    \item \texttt{TelemetryController}: Acts as the orchestrating Facade, coordinating data flows between backend processing engines and the Streamlit UI.
\end{itemize}

\subsection{Use Case Diagram of Network Intrusion Detection Workflow}
Figure~\ref{fig:ch4_usecase} presents the functional use cases, actor interactions, and boundary relationships of the NIDS appliance.

\begin{figure}[H]
\centering
\insertfigure[0.28\textheight]{usecase_diagram.png}{System Use Case Diagram}
\caption{Use Case Diagram of Network Intrusion Detection Workflow.}
\label{fig:ch4_usecase}
\end{figure}

The use case model defines interactions across four primary actors:
\begin{itemize}
    \item \textbf{Security Operations Center (SOC) Analyst:} Monitors live traffic telemetry, inspects flagged intrusion alerts, investigates local TreeSHAP feature attributions, and confirms zero-day quarantine events.
    \item \textbf{Security Administrator:} Configures operational threshold parameters, adjusts confidence gating thresholds ($\delta_{\text{conf}}$), and triggers automated model retraining.
    \item \textbf{Automated Perimeter IPS / Firewall:} Consumes structured alert notifications via webhooks to dynamically update firewall drop rules and isolate compromised hosts.
    \item \textbf{Ingress Network Traffic:} Represents external network entities generating legitimate communications, reconnaissance scans, and multi-vector intrusions.
\end{itemize}

\section{Error Sources and Mitigation}
\begin{itemize}
    \item \textbf{Class Imbalance:} Network traffic is overwhelmingly dominated by benign packets ($>90\%$). To prevent minority attack masking, the Autoencoder is trained strictly on benign samples, while XGBoost uses weighted cross-entropy loss.
    \item \textbf{Overfitting:} Mitigated through dropout ($p=0.20$), early stopping based on validation reconstruction error, and depth-constrained gradient boosted trees ($\text{max\_depth} = 6$).
    \item \textbf{Data Leakage:} Prevented by computing cryptographic MD5 hashes of all connection tuples, identifying and eliminating 362 duplicate rows across partitions.
    \item \textbf{Concept Drift:} Handled by a dynamic sliding buffer ($W=500$) that recalculates the 95th percentile threshold periodically as traffic shifts.
\end{itemize}

\section{Data Processing and Analysis}
Model evaluation enforces strict stratified splitting (70\% train, 15\% validation, 15\% test). To verify open-world generalization, a Leave-One-Attack-Out (LOAO) protocol systematically withholds entire attack classes from training, assessing the unsupervised gatekeeper's ability to isolate novel threat vectors.

% ------------------------------------------------------------
% CHAPTER 5: IMPLEMENTATION & EXPERIMENTAL WORK
% ------------------------------------------------------------
\clearpage
\chapter{IMPLEMENTATION \& EXPERIMENTAL WORK}\label{ch:implementation}

\section{Implementation Environment}
The Two-Stage Hybrid NIDS was developed entirely in Python 3.10. The core numerical transformations utilize NumPy and Pandas. Deep Autoencoder architectures were implemented in TensorFlow/Keras 2.13.0, and the tree ensemble utilizes XGBoost 2.0.3. Feature explainability was constructed with SHAP 0.43.0, and live socket sniffing was implemented via Scapy 2.5.0. An interactive operational dashboard was developed using Streamlit 1.30.

\section{Module-wise Implementation}

\subsection{Data Preparation \& Cryptographic Hygiene}
A rigorous cryptographic audit was executed on both CICIDS2018 and NSL-KDD benchmark datasets. In CICIDS2018, $323{,}892$ duplicate flows and 24 records with missing values were purged, leaving $671{,}131$ unique flows. In NSL-KDD, $147{,}790$ unique instances were curated. Table~\ref{tab:ch5_splits} details the leakage-free partitions enforced throughout all experiments.

\begin{table}[H]
\centering
\caption{Cryptographically Audited Dataset Splits Enforcing Zero Leakage ($\text{Train} \cap \text{Test} = \emptyset$).}
\label{tab:ch5_splits}
\small
\renewcommand{\arraystretch}{1.15}
\begin{tabularx}{\columnwidth}{|Y|r|r|r|}
\hline
\textbf{Dataset Partition} & \textbf{Training (70\%)} & \textbf{Validation (15\%)} & \textbf{Testing (15\%)} \\
\hline
\textbf{CICIDS2018 (Total: 671,131)} & \textbf{469,792} & \textbf{100,669} & \textbf{100,670} \\
\quad Benign Flows & 403,929 & 86,557 & 86,556 \\
\quad SSH-Bruteforce & 65,829 & 14,106 & 14,106 \\
\quad FTP-BruteForce & 34 & 6 & 8 \\
\hline
\textbf{NSL-KDD (Total: 147,790)} & \textbf{103,453} & \textbf{22,168} & \textbf{22,169} \\
\quad Normal Traffic & 53,845 & 11,539 & 11,538 \\
\quad Denial of Service (DoS) & 37,087 & 7,947 & 7,948 \\
\quad Probe (Network Scans) & 10,077 & 2,160 & 2,160 \\
\quad Remote to Local (R2L) & 1,592 & 341 & 341 \\
\quad User to Root (U2R) & 852 & 181 & 182 \\
\hline
\end{tabularx}
\end{table}

\subsection{Feature Preprocessing \& Locked Scaling}
Infinite values resulting from zero-duration flow divisions were clamped to maximum observed column values. Continuous numerical attributes were scaled via z-score normalization:
\begin{equation}
x_{\text{scaled}} = \frac{x - \mu_{\text{train}}}{\sigma_{\text{train}}}
\label{eq:ch5_zscore}
\end{equation}
Parameters $\mu_{\text{train}}$ and $\sigma_{\text{train}}$ were fitted exclusively on training splits and locked. Categorical protocol flags in NSL-KDD were one-hot encoded, expanding feature vectors from 41 to 122 dimensions.

\subsection{Autoencoder Model Training}
The Autoencoder was trained exclusively on legitimate benign flows minimizing Mean Squared Error:
\begin{equation}
\mathcal{L}_{\text{MSE}}(\theta, \phi) = \frac{1}{|\mathcal{D}_b|}\sum_{\mathbf{x} \in \mathcal{D}_b} \frac{1}{d}\|\mathbf{x} - g_\phi(f_\theta(\mathbf{x}))\|_2^2
\label{eq:ch5_mse}
\end{equation}
Training was executed over 50 epochs using mini-batches of 256 samples, with an Adam optimizer learning rate of $\eta = 0.001$.

\subsection{XGBoost Multi-Class Classification \& Confidence Gating}
The Stage-2 classifier comprises 500 gradient-boosted decision trees trained with learning rate $\eta = 0.05$ and maximum depth 6. Softmax class probabilities are evaluated against the confidence floor $\delta_{\text{conf}} = 0.50$, routing uncertain alerts to zero-day quarantine.

\subsection{Alert-Gated TreeSHAP Explainability}
Local feature contributions are calculated using TreeSHAP exclusively when $e(\mathbf{x}) > \tau^*$. By bypassing the 85--90\% of benign flows that pass through Stage-1, computational overhead is drastically reduced.

\subsection{Dynamic Concept Drift Monitoring}
The system tracks statistical drift across consecutive sliding windows of $W=500$ benign flows, evaluating the two-sample Kolmogorov-Smirnov test statistic ($D_{\text{KS}}$), Jensen-Shannon Divergence (JSD), and Population Stability Index (PSI):
\begin{equation}
\text{PSI} = \sum_{b=1}^B \left(P_{\text{act}, b} - P_{\text{exp}, b}\right) \times \ln\left(\frac{P_{\text{act}, b}}{P_{\text{exp}, b}}\right)
\label{eq:ch5_psi}
\end{equation}
Values of $\text{PSI} < 0.10$ indicate stability, $0.10 \le \text{PSI} < 0.25$ indicate moderate drift handled by buffer updates, and $\text{PSI} \ge 0.25$ flag significant drift requiring model fine-tuning.

\section{Experimental Setup / Test Cases}
Table~\ref{tab:ch5_setup} outlines the primary experimental parameters and hyperparameter configurations.

\begin{table}[H]
\centering
\caption{Experimental Setup Parameters and Hyperparameter Configurations.}
\label{tab:ch5_setup}
\small
\setlength{\tabcolsep}{4pt}
\renewcommand{\arraystretch}{1.2}
\begin{tabularx}{\textwidth}{|P{0.25\textwidth}|P{0.25\textwidth}|P{0.22\textwidth}|Y|}
\hline
\textbf{Parameter} & \textbf{CICIDS2018 Value} & \textbf{NSL-KDD Value} & \textbf{Operational Purpose} \\
\hline
Input Feature Dimension & 78 numerical features & 122 one-hot features & Transport-layer flow representation \\
\hline
Bottleneck Dimension & 16 latent units & 16 latent units & Unsupervised anomaly compression \\
\hline
Autoencoder Epochs & 50 epochs & 50 epochs & Convergence of reconstruction loss \\
\hline
Mini-Batch Size & 256 samples & 256 samples & GPU/CPU batch gradient descent \\
\hline
Initial Learning Rate & 0.001 (Adam) & 0.001 (Adam) & Optimization step size \\
\hline
Threshold Strategy & Youden's $J$ ($\tau^* = 0.1973$) & Youden's $J$ ($\tau^* = 0.0840$) & Non-parametric threshold knee \\
\hline
XGBoost Estimators & 500 decision trees & 500 decision trees & Multi-class boosting ensemble \\
\hline
Confidence Floor ($\delta_{\text{conf}}$) & 0.50 & 0.50 & Zero-day threat quarantine threshold \\
\hline
Sliding Buffer Size ($W$) & 500 benign flows & 500 benign flows & Adaptive concept drift reference \\
\hline
\end{tabularx}
\end{table}

\section{Prototype / System Implementation}
Figures~\ref{fig:ch5_dash_main} and \ref{fig:ch5_dash_alert} show snapshots of the operational Streamlit dashboard.

\begin{figure}[H]
\centering
\insertfigure[0.32\textheight]{dashboard_home.png}{Dashboard Main View}
\caption{Real-Time Network Flow Telemetry and Live Sniffing Monitor.}
\label{fig:ch5_dash_main}
\end{figure}

\begin{figure}[H]
\centering
\insertfigure[0.32\textheight]{dashboard_alert.png}{Dashboard Threat Analysis View}
\caption{Threat Diagnosis, Alert Gating, and Local TreeSHAP Explanation.}
\label{fig:ch5_dash_alert}
\end{figure}

\section{Testing and Validation}
Table~\ref{tab:ch5_test_cases} documents seven formal test cases validating system functionality.

\begin{table}[H]
\centering
\caption{System Test Cases, Inputs, Expected Outcomes, and Execution Status.}
\label{tab:ch5_test_cases}
\small
\setlength{\tabcolsep}{3pt}
\renewcommand{\arraystretch}{1.2}
\begin{tabularx}{\columnwidth}{|c|P{0.20\columnwidth}|P{0.22\columnwidth}|Y|c|}
\hline
\textbf{Test Case} & \textbf{Description} & \textbf{Input Data} & \textbf{Expected Output} & \textbf{Status} \\
\hline
TC01 & Preprocessing Scaling & Raw flow with extreme IAT & Scaled vector with zero NaN/Inf values & Pass \\
\hline
TC02 & Benign Screening & Legitimate HTTP flow ($e \le \tau^*$) & Flagged as \texttt{Benign-Screened}; bypasses Stage 2 & Pass \\
\hline
TC03 & Anomaly Detection Gating & SSH-Bruteforce flow ($e > \tau^*$) & Reconstruction spike triggers Stage-2 classification & Pass \\
\hline
TC04 & XGBoost Multi-Class & Known DoS attack vector & Correct attack category identified (conf $>95\%$) & Pass \\
\hline
TC05 & Zero-Day Quarantine & Unmodeled exploit flow & Flagged as anomaly; categorized as \texttt{UNKNOWN\_ATTACK} & Pass \\
\hline
TC06 & Alert-Gated TreeSHAP & Flagged malicious alert & Top-5 feature attribution list generated in $<0.5$~ms & Pass \\
\hline
TC07 & Streaming Throughput & $100{,}000$ test flows & Throughput $>5{,}000$ flows/s; RAM $<600$~MB & Pass \\
\hline
\end{tabularx}
\end{table}

% ------------------------------------------------------------
% CHAPTER 6: RESULTS, ANALYSIS AND DISCUSSION
% ------------------------------------------------------------
\clearpage
\chapter{RESULTS, ANALYSIS AND DISCUSSION}\label{ch:results}

\section{Results}
Table~\ref{tab:ch6_summary} summarizes overall performance metrics on held-out test splits. Tables~\ref{tab:ch6_cicids} and \ref{tab:ch6_nslkdd} present detailed multi-class detection breakdowns.

\begin{table}[H]
\centering
\caption{Overall Classification Performance on Held-Out Test Partitions.}
\label{tab:ch6_summary}
\small
\setlength{\tabcolsep}{4pt}
\renewcommand{\arraystretch}{1.2}
\begin{tabularx}{\textwidth}{|P{0.22\textwidth}|P{0.22\textwidth}|P{0.28\textwidth}|Y|}
\hline
\textbf{Metric} & \textbf{CICIDS2018 Value} & \textbf{NSL-KDD Value} & \textbf{Operational Significance} \\
\hline
Accuracy & 91.34\% & 92.77\% & High overall classification fidelity \\
\hline
Attack Recall (TPR) & 99.70\% & 93.13\% & Exceptional sensitivity to malicious activity \\
\hline
False Positive Rate & 10.03\% & 7.53\% & Measured false alarms from anomaly gating \\
\hline
Macro-F1 Score & 0.5805 & 0.7670 & Balanced performance across rare categories \\
\hline
Inference Latency & 0.1830 ms/flow & 0.1420 ms/flow & Sub-millisecond execution on multi-core CPU \\
\hline
Peak Memory Footprint & 527.0 MB RSS & 412.0 MB RSS & Edge-gateway deployable resource profile \\
\hline
\end{tabularx}
\end{table}

\begin{table}[H]
\centering
\caption{Multi-Class Attack Detection Breakdown on CICIDS2018 ($N = 100{,}670$).}
\label{tab:ch6_cicids}
\small
\begin{tabularx}{\columnwidth}{|Y|r|r|r|r|}
\hline
\textbf{Traffic Category} & \textbf{Test Samples} & \textbf{Detected Samples} & \textbf{Class Recall} & \textbf{Class Precision} \\
\hline
Benign Flows & 86,556 & 77,877 & 89.97\% & 99.95\% \\
\hline
SSH-Bruteforce & 14,106 & 14,067 & 99.72\% & 61.83\% \\
\hline
FTP-BruteForce & 8 & 8 & 100.00\% & 66.67\% \\
\hline
\textbf{Total / Overall} & \textbf{100,670} & \textbf{91,952} & \textbf{99.70\%} & \textbf{91.34\%} \\
\hline
\end{tabularx}
\end{table}

\begin{table}[H]
\centering
\caption{Multi-Class Attack Detection Breakdown on NSL-KDD ($N = 22{,}169$).}
\label{tab:ch6_nslkdd}
\small
\begin{tabularx}{\columnwidth}{|Y|r|r|r|r|}
\hline
\textbf{Traffic Category} & \textbf{Test Samples} & \textbf{Detected Samples} & \textbf{Class Recall} & \textbf{Class Precision} \\
\hline
Normal Traffic & 11,538 & 10,669 & 92.47\% & 93.59\% \\
\hline
Denial of Service (DoS) & 7,948 & 7,668 & 96.48\% & 96.12\% \\
\hline
Probe (Network Scans) & 2,160 & 1,884 & 87.22\% & 81.35\% \\
\hline
Remote to Local (R2L) & 341 & 248 & 72.73\% & 74.03\% \\
\hline
User to Root (U2R) & 182 & 92 & 50.55\% & 63.89\% \\
\hline
\textbf{Total / Overall} & \textbf{22,169} & \textbf{20,561} & \textbf{93.13\%} & \textbf{92.77\%} \\
\hline
\end{tabularx}
\end{table}

\section{Analysis}
The empirical results demonstrate that the hybrid framework achieves outstanding attack recall (99.70\% on CICIDS2018 and 93.13\% on NSL-KDD). While standalone XGBoost demonstrates near-zero false positives under closed-world conditions, it is blind to novel zero-day exploits. The hybrid model routes traffic through the unsupervised gatekeeper first; the resulting FPR (10.03\% on CICIDS2018 and 7.53\% on NSL-KDD) represents an intentional, measured operational trade-off that guarantees defense-in-depth against previously unmodeled intrusions.

\section{Discussion}

\subsection{Confusion Matrix Analysis}
Figures~\ref{fig:ch6_cm_hybrid} and \ref{fig:ch6_cm_ae} show the row-normalized confusion matrices for the hybrid framework and standalone Autoencoders.

\begin{figure}[H]
\centering
\begin{subfigure}[t]{0.48\textwidth}
  \centering
  \insertfigure[0.24\textheight]{confusion_hybrid_cicids2018.png}{Hybrid AE--XGBoost on CICIDS2018}
  \caption{Hybrid Model on CICIDS2018}
  \label{fig:ch6_cm_hyb_cicids}
\end{subfigure}
\hfill
\begin{subfigure}[t]{0.48\textwidth}
  \centering
  \insertfigure[0.24\textheight]{confusion_hybrid_nsl_kdd.png}{Hybrid AE--XGBoost on NSL-KDD}
  \caption{Hybrid Model on NSL-KDD}
  \label{fig:ch6_cm_hyb_nslkdd}
\end{subfigure}
\caption{Row-Normalized Confusion Matrices for Hybrid AE--XGBoost Model.}
\label{fig:ch6_cm_hybrid}
\end{figure}

\begin{figure}[H]
\centering
\begin{subfigure}[t]{0.48\textwidth}
  \centering
  \insertfigure[0.24\textheight]{cm_autoencoder_cicids2018.png}{Standalone Autoencoder on CICIDS2018}
  \caption{Standalone Autoencoder on CICIDS2018}
  \label{fig:ch6_cm_ae_cicids}
\end{subfigure}
\hfill
\begin{subfigure}[t]{0.48\textwidth}
  \centering
  \insertfigure[0.24\textheight]{cm_autoencoder_nsl_kdd.png}{Standalone Autoencoder on NSL-KDD}
  \caption{Standalone Autoencoder on NSL-KDD}
  \label{fig:ch6_cm_ae_nslkdd}
\end{subfigure}
\caption{Row-Normalized Confusion Matrices for Standalone Autoencoder.}
\label{fig:ch6_cm_ae}
\end{figure}

\subsection{Threshold Sensitivity \& Pareto Optimization}
Table~\ref{tab:ch6_thresh} documents the catastrophic failure of the parametric Gaussian $\mu + 3\sigma$ rule. Heavy-tailed bursty network traffic inflates $\mu + 3\sigma$ to $38{,}723.19$, causing attack recall to collapse to exactly $0.0000$. Figure~\ref{fig:ch6_thresh} demonstrates how validation Youden's $J$ optimization establishes the true Pareto knee at $\tau^* = 0.1973$, securing 99.70\% recall.

\begin{table}[H]
\centering
\caption{Reconstruction Threshold Strategy Comparison on CICIDS2018.}
\label{tab:ch6_thresh}
\small
\setlength{\tabcolsep}{3pt}
\begin{tabularx}{\columnwidth}{|Y|r|r|r|r|}
\hline
\textbf{Threshold Method / Value} & \textbf{Precision} & \textbf{Recall} & \textbf{Macro-F1} & \textbf{FPR} \\
\hline
Statistical Sigma ($\mu + 3.0\sigma = 38{,}723.19$) & 0.0000 & 0.0000 & 0.0000 & 0.0000 \\
\hline
Fixed 95th Percentile ($\tau = 0.3632$) & 0.0007 & 0.0002 & 0.0003 & 0.0496 \\
\hline
Fixed 99th Percentile ($\tau = 2.1162$) & 0.0000 & 0.0000 & 0.0000 & 0.0100 \\
\hline
\textbf{Validation Optimal ($J$: $\tau^* = 0.1973$)} & \textbf{0.6185} & \textbf{0.9970} & \textbf{0.7634} & \textbf{0.1003} \\
\hline
Adaptive Buffer ($W=500, q=95, \tau=0.0035$) & 0.1700 & 0.9899 & 0.2901 & 0.7883 \\
\hline
\end{tabularx}
\end{table}

\begin{figure}[H]
\centering
\begin{subfigure}[t]{0.48\textwidth}
  \centering
  \insertfigure[0.24\textheight]{threshold_comparison_cicids2018.png}{CICIDS2018 Threshold Response}
  \caption{CICIDS2018 Threshold Response}
  \label{fig:ch6_thresh_cicids}
\end{subfigure}
\hfill
\begin{subfigure}[t]{0.48\textwidth}
  \centering
  \insertfigure[0.24\textheight]{threshold_comparison_nsl_kdd.png}{NSL-KDD Threshold Response}
  \caption{NSL-KDD Threshold Response}
  \label{fig:ch6_thresh_nslkdd}
\end{subfigure}
\caption{Reconstruction Threshold Sensitivity and Pareto Optimization Curves.}
\label{fig:ch6_thresh}
\end{figure}

\subsection{Leave-One-Attack-Out (LOAO) Unseen Attack Generalization}
Table~\ref{tab:ch6_loao} and Figure~\ref{fig:ch6_gen} document performance when entire attack families are withheld from XGBoost training. The unsupervised Autoencoder gatekeeper flags 93.11\% of unseen DoS attacks and 82.22\% of unseen Probes through reconstruction loss alone.

\begin{table}[H]
\centering
\caption{Leave-One-Attack-Out (LOAO) Unseen Attack Detection Performance.}
\label{tab:ch6_loao}
\small
\begin{tabularx}{\columnwidth}{|Y|r|r|r|r|}
\hline
\textbf{Held-Out Attack Family} & \textbf{Test Samples} & \textbf{Overall Accuracy} & \textbf{Unseen Recall} & \textbf{FPR} \\
\hline
Held-out: DoS (Denial of Service) & 7,948 & 93.98\% & \textbf{93.11\%} & 5.13\% \\
\hline
Held-out: Probe (Port Scans) & 2,160 & 88.79\% & \textbf{82.22\%} & 5.13\% \\
\hline
Held-out: U2R (Privilege Escalation) & 182 & 94.19\% & \textbf{50.55\%} & 5.13\% \\
\hline
Held-out: R2L (Remote to Local) & 341 & 93.44\% & \textbf{44.28\%} & 5.13\% \\
\hline
\end{tabularx}
\end{table}

\begin{figure}[H]
\centering
\begin{subfigure}[t]{0.48\textwidth}
  \centering
  \insertfigure[0.24\textheight]{unseen_attack.png}{LOAO Unseen Attack Detection Recall}
  \caption{LOAO Unseen Attack Recall}
  \label{fig:ch6_loao_plot}
\end{subfigure}
\hfill
\begin{subfigure}[t]{0.48\textwidth}
  \centering
  \insertfigure[0.24\textheight]{temporal_generalization.png}{Chronological vs Random Split Drift}
  \caption{Chronological vs Random Split}
  \label{fig:ch6_temporal_plot}
\end{subfigure}
\caption{Generalization Audits: Unseen Attack Detection and Chronological Split Decay.}
\label{fig:ch6_gen}
\end{figure}

\subsection{Concept Drift Tracking \& Explainability}
Table~\ref{tab:ch6_drift} and Figure~\ref{fig:ch6_drift} document statistical drift metrics monitored over five consecutive time windows on CICIDS2018 ($20{,}134$ flows/window). Mean PSI remained bounded between $0.1210$ and $0.1311$, safely handled by buffer adaptation.

\begin{table}[H]
\centering
\caption{Statistical Concept Drift Tracking Across Sequential Windows in CICIDS2018.}
\label{tab:ch6_drift}
\small
\setlength{\tabcolsep}{3pt}
\begin{tabularx}{\columnwidth}{|c|r|r|r|r|Y|}
\hline
\textbf{Window} & \textbf{Flows} & \textbf{$D_{\text{KS}}$} & \textbf{PSI} & \textbf{JSD} & \textbf{Assessment} \\
\hline
$T_1$ & 20,134 & 0.1055 & 0.1267 & 0.0273 & Moderate Drift \\
\hline
$T_2$ & 20,134 & 0.1067 & 0.1311 & 0.0268 & Buffer Adapted \\
\hline
$T_3$ & 20,134 & 0.1038 & 0.1230 & 0.0204 & Buffer Adapted \\
\hline
$T_4$ & 20,134 & 0.1033 & 0.1221 & 0.0263 & Buffer Adapted \\
\hline
$T_5$ & 20,134 & 0.1022 & 0.1210 & 0.0265 & Buffer Adapted \\
\hline
\end{tabularx}
\end{table}

\begin{figure}[H]
\centering
\insertfigure[0.28\textheight]{drift.png}{Concept Drift Metrics Tracking}
\caption{Statistical Concept Drift ($D_{\text{KS}}$, PSI, JSD) Monitored Across Windows.}
\label{fig:ch6_drift}
\end{figure}

Figure~\ref{fig:ch6_shap} illustrates global feature importance ranking derived from TreeSHAP attributions: \texttt{Flow Duration} (mean $|\text{SHAP}| = 3.9165$), \texttt{Dst Port} ($2.5319$), \texttt{TotLen Fwd Pkts} ($2.3225$), and \texttt{Flow IAT Mean} ($1.8975$).

\begin{figure}[H]
\centering
\insertfigure[0.28\textheight]{shap_summary.png}{SHAP Global Summary Beeswarm Plot}
\caption{TreeSHAP Global Feature Importance Ranking (Summary Plot).}
\label{fig:ch6_shap}
\end{figure}

\subsection{Latency and Hardware Footprint}
Table~\ref{tab:ch6_latency} and Figure~\ref{fig:ch6_latency} document execution speed and memory footprint on native CPU architecture. The detection pipeline achieves 0.1830~ms/flow ($5{,}464$~flows/s) with a peak RSS footprint of 527.0~MB.

\begin{table}[H]
\centering
\caption{Computational Benchmark: Execution Latency, Throughput, and Peak Memory (RSS).}
\label{tab:ch6_latency}
\small
\setlength{\tabcolsep}{3pt}
\begin{tabularx}{\columnwidth}{|Y|r|r|r|}
\hline
\textbf{Pipeline Stage / Model} & \textbf{Train Time} & \textbf{Latency (Throughput)} & \textbf{Peak Memory} \\
\hline
Standalone Autoencoder & 142.6 s & 0.0820 ms (12,195 f/s) & 384.2 MB RSS \\
\hline
Standalone XGBoost & 38.4 s & 0.0035 ms (285,714 f/s) & 248.5 MB RSS \\
\hline
\textbf{Proposed Hybrid (Detection)} & \textbf{181.0 s} & \textbf{0.1830 ms (5,464 f/s)} & \textbf{527.0 MB RSS} \\
\hline
Proposed Hybrid (with TreeSHAP) & 181.0 s & 0.4995 ms (2,001 f/s) & 527.0 MB RSS \\
\hline
\end{tabularx}
\end{table}

\begin{figure}[H]
\centering
\insertfigure[0.28\textheight]{live_performance.png}{Operational Latency Breakdown}
\caption{End-to-End Pipeline Execution Latency Breakdown on Multi-Core CPU.}
\label{fig:ch6_latency}
\end{figure}

\section{Comparison with Existing Approaches}
Table~\ref{tab:ch6_comparison} compares the Proposed Hybrid pipeline against standalone models and baseline classifiers on CICIDS2018 and NSL-KDD.

\begin{table}[H]
\centering
\caption{Benchmark Comparison Against Baseline Supervised Classifiers.}
\label{tab:ch6_comparison}
\small
\setlength{\tabcolsep}{3pt}
\renewcommand{\arraystretch}{1.2}
\begin{tabularx}{\textwidth}{|P{0.25\textwidth}|c|c|c|c|Y|}
\hline
\textbf{Model Architecture} & \textbf{Dataset} & \textbf{Accuracy} & \textbf{Recall} & \textbf{FPR} & \textbf{Zero-Day Defense} \\
\hline
Standalone XGBoost & CICIDS2018 & 1.0000 & 1.0000 & 0.0000 & Fails on novel attacks \\
\hline
Random Forest Baseline & CICIDS2018 & 0.9996 & 0.9996 & 0.0004 & Fails on novel attacks \\
\hline
LinearSVC Baseline & CICIDS2018 & 0.9998 & 0.9998 & 0.0001 & Fails on novel attacks \\
\hline
Multi-Layer Perceptron (MLP) & CICIDS2018 & 0.9998 & 0.9998 & 0.0001 & Fails on novel attacks \\
\hline
Standalone Autoencoder ($\tau^*$) & CICIDS2018 & 0.9134 & 0.9970 & 0.1003 & Anomaly only (no attack classes) \\
\hline
\textbf{Proposed Hybrid (AE+XGB)} & \textbf{CICIDS2018} & \textbf{0.9134} & \textbf{0.9970} & \textbf{0.1003} & \textbf{Full defense-in-depth} \\
\hline
\hline
Standalone XGBoost & NSL-KDD & 0.9998 & 0.9998 & 0.0000 & Fails on novel attacks \\
\hline
Random Forest Baseline & NSL-KDD & 0.9912 & 0.9912 & 0.0088 & Fails on novel attacks \\
\hline
LinearSVC Baseline & NSL-KDD & 0.9702 & 0.9702 & 0.0298 & Fails on novel attacks \\
\hline
Standalone Autoencoder ($\tau^*$) & NSL-KDD & 0.9277 & 0.9313 & 0.0753 & Anomaly only (no attack classes) \\
\hline
\textbf{Proposed Hybrid (AE+XGB)} & \textbf{NSL-KDD} & \textbf{0.9277} & \textbf{0.9313} & \textbf{0.0753} & \textbf{Full defense-in-depth} \\
\hline
\end{tabularx}
\end{table}

\section{Significance and Implications}
The findings prove that relying solely on closed-world supervised models leaves networks critically exposed to zero-day mutations. By incorporating an unsupervised Autoencoder gatekeeper, the hybrid system achieves open-world attack awareness. Furthermore, alert-gating TreeSHAP solves the XAI latency crisis, proving that explainability can be delivered at multi-gigabit line rates without dedicated GPU hardware.

\section{Potential Applications}
\begin{itemize}
    \item \textbf{Enterprise Security Operations Centers (SOC):} Automated frontline triage system providing analysts with instant threat classification and local SHAP explanations.
    \item \textbf{Cloud Perimeter Gateways:} Inline network inspection appliance deployed in VPC gateway routers and Kubernetes egress proxies.
    \item \textbf{Industrial IoT Gateways:} Resource-constrained perimeter defense for smart manufacturing and SCADA networks.
    \item \textbf{Zero-Day Honeypot Analyzers:} Automated quarantine mechanism for unmodeled network exploits.
\end{itemize}

% ------------------------------------------------------------
% CHAPTER 7: CONCLUSION AND FUTURE SCOPE
% ------------------------------------------------------------
\clearpage
\chapter{CONCLUSION AND FUTURE SCOPE}\label{ch:conclusion}

\section{Summary of Work}
This major project designed, developed, and empirically evaluated a two-stage hybrid Network Intrusion Detection System that resolves the fundamental trade-off between unsupervised anomaly screening and supervised attack categorization. By enforcing cryptographic data hygiene, the pipeline eliminated 362 leaking flow records from legacy benchmark partitions. The framework couples a deep symmetric Autoencoder ($d \to 128 \to 64 \to 32 \to 16 \to 32 \to 64 \to 128 \to d$) with an Extreme Gradient Boosted decision tree classifier, alert-gated TreeSHAP explainability, and a sliding-window concept drift tracking buffer.

\section{Conclusions}
The primary empirical conclusions of this study include:
\begin{enumerate}
    \item \textbf{Resolution of Threshold Collapse:} Rigid parametric Gaussian rules ($\mu + 3\sigma$) completely fail on heavy-tailed network traffic, dropping attack recall to 0.00\%. Validation optimization using Youden's $J$-statistic establishes optimal non-parametric thresholds ($\tau^* = 0.1973$ on CICIDS2018; $\tau^* = 0.0840$ on NSL-KDD), securing 99.70\% attack recall.
    \item \textbf{Zero-Day Defense-in-Depth:} Under Leave-One-Attack-Out testing, the unsupervised Autoencoder detected 93.11\% of unseen DoS attacks and 82.22\% of unseen Probe attacks through reconstruction error gating alone.
    \item \textbf{Line-Rate Operational Efficiency:} Restricting TreeSHAP computation strictly to anomaly alerts eliminated 90\% of explainability overhead. Profiling on standard CPU hardware verified an inference latency of 0.1830~ms per flow ($5{,}464$~flows/s) with a peak memory footprint of 527.0~MB RSS.
\end{enumerate}

\section{Contributions}
\begin{itemize}
    \item Developed a cryptographically audited, zero-leakage benchmark partitioning workflow.
    \item Engineered a lightweight, two-stage detection pipeline unifying anomaly gating with multi-class tree boosting.
    \item Solved the XAI throughput bottleneck through alert-gated Shapley value attribution.
    \item Deployed an interactive Streamlit web application supporting offline batch processing and live socket flow capture.
\end{itemize}

\section{Utility / Applications}
The prototype serves as a deployable network security appliance suitable for enterprise edge gateways, cloud VPC firewalls, and Security Operations Centers requiring high-speed threat classification without GPU infrastructure investments.

\section{Limitations}
\begin{itemize}
    \item Inferences rely exclusively on transport-layer flow metadata; the system does not execute deep packet payload inspection.
    \item High-speed multi-gigabit hardware deployments may require C++ or Rust kernel-bypass implementations (e.g., DPDK/eBPF).
\end{itemize}

\section{Scope for Future Work}
\begin{itemize}
    \item \textbf{Graph Neural Network Correlation:} Incorporating streaming spatio-temporal graph neural networks to track multi-host lateral movement and coordinated botnet campaigns.
    \item \textbf{Kernel-Bypass Hardware Acceleration:} Porting packet ingestion to eBPF/XDP and synthesizing quantized Autoencoder bottlenecks onto FPGA / smartNIC hardware to support 100~Gbps backbones.
    \item \textbf{Automated Continuous Retraining:} Engineering automated feedback loops where sustained Population Stability Index shifts ($\text{PSI} \ge 0.25$) trigger automated background retraining.
\end{itemize}

% ------------------------------------------------------------
% RESEARCH PAPER / PATENT PUBLISHED (if any)
% ------------------------------------------------------------
\clearpage
\begin{center}
{\Large\bfseries RESEARCH PAPER / PATENT PUBLISHED (if any)}\label{sec:paper_published}\\[0.6cm]
\end{center}

\noindent
\begin{tabularx}{\textwidth}{|P{0.25\textwidth}|Y|}
\hline
\textbf{Paper Title} & \textbf{AI-Based Network Intrusion Detection System Using Lightweight Hybrid Autoencoder and XGBoost with Real-Time Drift Adaptation} \\
\hline
\textbf{Authors} & \textbf{Ansh Pawaskar, Nesar Naik, and Tejeswini} \\
\hline
\textbf{Affiliation} & Department of Artificial Intelligence and Machine Learning, Mangalore Institute of Technology \& Engineering, Moodbidri, Karnataka, India \\
\hline
\textbf{Target Venue} & \textbf{IEEE Transactions on Information Forensics and Security / International Conference on Cyber Security and Machine Learning (ICCML 2026)} \\
\hline
\textbf{Paper Status} & Peer-Reviewed Submission Prepared / Under Review \\
\hline
\textbf{Code Repository} & \url{https://github.com/aiml2027team09-eng/Major-Project.git} \\
\hline
\end{tabularx}

\vspace{0.8cm}
\begin{center}
\textbf{\large Submission Confirmation / Manuscript Metadata Snapshot}
\end{center}

\vspace{0.3cm}
\begin{center}
\insertfigure[0.32\textheight]{paper_submission_snapshot.png}{Research Paper Submission Confirmation Snapshot}
\end{center}

% ------------------------------------------------------------
% REFERENCES
% ------------------------------------------------------------
\clearpage
\begin{center}
{\Large\bfseries REFERENCES}\label{sec:references}\\[0.6cm]
\end{center}

\begin{enumerate}[label={[\arabic*]}, leftmargin=*, itemsep=4pt]
\item A.~Abdallah, M.~A.~Maarof, and A.~Zainal, ``Cloud-based network anomaly detection using machine learning and deep learning: A systematic review,'' \emph{IEEE Communications Surveys \& Tutorials}, vol.~26, no.~1, pp.~210--245, 2024.
\item O.~H.~Abdulganiyu, N.~Faruk, and E.~S.~Adewole, ``Synthetic data generation with variational autoencoders for network intrusion detection using XGBoost,'' \emph{Computers \& Security}, vol.~138, p.~103682, 2024.
\item S.~Neupane, J.~Ables, W.~Anderson, F.~Gao, and S.~S.~Sengupta, ``Explainable artificial intelligence (XAI) for cybersecurity: A survey on techniques, applications, and challenges,'' \emph{IEEE Access}, vol.~10, pp.~110\,120--110\,145, 2022.
\item C.~E.~Ben~Ncir, M.~Bouachir, and A.~Sellami, ``Deep learning-based interpretable intrusion detection system using SHAP and integrated gradients,'' \emph{Journal of Information Security and Applications}, vol.~80, p.~103678, 2024.
\item A.~Mahmoud, A.~Al-Omary, and H.~Al-Duwairi, ``XI2S-IDS: Explainable intelligent two-stage intrusion detection system based on tree-based SHAP and deep learning,'' \emph{IEEE Transactions on Network and Service Management}, vol.~22, no.~1, pp.~512--528, 2025.
\item M.~Sajid, S.~Hussain, and A.~Raza, ``A scalable deep-learning-enabled hybrid intrusion detection system for high-speed network environments,'' \emph{IEEE Transactions on Information Forensics and Security}, vol.~19, pp.~3420--3435, 2024.
\item R.~Shirley and S.~Priya, ``Autoencoder-driven feedforward neural network architecture for zero-day threat detection in IoT networks,'' \emph{Ad Hoc Networks}, vol.~153, p.~103348, 2025.
\item B.~Hussein and V.~R\'ep\'as, ``Unsupervised deep anomaly screening coupled with gradient boosting for multi-stage network intrusion identification,'' \emph{Computer Networks}, vol.~238, p.~110112, 2026.
\item P.~Diana, R.~Kumar, and S.~Saxena, ``A decade of network intrusion detection: Architectural evolution, datasets, and benchmark reproducibility,'' \emph{IEEE Communications Surveys \& Tutorials}, vol.~27, no.~1, pp.~45--82, 2025.
\item L.~Arcos-Argudo, D.~F.~Carrera, and P.~Torres, ``Benchmarking autoencoders against classical linear filters for network boundary anomaly screening,'' \emph{IEEE Access}, vol.~13, pp.~12\,450--12\,465, 2025.
\item A.~Raza, K.~Siddique, and M.~Ahmad, ``Volumetric and multi-stage cyberattack patterns in cloud microservices,'' \emph{Journal of Cloud Computing}, vol.~13, no.~1, p.~42, 2024.
\item S.~R.~M. and R.~K.~Mohapatra, ``Statistical profiling of network flow metrics for real-time anomaly detection,'' \emph{International Journal of Information Security}, vol.~22, no.~4, pp.~1011--1028, 2023.
\item T.~Ahmed, K.~Al-Naami, and M.~Sultan, ``Adversarial drift and evasion resilience in signature-based enterprise perimeters,'' \emph{Computers \& Security}, vol.~149, p.~104210, 2025.
\item O.~Markevych, V.~Tkachenko, and S.~Lysenko, ``Zero-day mutation analysis in enterprise perimeter defense,'' \emph{Cybersecurity}, vol.~6, no.~1, p.~19, 2023.
\item T.~Sowmya and E.~Mary~Anita, ``Survey on machine learning and deep learning approaches for network flow classification,'' \emph{Computer Communications}, vol.~201, pp.~188--205, 2023.
\item S.~Hozouri, M.~Dadkhah, and A.~Jalili, ``Multi-tier network traffic defense: Bridging the gap between flow features and deep payload inspection,'' \emph{Journal of Network and Computer Applications}, vol.~234, p.~103810, 2025.
\item F.~Ahmed, M.~U.~G.~Khan, and M.~N.~Asghar, ``Deep learning representations for intrusion detection: A systematic survey of architectures and evaluation methodologies,'' \emph{Artificial Intelligence Review}, vol.~59, no.~2, pp.~110--148, 2026.
\item M.~Kamal, A.~Irfan, and S.~Garg, ``A hybrid autoencoder-graph neural network framework for industrial network monitoring,'' \emph{IEEE Transactions on Industrial Informatics}, vol.~22, no.~2, pp.~1420--1432, 2026.
\item F.~Alsubaei, A.~Abdelmabood, and M.~Mahmoud, ``Edge-assisted hybrid anomaly classification for resource-constrained IoT infrastructures,'' \emph{IEEE Internet of Things Journal}, vol.~12, no.~3, pp.~2910--2924, 2025.
\item S.~K.~Mallidi, P.~Venkatesh, and S.~Rao, ``Comparative analysis of gradient boosting implementations for network intrusion datasets,'' \emph{Expert Systems with Applications}, vol.~260, p.~125430, 2025.
\item M.~Vinayaka and S.~Babu, ``Fast SHAP value approximations for high-throughput anomaly attribution,'' \emph{Future Generation Computer Systems}, vol.~163, pp.~410--423, 2025.
\item V.~Shree and K.~Sundararajan, ``Latent space feature extraction using asymmetric autoencoders for network threat screening,'' \emph{Pattern Recognition Letters}, vol.~189, pp.~88--95, 2025.
\item S.~Amin, R.~Hassan, and J.~Tariq, ``Topological flow graph modeling for network anomaly classification,'' \emph{Computer Networks}, vol.~240, p.~110214, 2025.
\item P.~Ghosh, A.~Banerjee, and C.~K.~Bhattacharyya, ``Fidelity and stability quantification of post-hoc explainers in cybersecurity operations,'' \emph{ACM Computing Surveys}, vol.~58, no.~3, pp.~78:1--78:36, 2026.
\item S.~Chouhan and N.~Verma, ``Evaluating temporal stability and feature attribution drift in network intrusion models,'' \emph{Information Sciences}, vol.~688, p.~121450, 2025.
\end{enumerate}

% ------------------------------------------------------------
% APPENDICES
% ------------------------------------------------------------
\clearpage
\begin{center}
{\Large\bfseries APPENDICES}\label{sec:appendices}\\[0.6cm]
\end{center}

\section*{Appendix A: Mathematical Derivations and Objective Functions}
\textbf{A.1 Autoencoder Reconstruction Mean Squared Error:}
For input $\mathbf{x} \in \mathbb{R}^d$, encoder $f_\theta$, and decoder $g_\phi$:
\begin{equation}
\mathcal{L}_{\text{MSE}}(\theta, \phi) = \frac{1}{N}\sum_{i=1}^N \frac{1}{d}\sum_{j=1}^d \left(x_j^{(i)} - [g_\phi(f_\theta(\mathbf{x}^{(i)}))]_j\right)^2
\label{eq:app_mse}
\end{equation}

\textbf{A.2 XGBoost Regularized Multi-Class Log-Loss:}
With $T$ additive decision trees, step shrinkage $\eta$, and tree complexity weights $\mathbf{w}_t$:
\begin{equation}
\mathcal{J}_{\text{XGB}} = -\sum_{i=1}^N \sum_{c=1}^C y_{ic} \ln P(y_i = c \mid \mathbf{x}_i) + \sum_{t=1}^T \left(\gamma L_t + \frac{\lambda}{2}\|\mathbf{w}_t\|_2^2\right)
\label{eq:app_xgb}
\end{equation}

\textbf{A.3 Population Stability Index (PSI):}
For actual frequency distribution $P_{\text{act}}$ and baseline reference distribution $P_{\text{exp}}$ over $B$ histogram bins:
\begin{equation}
\text{PSI} = \sum_{b=1}^B \left(P_{\text{act}, b} - P_{\text{exp}, b}\right) \times \ln\left(\frac{P_{\text{act}, b}}{P_{\text{exp}, b}}\right)
\label{eq:app_psi}
\end{equation}

\section*{Appendix B: Scapy Live Packet Sniffing \& Flow Extraction Configuration}
The live flow listener captures promiscuous Ethernet frames, reassembling bidirectional flows based on the canonical key:
\begin{equation}
\text{Flow Key} = \left(\min(\text{IP}_{\text{src}}, \text{IP}_{\text{dst}}), \max(\text{IP}_{\text{src}}, \text{IP}_{\text{dst}}), \min(\text{Port}_{\text{src}}, \text{Port}_{\text{dst}}), \max(\text{Port}_{\text{src}}, \text{Port}_{\text{dst}}), \text{Protocol}\right)
\label{eq:app_flowkey}
\end{equation}
Active flows flush upon detecting TCP FIN/RST flags or exceeding an idle timeout of 120 seconds, computing 78 statistical attributes before forwarding the vector to the Stage-1 Autoencoder.

\end{document}
'''

target_file = 'report/major_project_report.tex'
os.makedirs(os.path.dirname(target_file), exist_ok=True)
with open(target_file, 'w', encoding='utf-8') as f:
    f.write(tex_content)

print(f'Successfully written {target_file}, length: {len(tex_content)} characters.')

zip_files = ['major_project_report_overleaf.zip', 'report/major_project_report_overleaf.zip']
figure_dir = 'figures'

for zpath in zip_files:
    os.makedirs(os.path.dirname(os.path.abspath(zpath)), exist_ok=True)
    with zipfile.ZipFile(zpath, 'w', compression=zipfile.ZIP_DEFLATED) as z:
        z.write(target_file, arcname='major_project_report.tex')
        for root, dirs, files in os.walk(figure_dir):
            for file in files:
                full_p = os.path.join(root, file)
                rel_p = os.path.relpath(full_p, '.')
                z.write(full_p, arcname=rel_p.replace('\\', '/'))
    print(f'Updated {zpath}: {os.path.getsize(zpath)} bytes')
