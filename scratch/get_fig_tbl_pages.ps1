$docPath = "d:\Users\anshp\Final year project\Major-Project\report\Major_Project_Report_Final.docx"

$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0

try {
    $doc = $word.Documents.Open($docPath, [ref]$false, [ref]$true)
    
    $figures = @()
    $tables = @()

    foreach ($para in $doc.Paragraphs) {
        $text = $para.Range.Text.Trim()
        if ([string]::IsNullOrWhiteSpace($text)) { continue }

        if ($text -match "^Figure\s+(\d+\.\d+)\s*[:\.]?\s*(.*)") {
            $figNum = "Figure " + $matches[1]
            $figTitle = $matches[2]
            $page = $para.Range.Information(1) # wdActiveEndAdjustedPageNumber
            $figures += [PSCustomObject]@{
                Number = $figNum
                Title = $figTitle
                Page = $page
            }
        } elseif ($text -match "^Table\s+(\d+\.\d+)\s*[:\.]?\s*(.*)") {
            $tblNum = "Table " + $matches[1]
            $tblTitle = $matches[2]
            $page = $para.Range.Information(1) # wdActiveEndAdjustedPageNumber
            $tables += [PSCustomObject]@{
                Number = $tblNum
                Title = $tblTitle
                Page = $page
            }
        }
    }

    $out = [PSCustomObject]@{
        Figures = $figures
        Tables = $tables
    }

    $json = $out | ConvertTo-Json -Depth 4
    $json | Set-Content -Path "scratch/figures_tables_pages.json" -Encoding UTF8
    Write-Output "Extracted $($figures.Count) figures and $($tables.Count) tables."
}
finally {
    if ($doc) { $doc.Close([ref]$false) }
    $word.Quit()
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($word) | Out-Null
    [System.GC]::Collect()
    [System.GC]::WaitForPendingFinalizers()
}
