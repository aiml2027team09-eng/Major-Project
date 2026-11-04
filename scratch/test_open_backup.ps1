$word = New-Object -ComObject Word.Application
$word.Visible = $false
try {
    Write-Host "Opening backup..."
    $doc = $word.Documents.Open('d:\Users\anshp\Final year project\Major-Project\report\Part B_26AI09_backup.docx')
    Write-Host "Backup opened successfully! Pages: $($doc.ComputeStatistics(2))"
    $doc.Close(0)
} catch {
    Write-Host "ERROR: $_"
} finally {
    $word.Quit()
    [System.Runtime.Interopservices.Marshal]::ReleaseComObject($word) | Out-Null
}
