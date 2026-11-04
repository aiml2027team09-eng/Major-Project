Stop-Process -Name WINWORD -Force -ErrorAction SilentlyContinue
$word = New-Object -ComObject Word.Application
$word.Visible = $false
try {
    $doc = $word.Documents.Open('d:\Users\anshp\Final year project\Major-Project\report\Part A_26AI09.docx')
    Write-Host "Part A Sections: $($doc.Sections.Count)"
    for ($i = 1; $i -le $doc.Sections.Count; $i++) {
        $sec = $doc.Sections.Item($i)
        $ftr = $sec.Footers.Item(1) # wdHeaderFooterPrimary = 1
        $pgSetup = $sec.PageSetup
        Write-Host "Section $i`: StartingPageNumber = $($sec.Headers.Item(1).PageNumbers.StartingNumber), NumberStyle = $($sec.Headers.Item(1).PageNumbers.NumberStyle)"
        Write-Host "  Footer text: '$($ftr.Range.Text.Trim())'"
    }
    $doc.Close(0)
}
finally {
    $word.Quit()
    [System.Runtime.Interopservices.Marshal]::ReleaseComObject($word) | Out-Null
}
