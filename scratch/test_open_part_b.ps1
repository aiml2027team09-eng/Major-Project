Stop-Process -Name WINWORD -Force -ErrorAction SilentlyContinue
Start-Sleep -Milliseconds 300

$sw = [System.Diagnostics.Stopwatch]::StartNew()
$word = New-Object -ComObject Word.Application
$word.Visible = $false
try {
    Write-Host "Starting open..."
    $doc = $word.Documents.Open('d:\Users\anshp\Final year project\Major-Project\report\Part B_26AI09.docx')
    Write-Host "Opened in $($sw.ElapsedMilliseconds) ms"
    $pages = $doc.ComputeStatistics(2)
    Write-Host "Total pages: $pages in $($sw.ElapsedMilliseconds) ms"
    $doc.Close(0)
} catch {
    Write-Error "Error opening Part B: $_"
} finally {
    $word.Quit()
    [System.Runtime.Interopservices.Marshal]::ReleaseComObject($word) | Out-Null
}
