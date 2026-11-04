Stop-Process -Name WINWORD -Force -ErrorAction SilentlyContinue
Start-Sleep -Milliseconds 300

$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
try {
    Write-Host "Opening Part B with DisplayAlerts=0..."
    $doc = $word.Documents.Open('d:\Users\anshp\Final year project\Major-Project\report\Part B_26AI09.docx')
    Write-Host "Success! Total pages: $($doc.ComputeStatistics(2))"
    $doc.Close(0)
} catch {
    Write-Error "Failed: $_"
} finally {
    $word.Quit()
    [System.Runtime.Interopservices.Marshal]::ReleaseComObject($word) | Out-Null
}
