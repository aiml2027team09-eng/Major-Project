Stop-Process -Name WINWORD -Force -ErrorAction SilentlyContinue
$word = New-Object -ComObject Word.Application
$word.Visible = $false
try {
    $doc = $word.Documents.Open('d:\Users\anshp\Final year project\Major-Project\report\Part B_26AI09.docx')
    $paraIndices = @(0, 48, 74, 132, 178, 229, 293, 304, 331)
    
    foreach ($idx in $paraIndices) {
        $p = $doc.Paragraphs.Item($idx + 1) # 1-indexed in Word COM
        $pageNum = $p.Range.Information(3)
        $txt = $p.Range.Text.Trim().Replace("`r", " ").Replace("`n", " ")
        Write-Host "Para $idx ($pageNum): '$txt'"
    }
    $doc.Close(0)
}
finally {
    $word.Quit()
    [System.Runtime.Interopservices.Marshal]::ReleaseComObject($word) | Out-Null
}
