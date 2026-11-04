$word = New-Object -ComObject Word.Application
$word.Visible = $false
try {
    Write-Host "Opening Master doc..."
    $doc = $word.Documents.Open('d:\Users\anshp\Final year project\Major-Project\report\Major_Project_Report_Final_Updated.docx')
    Write-Host "Master opened! Pages: $($doc.ComputeStatistics(2))"
    $doc.Close(0)
} catch {
    Write-Host "ERROR: $_"
} finally {
    $word.Quit()
    [System.Runtime.Interopservices.Marshal]::ReleaseComObject($word) | Out-Null
}
