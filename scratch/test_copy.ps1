Stop-Process -Name WINWORD -Force -ErrorAction SilentlyContinue
Start-Sleep -Milliseconds 300

Copy-Item 'report/Major_Project_Report_Final_Updated.docx' 'scratch/test_copy.docx' -Force
$sw = [System.Diagnostics.Stopwatch]::StartNew()
$word = New-Object -ComObject Word.Application
$word.Visible = $false
try {
    Write-Host "Opening test_copy..."
    $doc = $word.Documents.Open('d:\Users\anshp\Final year project\Major-Project\scratch\test_copy.docx')
    Write-Host "Opened successfully in $($sw.ElapsedMilliseconds) ms"
    $doc.Close(0)
} finally {
    $word.Quit()
    [System.Runtime.Interopservices.Marshal]::ReleaseComObject($word) | Out-Null
}
