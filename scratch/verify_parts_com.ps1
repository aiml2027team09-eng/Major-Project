Stop-Process -Name WINWORD -Force -ErrorAction SilentlyContinue
Start-Sleep -Milliseconds 300

$word = New-Object -ComObject Word.Application
$word.Visible = $false
try {
    Write-Host "Opening Part A..."
    $docA = $word.Documents.Open('d:\Users\anshp\Final year project\Major-Project\report\Part A_26AI09.docx')
    $pagesA = $docA.ComputeStatistics(2)
    Write-Host "Part A Pages: $pagesA"
    $docA.Close(0)

    Write-Host "Opening Part B..."
    $docB = $word.Documents.Open('d:\Users\anshp\Final year project\Major-Project\report\Part B_26AI09.docx')
    $pagesB = $docB.ComputeStatistics(2)
    Write-Host "Part B Pages: $pagesB"
    $docB.Close(0)
    
    Write-Host "Verification completed successfully!"
} catch {
    Write-Error "Error: $_"
} finally {
    $word.Quit()
    [System.Runtime.Interopservices.Marshal]::ReleaseComObject($word) | Out-Null
}
