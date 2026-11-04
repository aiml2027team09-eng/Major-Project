param([string]$filePath = 'scratch/test_copy.docx')
Stop-Process -Name WINWORD -Force -ErrorAction SilentlyContinue
Start-Sleep -Milliseconds 200

$fullPath = Resolve-Path $filePath
$sw = [System.Diagnostics.Stopwatch]::StartNew()
$word = New-Object -ComObject Word.Application
$word.Visible = $false
try {
    Write-Host "Opening $fullPath..."
    $doc = $word.Documents.Open($fullPath.Path)
    $pages = $doc.ComputeStatistics(2)
    Write-Host "Opened successfully in $($sw.ElapsedMilliseconds) ms | Total Pages: $pages"
    $doc.Close(0)
} catch {
    Write-Error "Failed: $_"
} finally {
    $word.Quit()
    [System.Runtime.Interopservices.Marshal]::ReleaseComObject($word) | Out-Null
}
