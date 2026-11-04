$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0

try {
    foreach ($file in @('Part A_26AI01.docx', 'Part B_26AI01.docx')) {
        $path = "d:\Users\anshp\Final year project\Major-Project\report\" + $file
        $doc = $word.Documents.Open($path, [ref]$false, [ref]$true)
        $pages = $doc.ComputeStatistics(2) # wdStatisticPages
        $words = $doc.ComputeStatistics(0) # wdStatisticWords
        Write-Output ("File: " + $file + " | Pages: " + $pages + " | Words: " + $words)
        
        # Verify headers/footers in sections
        foreach ($sec in $doc.Sections) {
            $hCount = $sec.Headers.Item(1).Range.Text.Trim().Length
            $fCount = $sec.Footers.Item(1).Range.Text.Trim().Length
            Write-Output ("  Section header chars: " + $hCount + " | footer chars: " + $fCount)
        }
        $doc.Close([ref]$false)
    }
}
finally {
    $word.Quit()
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($word) | Out-Null
}
