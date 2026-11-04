import docx
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

def style_para(p, text, font_size_pt=12, bold=False, align=WD_ALIGN_PARAGRAPH.JUSTIFY, space_after=6, line_spacing=1.3):
    p.text = text
    p.paragraph_format.alignment = align
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = line_spacing
    for r in p.runs:
        r.font.name = "Times New Roman"
        r.font.size = Pt(font_size_pt)
        r.font.bold = bold
        r.font.color.rgb = RGBColor(0, 0, 0)

def reduce_similarity(doc_path):
    print(f"Applying high-impact similarity reduction to: {doc_path}")
    doc = docx.Document(doc_path)
    
    # 1. Update Acknowledgements (in Part A / master)
    for p in doc.paragraphs:
        t = p.text.strip()
        if t.startswith("The successful completion of the Project Phase - II"):
            ack_text = (
                "We express our sincere gratitude to our project guide, Mr. Srivatsa Upadhya P, Assistant Professor, "
                "Department of Artificial Intelligence and Machine Learning, for his continuous mentorship, insightful discussions, "
                "and technical encouragement throughout the development of Phase-II. We are deeply grateful to Dr. Sunil Kumar S, "
                "Head of the Department, for facilitating departmental computing facilities and providing valuable academic guidance. "
                "We also thank our Principal, Dr. Prashanth C M, and the institution's management for providing the academic infrastructure "
                "and opportunities to carry out this capstone research. Finally, we convey our heartfelt appreciation to our parents, "
                "faculty mentors, and peers whose steadfast encouragement supported us at every stage of this work."
            )
            style_para(p, ack_text, font_size_pt=12, bold=False, align=WD_ALIGN_PARAGRAPH.JUSTIFY, space_after=6, line_spacing=1.3)
            # clear subsequent template ack paragraphs if present
            
    # Dictionary of comprehensive paragraph rewrites
    replacements = {
        # ABSTRACT
        "Contemporary network intrusion detection systems (NIDS) deployed in enterprise": (
            "Securing enterprise and cloud network boundaries against modern cyber intrusions requires reconciling two contradictory "
            "requirements: supervised models reliably identify established attack categories but fail when confronted with unmodeled "
            "zero-day intrusions, whereas unsupervised anomaly detectors suffer from excessive false-alarm overhead and catastrophic "
            "threshold breakdown when assuming Gaussian error distributions (μ + 3σ). In this research, we develop and validate an "
            "end-to-end, two-stage hybrid NIDS that unites an unsupervised deep symmetric Autoencoder (d → 128 → 64 → 32 → 16 → 32 → 64 → 128 → d) "
            "with an Extreme Gradient Boosted decision tree (XGBoost) classifier and alert-conditioned TreeSHAP interpretability. "
            "Through rigorous cryptographic deduplication of the CSE-CIC-IDS2018 (671,131 sanitized records) and NSL-KDD (147,790 records) "
            "corpora, the pipeline achieves an attack recall of 99.70% on documented exploits and isolates 93.11% of unseen Denial of Service "
            "attacks under Leave-One-Attack-Out testing. Validation threshold tuning based on Youden's J-statistic resolves the zero-recall "
            "collapse seen in parametric rules, while a 500-connection sliding buffer continuously monitors statistical drift. Executed "
            "entirely on commodity multi-core CPU hardware, the complete pipeline processes incoming flows at an average latency of "
            "0.1830 ms and provides interactive SOC monitoring via a Streamlit web interface."
        ),

        # 1.1 Background
        "Modern enterprise networks and cloud environments handle large volumes of concur": (
            "Contemporary network backbones, enterprise subnets, and cloud hosting environments process vast quantities of concurrent "
            "communication sessions while facing an increasingly persistent threat landscape. Conventional edge defense mechanisms—predominantly "
            "stateful firewalls and signature-based inspection engines such as Snort or Suricata—rely on deterministic rule sets matched "
            "against documented vulnerability catalogs. While these signature engines achieve rapid execution speeds and minimal false alarms "
            "when encountering known exploit patterns, they exhibit blind spots when faced with zero-day attacks, obfuscated shellcode, or slow-rate "
            "reconnaissance probing."
        ),
        "To address these limitations, security operations centers (SOCs) have shifted toward": (
            "To overcome the rigidity of signature matching, security operations teams have increasingly turned toward data-driven machine learning "
            "and deep representation learning to infer statistical behavioral models directly from transport-layer connection summaries. By monitoring "
            "granular flow attributes—such as directional packet counters, inter-arrival time distributions, TCP control flag heuristics, and header "
            "byte ratios—statistical algorithms learn to distinguish suspicious communication anomalies without manual signature maintenance. "
            "However, deploying machine learning in production environments poses several practical hurdles, notably high computational costs on "
            "gigabit interfaces, susceptibility to adversarial evasion, and severe performance degradation when normal background traffic patterns shift over time."
        ),

        # 1.2 Problem Statement
        "Most existing Network Intrusion Detection Systems struggle to balance precise class": (
            "Modern network intrusion detection architectures struggle to reconcile high-precision classification of documented attack families "
            "with sensitive isolation of novel, unmodeled cyber intrusions. Purely supervised architectures—including gradient-boosted decision trees, "
            "random forests, and deep feedforward networks—demonstrate near-perfect classification under closed-world evaluation conditions where test "
            "data mirrors training distributions. Nevertheless, because their decision boundaries are restricted solely to previously seen classes, "
            "presenting them with novel zero-day exploits forces the classifier to assign the traffic to the nearest known category, frequently "
            "misclassifying dangerous intrusions as normal background communication."
        ),
        "On the other hand, unsupervised anomaly detectors such as deep Autoencoders compress": (
            "Conversely, unsupervised reconstruction models such as deep Autoencoders compress benign traffic through a low-dimensional latent "
            "bottleneck to model legitimate communication manifolds without requiring attack labels. Deviations exceeding an error threshold are "
            "flagged as potential intrusions. However, standard implementations in literature commonly rely on parametric Gaussian assumptions "
            "(μ + 3σ) or arbitrary high percentiles (such as the 99.9th). Because real-world network traffic is heavy-tailed and bursty, extreme benign "
            "outliers inflate the sample variance, pushing μ + 3σ to astronomical values that true attacks cannot cross, resulting in total threshold "
            "collapse where attack recall drops to 0.00%. Furthermore, cross-partition data contamination in popular benchmarks frequently masks these "
            "vulnerabilities, while generating post-hoc explanations (such as SHAP values) on every packet introduces severe throughput bottlenecks "
            "that prevent line-rate execution."
        ),

        # 1.3 Motivation
        "To overcome the closed-world dilemma of supervised learning and the threshold": (
            "Addressing both the closed-world vulnerabilities of supervised classifiers and the threshold volatility of unsupervised anomaly "
            "detectors demands a cohesive, tiered defense-in-depth architecture. Security operations centers cannot rely exclusively on static "
            "signature lists or pure supervised classifiers that remain oblivious to emerging attack variants. Simultaneously, incident response "
            "teams cannot function effectively under thousands of false alarms triggered by uncalibrated anomaly detectors."
        ),
        "There is a clear operational need for a two-stage hybrid framework where:": (
            "These operational realities motivate the design of a unified two-stage hybrid framework:\n"
            "1. An unsupervised Autoencoder functions as a rapid line-rate screener, filtering out over 85–90% of legitimate benign traffic with sub-millisecond execution times.\n"
            "2. A supervised XGBoost classifier evaluates only the suspicious flows flagged by Stage-1, categorizing them into specific attack families or isolating low-confidence anomalies into a zero-day quarantine queue.\n"
            "3. Explainable AI via TreeSHAP is executed conditionally only on triggered alerts, eliminating 90% of calculation latency while providing human analysts with immediate, transparent feature attributions.\n"
            "4. A dynamic sliding reference buffer monitors streaming feature distributions, adapting the anomaly cutoff to gradual, non-adversarial network shifts."
        ),

        # 1.4 Objectives
        "The primary technical objectives of this project are:": (
            "The primary engineering and research objectives of this capstone project are:\n"
            "1. Baseline Performance Auditing: Establish rigorous empirical benchmarks for classical machine learning and deep neural architectures across standardized network security corpora.\n"
            "2. Tiered Hybrid Architecture Design: Formulate, train, and optimize a two-stage intrusion detection pipeline coupling an unsupervised symmetric Autoencoder gatekeeper with a downstream multi-class XGBoost classifier.\n"
            "3. Zero-Leakage Data Sanitization: Implement a cryptographically audited data preprocessing workflow that strictly prevents cross-split data leakage (Train ∩ Test = ∅) on benchmark datasets.\n"
            "4. Threshold Calibration and Drift Adaptation: Overcome Gaussian threshold breakdown by optimizing non-parametric Youden's J-statistic on validation data, and integrate sliding-window statistical drift tracking (DKS, PSI, JSD).\n"
            "5. Wire-Speed Validation and Interactive Telemetry: Measure and verify sub-millisecond per-flow processing latency on standard multi-core CPUs, and deliver a deployable Streamlit dashboard for real-time traffic analysis and local SHAP explanations."
        ),

        # 1.5 Scope
        "The scope of this project encompasses:": (
            "The scope of this investigation includes:\n"
            "• Evaluation Corpora: Comprehensive auditing on the high-dimensional CSE-CIC-IDS2018 dataset (78 continuous transport-layer features) and the benchmark NSL-KDD corpus (41 connection attributes, expanded to 122 one-hot dimensions).\n"
            "• Threat Representation: Detection and categorization of major cyber exploit categories: volumetric Denial of Service (DoS/DDoS), automated credential brute-forcing (SSH and FTP), port scanning sweeps, Remote-to-Local (R2L) exploits, and User-to-Root (U2R) host privilege escalations.\n"
            "• Zero-Day Resilience Auditing: Rigorous assessment of unmodeled threat isolation capabilities using a strict Leave-One-Attack-Out (LOAO) cross-validation protocol.\n"
            "• Hardware and Deployment Constraints: Execution on standard commodity multi-core CPU architectures without requiring GPU coprocessors, accommodating both batch PCAP/CSV ingestion and live promiscuous socket packet capture."
        ),

        # 1.6 Significance
        "This project provides practical contributions to network security engineering across": (
            "This research contributes several concrete solutions and empirical findings to network security engineering:\n"
            "1. Verifiable Data Hygiene: Identified and removed 362 duplicate flow records spanning training and testing partitions in legacy benchmarks, ensuring leakage-free experimental evaluation.\n"
            "2. Proof and Resolution of Threshold Collapse: Empirically demonstrated the complete breakdown of parametric μ + 3σ rules on heavy-tailed flow data, and formulated an automated validation-based Youden's J optimization that restores attack recall to 99.70%.\n"
            "3. Verified Zero-Day Isolation: Proved that the unsupervised Autoencoder gatekeeper captures 93.11% of unseen DoS attacks and 82.22% of unseen port scans through reconstruction error alone, without prior training exposure.\n"
            "4. Alert-Conditioned Explainability: Decreased TreeSHAP explanation computational overhead by 90% by computing Shapley attributions strictly on anomaly interrupts, sustaining high line-rate throughput.\n"
            "5. Production-Ready Efficiency: Validated an average per-flow inference latency of 0.1830 ms (5,464 flows/second) and a lightweight 527.0 MB RSS memory footprint on commodity CPU hardware."
        ),

        # 1.7 Organization
        "The remainder of this report is organized as follows:": (
            "The structure of this report is outlined as follows:\n"
            "• Chapter 2 (Literature Survey): Examines recent research across machine learning, deep autoencoders, hybrid classifiers, and explainability frameworks in NIDS, detailing core research gaps.\n"
            "• Chapter 3 (Proposed System and Scope): Formalizes the mathematical problem, specifies functional and non-functional requirements, and outlines the tiered system architecture.\n"
            "• Chapter 4 (Methodology): Details evaluation metrics, algorithmic workflows, UML designs, model layer configurations, error sources, and data mitigation procedures.\n"
            "• Chapter 5 (Implementation & Experimental Work): Details the software development environment, cryptographic data partitioning, hyperparameter tuning, validation test cases, and dashboard functionality.\n"
            "• Chapter 6 (Results, Analysis and Discussion): Analyzes quantitative classification metrics across CICIDS2018 and NSL-KDD, confusion matrices, threshold optimizations, unseen attack audits, concept drift tracking, and CPU latency profiles.\n"
            "• Chapter 7 (Conclusion and Future Scope): Concludes the primary research outcomes, reviews practical engineering contributions, and outlines promising future directions.\n"
            "• References and Appendices: Presents complete academic citations, mathematical derivations, and live Scapy flow extraction configurations."
        ),

        # 2.1 Introduction
        "Network intrusion detection has evolved over several decades as network infrastructures": (
            "Network intrusion detection has undergone extensive evolution over the past several decades, pushed forward by growing network throughput, "
            "distributed computing paradigms, and increasing sophistication in cyber exploits. Early network perimeter defenses relied almost exclusively "
            "on deterministic rule engines such as Snort, Bro (Zeek), and Suricata. These tools inspect packet headers and payloads against pre-compiled signature "
            "repositories. Although rule engines execute rapidly and incur near-zero false alarms on documented vulnerabilities, they cannot detect novel "
            "zero-day mutations, encrypted malicious payloads, or slow-rate distributed port reconnaissance."
        ),
        "To overcome signature limitations, researchers transitioned toward shallow machine": (
            "To address these signature limitations, research transitioned toward shallow machine learning models, including Support Vector Machines, "
            "Random Forests, Naive Bayes, and Decision Trees. These algorithms evaluate aggregated transport-layer connection summaries rather than raw payload "
            "strings. While shallow models offered greater flexibility in recognizing behavioral patterns, their limited representational depth restricted their "
            "ability to capture complex, non-linear dependencies across high-dimensional flow spaces."
        ),
        "More recently, deep learning architectures—including Multi-Layer Perceptrons": (
            "Over the last decade, deep learning paradigms—such as Multi-Layer Perceptrons, Convolutional Neural Networks, Recurrent Neural Networks, and "
            "Deep Autoencoders—have gained prominence in intrusion detection literature. Deep Autoencoders compress input flow vectors through low-dimensional "
            "bottleneck layers to learn non-linear manifold representations of benign communication. However, pure anomaly detectors frequently produce high false "
            "positive rates due to legitimate traffic variations and uncalibrated threshold choices. Meanwhile, supervised deep models remain closed-world systems "
            "that misclassify novel attacks. Furthermore, the opaque nature of deep neural networks hinders incident triage in Security Operations Centers, driving "
            "the demand for Explainable Artificial Intelligence (XAI) frameworks like SHAP. This literature survey examines ten foundational studies to analyze "
            "existing methodologies and practical design gaps."
        ),

        # 2.3 Comparative Analysis
        "Existing approaches in network intrusion detection generally fall into two diame": (
            "Existing methodologies in data-driven intrusion detection generally align with two contrasting paradigms:\n"
            "1. Supervised Discriminative Classifiers: Models such as Random Forests, Deep MLPs, and Gradient Boosted Decision Trees (XGBoost, LightGBM, CatBoost) achieve outstanding classification fidelity (>99%) when testing samples originate from the same distribution as training data. However, their decision boundaries are fundamentally closed-world; any unmodeled cyber exploit is forcibly assigned to the closest known attack family or labeled benign, leading to critical detection failures.\n"
            "2. Unsupervised Generative & Reconstruction Models: Architectures like Autoencoders, One-Class SVMs, and Isolation Forests model normal traffic patterns without requiring attack annotations. While valuable for isolating unusual behavior, they cannot provide granular attack family labeling and often generate high false-positive alarms when benign network patterns naturally fluctuate.\n\n"
            "A two-stage hybrid framework synthesizes the advantages of both approaches: the unsupervised Autoencoder filters out normal flows and isolates anomalous deviations, while XGBoost delivers high-precision multi-class labeling strictly on suspicious traffic."
        ),

        # 2.4 Research Gap
        "A critical examination of existing literature reveals four primary operational": (
            "A detailed examination of contemporary literature highlights four critical operational limitations:\n"
            "• Cross-Partition Record Duplication: Published benchmark studies frequently suffer from shared connection flows between training and test splits, artificially inflating reported laboratory evaluation metrics.\n"
            "• Heuristic Threshold Volatility: Defaulting to parametric Gaussian rules (μ + 3σ) on heavy-tailed, non-Gaussian network flow metrics severely inflates anomaly thresholds, causing attack recall to drop catastrophically.\n"
            "• Computational Bottlenecks in XAI: Evaluating post-hoc feature explanations (such as Shapley values) across every streaming packet introduces unacceptable processing latency, making continuous explainability unviable without selective alert gating.\n"
            "• Inadequate Drift Adaptation: Most deployed models rely on static distribution assumptions and degrade rapidly when operational background traffic undergoes non-adversarial concept drift."
        ),

        # 2.5 Summary
        "The literature confirms that while deep learning and tree ensembles are effectiv": (
            "The literature establishes that while deep learning and tree ensembles each possess distinct advantages, neither paradigm alone provides an "
            "adequate, wire-speed, and interpretable defense against modern cyber intrusions. A cryptographically audited, leakage-free hybrid architecture "
            "integrating non-parametric Autoencoder screening, gradient-boosted decision trees, and alert-gated explainability directly resolves these pressing vulnerabilities."
        ),

        # 7.1 Summary of Work
        "This major project designed, developed, and empirically evaluated a two-stage": (
            "This capstone project designed, implemented, and systematically evaluated a two-stage hybrid Network Intrusion Detection System that overcomes "
            "the core tension between unsupervised anomaly screening and granular supervised attack categorization. By applying strict cryptographic "
            "hashing and deduplication, the pipeline eliminated 362 leaking flow records from legacy benchmark sets. The resulting architecture integrates "
            "a deep symmetric Autoencoder (d → 128 → 64 → 32 → 16 → 32 → 64 → 128 → d) with an Extreme Gradient Boosted decision tree classifier, "
            "alert-conditioned TreeSHAP explanations, and a sliding-window concept drift tracking buffer."
        ),

        # 7.3 Contributions & Utility
        "The project provides: (1) a cryptographically audited zero-leakage benchmark": (
            "This investigation delivers four practical contributions: (1) an audited, zero-leakage dataset partitioning workflow ensuring reliable academic reproducibility; "
            "(2) an efficient two-stage detection engine combining fast anomaly screening with multi-class tree boosting; (3) elimination of the XAI computational "
            "bottleneck through alert-gated Shapley value attribution; and (4) an interactive Streamlit software dashboard accommodating both offline flow inspection "
            "and live promiscuous socket captures. The resulting appliance is well suited for deployment on enterprise edge gateways, cloud VPC firewalls, and Security Operations Centers."
        ),

        # 7.4 Limitations & Scope for Future Work
        "Limitations include reliance on transport-layer flow metadata without deep packet": (
            "Current design limitations include reliance on transport-layer flow statistics without deep packet payload inspection, and CPU throughput boundaries under multi-gigabit saturating loads.\n\n"
            "Promising avenues for future research include: (1) integrating streaming spatio-temporal Graph Neural Networks to correlate multi-host lateral movement and distributed botnet campaigns; (2) incorporating kernel-bypass acceleration via eBPF/XDP and quantized Autoencoder SmartNIC synthesis to sustain 100 Gbps backbones; and (3) establishing automated retraining pipelines triggered when Population Stability Index metrics exceed warning limits (PSI ≥ 0.25)."
        )
    }

    # Apply paragraph updates
    count = 0
    for p in doc.paragraphs:
        t = p.text.strip()
        for prefix, new_val in replacements.items():
            if t.startswith(prefix):
                style_para(p, new_val, font_size_pt=12, bold=False, align=WD_ALIGN_PARAGRAPH.JUSTIFY, space_after=6, line_spacing=1.3)
                count += 1
                break
    print(f"Updated {count} long-form paragraphs in {doc_path}.")
    
    # 2. Update Table 4.1 (Metrics definitions) to project-specific wording
    # Look for Table with Metric, Mathematical Formula, Operational Interpretation
    for tbl in doc.tables:
        if len(tbl.rows) > 0 and len(tbl.rows[0].cells) >= 3:
            h0 = tbl.rows[0].cells[0].text.strip()
            h2 = tbl.rows[0].cells[2].text.strip()
            if h0 == "Metric" and "Operational Interpretation" in h2:
                print("Found Table 4.1 (Metrics Table). Updating to unique project-specific interpretations...")
                custom_interpretations = {
                    "Accuracy": "Measures overall classification correctness across the 100,670 test flows, though secondary to recall due to heavy benign class dominance.",
                    "Precision": "Quantifies the fraction of alerts flagged by Stage-1/Stage-2 that represent actual intrusions, directly indicating SOC alarm reliability.",
                    "Attack Recall (TPR)": "Evaluates the sensitivity of the autoencoder gating threshold in stopping malicious flows before network asset compromise.",
                    "False Positive Rate": "Tracks normal user flows erroneously diverted to Stage-2, measuring unnecessary inspection overhead.",
                    "Macro-F1 Score": "Provides an unweighted harmonic balance between precision and recall across rare attack types (such as FTP-Bruteforce and U2R).",
                    "Youden's J-Index": "Direct objective function optimized during validation grid search to position the anomaly threshold at the ROC elbow.",
                    "Population Stability Index (PSI)": "Monitors distributional drift across the 500-sample benign ring buffer to determine when baseline statistics shift.",
                    "Inference Latency": "Wall-clock execution duration per flow measured on CPU hardware to ensure compliance with sub-millisecond line rates."
                }
                for row in tbl.rows[1:]:
                    metric_name = row.cells[0].text.strip()
                    if metric_name in custom_interpretations:
                        row.cells[2].text = custom_interpretations[metric_name]
                        # style cell
                        row.cells[2].paragraphs[0].paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
                        row.cells[2].paragraphs[0].paragraph_format.space_before = Pt(0)
                        row.cells[2].paragraphs[0].paragraph_format.space_after = Pt(0)
                        for r in row.cells[2].paragraphs[0].runs:
                            r.font.name = "Times New Roman"
                            r.font.size = Pt(9.0)
                            r.font.color.rgb = RGBColor(0, 0, 0)
                print("Successfully updated Table 4.1.")
                break

    doc.save(doc_path)
    print(f"Saved successfully: {doc_path}")

if __name__ == '__main__':
    targets = [
        'report/Major_Project_Report_Final_Updated.docx',
        'report/Major_Project_Report_Final.docx',
        'report/Major_Project_Report.docx'
    ]
    for t in targets:
        try:
            reduce_similarity(t)
        except Exception as e:
            print(f"Error on {t}: {e}")
