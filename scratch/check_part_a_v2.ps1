Stop-Process -Name WINWORD -Force -ErrorAction SilentlyContinue
$word = New-Object -ComObject Word.Application
$word.Visible = $false
try {
    $docA = $word.Documents.Open('d:\Users\anshp\Final year project\Major-Project\report\Part A_26AI09.docx')
    Write-Host "Part A Total Pages: $($docA.ComputeStatistics(2))"
    Write-Host "Part A Sections Count: $($docA.Sections.Count)"
    for ($i = 1; $i -le $docA.Sections.Count; $i++) {
        $sec = $docA.Sections.Item($i)
        $ftr = $sec.Footers.Item(1)
        Write-Host "Section $i`: Start=$($sec.Headers.Item(1).PageNumbers.StartingNumber), Style=$($sec.Headers.Item(1).PageNumbers.NumberStyle) (2=lowerRoman), Footer='$($ftr.Range.Text.Trim())'"
    }
    $docA.Close(0)
}
finally {
    $word.Quit()
    [System.Runtime.Interopservices.Marshal]::ReleaseComObject($word) | Out-Null
}
