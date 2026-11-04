Stop-Process -Name WINWORD -Force -ErrorAction SilentlyContinue
Start-Sleep -Milliseconds 300

$word = New-Object -ComObject Word.Application
$word.Visible = $true
$word.DisplayAlerts = 0

try {
    Write-Host "Opening report/Part B_26AI09.docx..."
    $doc = $word.Documents.Open('d:\Users\anshp\Final year project\Major-Project\report\Part B_26AI09.docx', $false, $true)
    Write-Host "Success! Pages: $($doc.ComputeStatistics(2))"
    $doc.Close(0)
} catch {
    Write-Error "Error: $_"
} finally {
    $word.Quit()
    [System.Runtime.Interopservices.Marshal]::ReleaseComObject($word) | Out-Null
}
