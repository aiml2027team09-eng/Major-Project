$word = New-Object -ComObject Word.Application
$word.Visible = $false
try {
    $doc = $word.Documents.Open('d:\Users\anshp\Final year project\Major-Project\report\Part B_26AI09.docx', $false, $true) # ReadOnly
    
    Write-Host "Total Pages: $($doc.ComputeStatistics(2))"
    
    # Check paragraphs 1 to 30
    for ($i = 1; $i -le 30; $i++) {
        $p = $doc.Paragraphs.Item($i)
        $txt = $p.Range.Text.Trim()
        if ($txt.Length -gt 50) { $txt = $txt.Substring(0, 50) + "..." }
        $page = $p.Range.Information(3)
        Write-Host "P $i [Page $page]: $txt"
    }
    
    $doc.Close($false)
} finally {
    $word.Quit()
    [System.Runtime.Interopservices.Marshal]::ReleaseComObject($word) | Out-Null
}
