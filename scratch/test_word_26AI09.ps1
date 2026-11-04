$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0

try {
    foreach ($file in @('Part A_26AI09.docx', 'Part B_26AI09.docx')) {
        $path = "d:\Users\anshp\Final year project\Major-Project\report\" + $file
        $doc = $word.Documents.Open($path, [ref]$false, [ref]$true)
        $pages = $doc.ComputeStatistics(2) # wdStatisticPages
        $words = $doc.ComputeStatistics(0) # wdStatisticWords
        $paras = $doc.Paragraphs.Count
        Write-Output ("FILE: " + $file + " | Pages: " + $pages + " | Words: " + $words + " | Paras: " + $paras)
        
        $secIdx = 0
        foreach ($sec in $doc.Sections) {
            $secIdx++
            $hChars = $sec.Headers.Item(1).Range.Text.Trim().Length
            $fChars = $sec.Footers.Item(1).Range.Text.Trim().Length
            Write-Output ("  Sec " + $secIdx + " header chars: " + $hChars + " | footer chars: " + $fChars)
        }
        $doc.Close([ref]$false)
    }
}
finally {
    $word.Quit()
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($word) | Out-Null
}
