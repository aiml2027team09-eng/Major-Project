Stop-Process -Name WINWORD -Force -ErrorAction SilentlyContinue
Start-Sleep -Milliseconds 500

$word = New-Object -ComObject Word.Application
$word.Visible = $false
try {
    Write-Host "Opening master document..."
    $doc = $word.Documents.Open('d:\Users\anshp\Final year project\Major-Project\report\Major_Project_Report_Final_Updated.docx')
    $pagesCount = $doc.ComputeStatistics(2)
    Write-Host "Master Total Pages: $pagesCount"
    
    # Locate Chapter 1 in body (skip preliminary pages / TOC)
    $ch1Paragraph = $null
    foreach ($p in $doc.Paragraphs) {
        if ($p.Range.Text -match "^CHAPTER\s+1\b") {
            $ch1Paragraph = $p
            break
        }
    }
    
    if ($ch1Paragraph -eq $null) {
        Write-Error "Could not find Chapter 1 paragraph in body!"
        exit 1
    }
    
    $bodyStart = $ch1Paragraph.Range.Start
    $bodyEnd = $doc.Content.End
    $ch1MasterPage = $ch1Paragraph.Range.Information(3)
    Write-Host "Chapter 1 found at Character $bodyStart, Master Page: $ch1MasterPage"
    
    # In Part B, Chapter 1 is page 1.
    # So offset = ch1MasterPage - 1
    $offset = $ch1MasterPage - 1
    Write-Host "Preliminary pages offset: $offset (Part B Page = Master Page - $offset)"

    $results = @{}
    $headingPages = @{}

    $searchSections = @(
        @{ Key="1."; Text="CHAPTER 1" },
        @{ Key="1.1"; Text="1.1 Background" },
        @{ Key="1.2"; Text="1.2 Problem Statement" },
        @{ Key="1.3"; Text="1.3 Motivation / Need for the Project" },
        @{ Key="1.4"; Text="1.4 Objectives" },
        @{ Key="1.5"; Text="1.5 Scope of the Project" },
        @{ Key="1.6"; Text="1.6 Significance / Expected Contribution" },
        @{ Key="1.7"; Text="1.7 Organization of the Report" },
        
        @{ Key="2."; Text="CHAPTER 2" },
        @{ Key="2.1"; Text="2.1 Introduction" },
        @{ Key="2.2"; Text="2.2 Review of Existing Work" },
        @{ Key="2.3"; Text="2.3 Comparative Analysis" },
        @{ Key="2.4"; Text="2.4 Research / Design Gap" },
        @{ Key="2.5"; Text="2.5 Summary" },

        @{ Key="3."; Text="CHAPTER 3" },
        @{ Key="3.1"; Text="3.1 Problem Formulation" },
        @{ Key="3.2"; Text="3.2 Proposed Solution" },
        @{ Key="3.3"; Text="3.3 Requirements" },
        @{ Key="3.3.1"; Text="Functional & Non-Functional Requirements" },
        @{ Key="3.3.2"; Text="Hardware & Software Requirements" },
        @{ Key="3.4"; Text="3.4 System Architecture / Block Diagram" },
        @{ Key="3.5"; Text="3.5 Functional Components & Scope Constraints" },

        @{ Key="4."; Text="CHAPTER 4" },
        @{ Key="4.1"; Text="4.1 Objective and Method / Approach" },
        @{ Key="4.2"; Text="4.2 Measurement / Evaluation Parameters" },
        @{ Key="4.3"; Text="4.3 Model Architecture and Structural Diagrams" },
        @{ Key="4.3.1"; Text="Autoencoder Latent Topology & Manifold Projection" },
        @{ Key="4.3.2"; Text="Sequence Diagram of Packet Ingestion and Prediction" },
        @{ Key="4.3.3"; Text="Activity Diagram of Tiered Detection and Alert Routing" },
        @{ Key="4.3.4"; Text="Data Flow Diagram (DFD Level-1) for Flow Processing" },
        @{ Key="4.3.5"; Text="Class Diagram and Use Case Diagram" },
        @{ Key="4.4"; Text="4.4 Error Sources, Mitigation, and Data Processing" },

        @{ Key="5."; Text="CHAPTER 5" },
        @{ Key="5.1"; Text="5.1 Implementation Environment" },
        @{ Key="5.2"; Text="5.2 Module-wise Implementation" },
        @{ Key="5.2.1"; Text="5.2.1 Data Preparation & Cryptographic Hygiene" },
        @{ Key="5.2.2"; Text="5.2.2 Feature Preprocessing & Locked Scaling" },
        @{ Key="5.2.3"; Text="5.2.3 Autoencoder Model Training & Manifold Construction" },
        @{ Key="5.2.4"; Text="5.2.4 Validation Youden's J Threshold Optimization" },
        @{ Key="5.2.5"; Text="5.2.5 XGBoost Multi-Class Classification & Confidence Gating" },
        @{ Key="5.2.6"; Text="5.2.6 Dynamic Concept Drift Monitoring & Alert-Gated TreeSHAP" },
        @{ Key="5.3"; Text="5.3 Experimental Setup" },

        @{ Key="6."; Text="CHAPTER 6" },
        @{ Key="6.1"; Text="6.1 Quantitative Classification Results" },
        @{ Key="6.2"; Text="6.2 Confusion Matrix & Threshold Analysis" },
        @{ Key="6.3"; Text="6.3 Zero-Day Generalization & Drift Tracking" },
        @{ Key="6.4"; Text="6.4 Latency, Memory Footprint & Baseline Comparisons" },
        @{ Key="6.5"; Text="6.5 Prototype & Testing" },

        @{ Key="7."; Text="CHAPTER 7" },
        @{ Key="7.1"; Text="7.1 Summary of Work" },
        @{ Key="7.2"; Text="7.2 Conclusions" },
        @{ Key="7.3"; Text="7.3 Contributions & Utility" },
        @{ Key="7.4"; Text="7.4 Limitations & Scope for Future Work" },
        
        @{ Key="REFERENCES"; Text="REFERENCES" },
        @{ Key="APPENDICES"; Text="APPENDICES" },
        @{ Key="Appendix A"; Text="Appendix A: Mathematical Derivations" },
        @{ Key="Appendix B"; Text="Appendix B: Scapy Live Packet Sniffing" }
    )

    foreach ($item in $searchSections) {
        $searchRange = $doc.Range($bodyStart, $bodyEnd)
        $find = $searchRange.Find
        $find.ClearFormatting()
        if ($find.Execute($item.Text)) {
            $mPage = $searchRange.Information(3)
            $pPage = [Math]::Max(1, $mPage - $offset)
            $headingPages[$item.Key] = $pPage
            Write-Host "Heading [$($item.Key)] -> Master Page $mPage | Part B Page $pPage"
        } else {
            Write-Host "Heading [$($item.Key)] -> NOT FOUND!" -ForegroundColor Red
        }
    }
    $results["headings"] = $headingPages

    $searchFigures = @(
        @{ Key="Figure 3.1"; Text="Figure 3.1:" },
        @{ Key="Figure 4.1"; Text="Figure 4.1:" },
        @{ Key="Figure 4.2"; Text="Figure 4.2:" },
        @{ Key="Figure 4.3"; Text="Figure 4.3:" },
        @{ Key="Figure 4.4"; Text="Figure 4.4:" },
        @{ Key="Figure 4.5"; Text="Figure 4.5:" },
        @{ Key="Figure 6.1"; Text="Figure 6.1:" },
        @{ Key="Figure 6.2"; Text="Figure 6.2:" },
        @{ Key="Figure 6.3"; Text="Figure 6.3:" },
        @{ Key="Figure 6.4"; Text="Figure 6.4:" },
        @{ Key="Figure 6.5"; Text="Figure 6.5:" },
        @{ Key="Figure 6.6"; Text="Figure 6.6:" },
        @{ Key="Figure 6.7"; Text="Figure 6.7:" },
        @{ Key="Figure 6.8"; Text="Figure 6.8:" },
        @{ Key="Figure 6.9"; Text="Figure 6.9:" }
    )
    $figPages = @{}
    foreach ($item in $searchFigures) {
        $searchRange = $doc.Range($bodyStart, $bodyEnd)
        $find = $searchRange.Find
        $find.ClearFormatting()
        if ($find.Execute($item.Text)) {
            $mPage = $searchRange.Information(3)
            $pPage = [Math]::Max(1, $mPage - $offset)
            $figPages[$item.Key] = $pPage
            Write-Host "Figure [$($item.Key)] -> Master Page $mPage | Part B Page $pPage"
        } else {
            Write-Host "Figure [$($item.Key)] -> NOT FOUND!" -ForegroundColor Red
        }
    }
    $results["figures"] = $figPages

    $searchTables = @(
        @{ Key="Table 2.1"; Text="Table 2.1: Comparison of Existing" },
        @{ Key="Table 4.1"; Text="Table 4.1: Measurement and Evaluation" },
        @{ Key="Table 4.2"; Text="Table 4.2: Autoencoder Bottleneck" },
        @{ Key="Table 5.1"; Text="Table 5.1: Cryptographically Audited" },
        @{ Key="Table 5.2"; Text="Table 5.2: Experimental Setup Parameters" },
        @{ Key="Table 5.3"; Text="Table 5.3: System Test Cases" },
        @{ Key="Table 6.1"; Text="Table 6.1: Overall Classification Performance" },
        @{ Key="Table 6.2"; Text="Table 6.2: Multi-Class Attack Detection Breakdown on CICIDS2018" },
        @{ Key="Table 6.3"; Text="Table 6.3: Multi-Class Attack Detection Breakdown on NSL-KDD" },
        @{ Key="Table 6.4"; Text="Table 6.4: Reconstruction Threshold Strategy Comparison" },
        @{ Key="Table 6.5"; Text="Table 6.5: Leave-One-Attack-Out" },
        @{ Key="Table 6.6"; Text="Table 6.6: Statistical Concept Drift Tracking" },
        @{ Key="Table 6.7"; Text="Table 6.7: Computational Benchmark" },
        @{ Key="Table 6.8"; Text="Table 6.8: Benchmark Comparison Against Baseline" }
    )
    $tblPages = @{}
    foreach ($item in $searchTables) {
        $searchRange = $doc.Range($bodyStart, $bodyEnd)
        $find = $searchRange.Find
        $find.ClearFormatting()
        if ($find.Execute($item.Text)) {
            $mPage = $searchRange.Information(3)
            $pPage = [Math]::Max(1, $mPage - $offset)
            $tblPages[$item.Key] = $pPage
            Write-Host "Table [$($item.Key)] -> Master Page $mPage | Part B Page $pPage"
        } else {
            Write-Host "Table [$($item.Key)] -> NOT FOUND!" -ForegroundColor Red
        }
    }
    $results["tables"] = $tblPages

    $jsonOut = $results | ConvertTo-Json -Depth 5
    $jsonPath = 'd:\Users\anshp\Final year project\Major-Project\scratch\part_b_pages_v3.json'
    [System.IO.File]::WriteAllText($jsonPath, $jsonOut, [System.Text.Encoding]::UTF8)
    Write-Host "Saved updated page mapping to $jsonPath"

    $doc.Close(0)
} finally {
    $word.Quit()
    [System.Runtime.Interopservices.Marshal]::ReleaseComObject($word) | Out-Null
}
