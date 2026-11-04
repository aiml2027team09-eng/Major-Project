$docPath = "d:\Users\anshp\Final year project\Major-Project\report\Major_Project_Report_Final.docx"

$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0

try {
    $doc = $word.Documents.Open($docPath, [ref]$false, [ref]$true) # Open ReadOnly
    $pages = $doc.ComputeStatistics(2) # wdStatisticPages = 2
    Write-Output "Total pages according to Word statistics: $pages"

    $results = @()

    foreach ($para in $doc.Paragraphs) {
        $text = $para.Range.Text.Trim()
        if ([string]::IsNullOrWhiteSpace($text)) { continue }

        $isHeading = $false
        $type = ""

        if ($text -match "^CHAPTER\s+\d+") {
            $isHeading = $true
            $type = "CHAPTER"
        } elseif ($text -match "^\d+\.\d+(\.\d+)?\s+") {
            $isHeading = $true
            $type = "SECTION"
        } elseif ($text -eq "Functional & Non-Functional Requirements" -or $text -eq "Hardware & Software Requirements") {
            $isHeading = $true
            $type = "SUBSECTION"
        } elseif ($text -eq "Autoencoder Latent Topology & Manifold Projection" -or `
                  $text -eq "Sequence Diagram of Packet Ingestion and Prediction" -or `
                  $text -eq "Activity Diagram of Tiered Detection and Alert Routing" -or `
                  $text -eq "Data Flow Diagram (DFD Level-1) for Flow Processing" -or `
                  $text -eq "Class Diagram and Use Case Diagram") {
            $isHeading = $true
            $type = "SUBSECTION"
        } elseif ($text -match "^REFERENCES" -or $text -match "^APPENDICES" -or $text -match "^Appendix\s+[A-Z]") {
            $isHeading = $true
            $type = "BACKMATTER"
        } elseif ($text -match "^RESEARCH PAPER") {
            $isHeading = $true
            $type = "BACKMATTER"
        }

        if ($isHeading) {
            $pageNum = $para.Range.Information(3) # wdActiveEndPageNumber = 3
            # Also get section page number or adjusted page number
            $adjPageNum = $para.Range.Information(1) # wdActiveEndAdjustedPageNumber = 1
            $firstLine = ($text -split "`r`n|`r|`n")[0]
            if ($firstLine.Length -gt 60) { $firstLine = $firstLine.Substring(0, 60) }
            
            $results += [PSCustomObject]@{
                Type = $type
                Text = ($text -split "`r`n|`r|`n")[0]
                Page = $pageNum
                AdjPage = $adjPageNum
            }
        }
    }

    $results | Format-Table -AutoSize
    $json = $results | ConvertTo-Json -Depth 3
    $json | Set-Content -Path "scratch/toc_pages.json" -Encoding UTF8
}
finally {
    if ($doc) { $doc.Close([ref]$false) }
    $word.Quit()
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($word) | Out-Null
    [System.GC]::Collect()
    [System.GC]::WaitForPendingFinalizers()
}
