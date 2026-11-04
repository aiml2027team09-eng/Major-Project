Stop-Process -Name WINWORD -Force -ErrorAction SilentlyContinue
$word = New-Object -ComObject Word.Application
$word.Visible = $false
try {
    $docB = $word.Documents.Open('d:\Users\anshp\Final year project\Major-Project\report\Part B_26AI09.docx')
    Write-Host "Part B Sections: $($docB.Sections.Count)"
    for ($i = 1; $i -le $docB.Sections.Count; $i++) {
        $sec = $docB.Sections.Item($i)
        $ftr = $sec.Footers.Item(1)
        Write-Host "Section $i`: StartingPageNumber = $($sec.Headers.Item(1).PageNumbers.StartingNumber), NumberStyle = $($sec.Headers.Item(1).PageNumbers.NumberStyle)"
        Write-Host "  Footer text: '$($ftr.Range.Text.Trim())'"
    }
    $pages = $docB.ComputeStatistics(2)
    Write-Host "Part B Total Pages: $pages"
    $docB.Close(0)
}
finally {
    $word.Quit()
    [System.Runtime.Interopservices.Marshal]::ReleaseComObject($word) | Out-Null
}
