Stop-Process -Name WINWORD -Force -ErrorAction SilentlyContinue
Start-Sleep -Milliseconds 500
$word = New-Object -ComObject Word.Application
$word.Visible = $false
try {
    $doc = $word.Documents.Open('d:\Users\anshp\Final year project\Major-Project\report\Part B_26AI09.docx')
    $pagesCount = $doc.ComputeStatistics(2)
    Write-Host "Part B Total Pages: $pagesCount"

    $results = @{}
    $headingPages = @{}

    # 1. Scan paragraphs directly for Chapters, References, Appendices
    foreach ($p in $doc.Paragraphs) {
        $txt = $p.Range.Text.Trim()
        
        if ($txt -match "^CHAPTER\s+1\b") { $headingPages["1."] = $p.Range.Information(3) }
        elseif ($txt -match "^CHAPTER\s+2\b") { $headingPages["2."] = $p.Range.Information(3) }
        elseif ($txt -match "^CHAPTER\s+3\b") { $headingPages["3."] = $p.Range.Information(3) }
        elseif ($txt -match "^CHAPTER\s+4\b") { $headingPages["4."] = $p.Range.Information(3) }
        elseif ($txt -match "^CHAPTER\s+5\b") { $headingPages["5."] = $p.Range.Information(3) }
        elseif ($txt -match "^CHAPTER\s+6\b") { $headingPages["6."] = $p.Range.Information(3) }
        elseif ($txt -match "^CHAPTER\s+7\b") { $headingPages["7."] = $p.Range.Information(3) }
        elseif ($txt -eq "REFERENCES") { $headingPages["REFERENCES"] = $p.Range.Information(3) }
        elseif ($txt -eq "APPENDICES") { $headingPages["APPENDICES"] = $p.Range.Information(3) }
        elseif ($txt -match "^Appendix\s+A:") { $headingPages["Appendix A"] = $p.Range.Information(3) }
        elseif ($txt -match "^Appendix\s+B:") { $headingPages["Appendix B"] = $p.Range.Information(3) }
    }

    # 2. Search for Sections & Subsections
    $searchSections = @(
        @{ Key="1.1"; Text="1.1 Background" },
        @{ Key="1.2"; Text="1.2 Problem Statement" },
        @{ Key="1.3"; Text="1.3 Motivation / Need for the Project" },
        @{ Key="1.4"; Text="1.4 Objectives" },
        @{ Key="1.5"; Text="1.5 Scope of the Project" },
        @{ Key="1.6"; Text="1.6 Significance / Expected Contribution" },
        @{ Key="1.7"; Text="1.7 Organization of the Report" },
        
        @{ Key="2.1"; Text="2.1 Introduction" },
        @{ Key="2.2"; Text="2.2 Review of Existing Work" },
        @{ Key="2.3"; Text="2.3 Comparative Analysis" },
        @{ Key="2.4"; Text="2.4 Research / Design Gap" },
        @{ Key="2.5"; Text="2.5 Summary" },

        @{ Key="3.1"; Text="3.1 Problem Formulation" },
        @{ Key="3.2"; Text="3.2 Proposed Solution" },
        @{ Key="3.3"; Text="3.3 Requirements" },
        @{ Key="3.3.1"; Text="Functional & Non-Functional Requirements" },
        @{ Key="3.3.2"; Text="Hardware & Software Requirements" },
        @{ Key="3.4"; Text="3.4 System Architecture / Block Diagram" },
        @{ Key="3.5"; Text="3.5 Functional Components & Scope Constraints" },

        @{ Key="4.1"; Text="4.1 Objective and Method / Approach" },
        @{ Key="4.2"; Text="4.2 Measurement / Evaluation Parameters" },
        @{ Key="4.3"; Text="4.3 Model Architecture and Structural Diagrams" },
        @{ Key="4.3.1"; Text="Autoencoder Latent Topology & Manifold Projection" },
        @{ Key="4.3.2"; Text="Sequence Diagram of Packet Ingestion and Prediction" },
        @{ Key="4.3.3"; Text="Activity Diagram of Tiered Detection and Alert Routing" },
        @{ Key="4.3.4"; Text="Data Flow Diagram (DFD Level-1) for Flow Processing" },
        @{ Key="4.3.5"; Text="Class Diagram and Use Case Diagram" },
        @{ Key="4.4"; Text="4.4 Error Sources, Mitigation, and Data Processing" },

        @{ Key="5.1"; Text="5.1 Implementation Environment" },
        @{ Key="5.2"; Text="5.2 Module-wise Implementation" },
        @{ Key="5.2.1"; Text="5.2.1 Data Preparation & Cryptographic Hygiene" },
        @{ Key="5.2.2"; Text="5.2.2 Feature Preprocessing & Locked Scaling" },
        @{ Key="5.2.3"; Text="5.2.3 Autoencoder Model Training & Manifold Construction" },
        @{ Key="5.2.4"; Text="5.2.4 Validation Youden's J Threshold Optimization" },
        @{ Key="5.2.5"; Text="5.2.5 XGBoost Multi-Class Classification & Confidence Gating" },
        @{ Key="5.2.6"; Text="5.2.6 Dynamic Concept Drift Monitoring & Alert-Gated TreeSHAP" },
        @{ Key="5.3"; Text="5.3 Experimental Setup" },

        @{ Key="6.1"; Text="6.1 Quantitative Classification Results" },
        @{ Key="6.2"; Text="6.2 Confusion Matrix & Threshold Analysis" },
        @{ Key="6.3"; Text="6.3 Zero-Day Generalization & Drift Tracking" },
        @{ Key="6.4"; Text="6.4 Latency, Memory Footprint & Baseline Comparisons" },
        @{ Key="6.5"; Text="6.5 Prototype & Testing" },

        @{ Key="7.1"; Text="7.1 Summary of Work" },
        @{ Key="7.2"; Text="7.2 Conclusions" },
        @{ Key="7.3"; Text="7.3 Contributions & Utility" },
        @{ Key="7.4"; Text="7.4 Limitations & Scope for Future Work" }
    )

    foreach ($item in $searchSections) {
        $find = $doc.Content.Find
        $find.ClearFormatting()
        $found = $find.Execute($item.Text)
        if ($found) {
            $p = $find.Parent.Information(3)
            $headingPages[$item.Key] = $p
            Write-Host "Section [$($item.Key)] -> Page $p"
        } else {
            Write-Host "Section [$($item.Key)] -> NOT FOUND"
            $headingPages[$item.Key] = -1
        }
    }
    $results["headings"] = $headingPages

    # 3. Search for Figures
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
        $find = $doc.Content.Find
        $find.ClearFormatting()
        $found = $find.Execute($item.Text)
        if ($found) {
            $p = $find.Parent.Information(3)
            $figPages[$item.Key] = $p
            Write-Host "Figure [$($item.Key)] -> Page $p"
        } else {
            Write-Host "Figure [$($item.Key)] -> NOT FOUND"
            $figPages[$item.Key] = -1
        }
    }
    $results["figures"] = $figPages

    # 4. Search for Tables
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
        $find = $doc.Content.Find
        $find.ClearFormatting()
        $found = $find.Execute($item.Text)
        if ($found) {
            $p = $find.Parent.Information(3)
            $tblPages[$item.Key] = $p
            Write-Host "Table [$($item.Key)] -> Page $p"
        } else {
            Write-Host "Table [$($item.Key)] -> NOT FOUND"
            $tblPages[$item.Key] = -1
        }
    }
    $results["tables"] = $tblPages

    $jsonOut = $results | ConvertTo-Json -Depth 5
    $jsonPath = 'd:\Users\anshp\Final year project\Major-Project\scratch\part_b_pages_v2.json'
    [System.IO.File]::WriteAllText($jsonPath, $jsonOut, [System.Text.Encoding]::UTF8)
    Write-Host "Saved updated page mapping to $jsonPath"

    $doc.Close(0)
}
finally {
    $word.Quit()
    [System.Runtime.Interopservices.Marshal]::ReleaseComObject($word) | Out-Null
}
