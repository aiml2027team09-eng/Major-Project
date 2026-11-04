Write-Host "Step 1: Creating Word application..."
$word = New-Object -ComObject Word.Application
$word.Visible = $false
try {
    Write-Host "Step 2: Opening Part B..."
    $doc = $word.Documents.Open('d:\Users\anshp\Final year project\Major-Project\report\Part B_26AI09.docx')
    Write-Host "Step 3: Document opened successfully!"
    $pages = $doc.ComputeStatistics(2)
    Write-Host "Step 4: Part B Total Pages: $pages"
    $doc.Close(0)
    Write-Host "Step 5: Document closed."
} catch {
    Write-Host "ERROR: $_"
} finally {
    $word.Quit()
    [System.Runtime.Interopservices.Marshal]::ReleaseComObject($word) | Out-Null
    Write-Host "Step 6: Word quit."
}
