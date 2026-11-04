Stop-Process -Name WINWORD -Force -ErrorAction SilentlyContinue
Start-Sleep -Milliseconds 300

$word = New-Object -ComObject Word.Application
$word.Visible = $false
try {
    $files = @(
        'd:\Users\anshp\Final year project\Major-Project\report\CISC_2026_Research_Paper_DoubleBlind.docx',
        'd:\Users\anshp\Final year project\Major-Project\report\CISC_2026_Research_Paper_CameraReady.docx'
    )
    foreach ($f in $files) {
        $pdfPath = $f.Substring(0, $f.LastIndexOf('.')) + ".pdf"
        Write-Host "Exporting $f to $pdfPath..."
        $doc = $word.Documents.Open($f)
        # 17 corresponds to wdFormatPDF
        $doc.SaveAs([ref]$pdfPath, [ref]17)
        $doc.Close(0)
        Write-Host "Successfully generated: $pdfPath"
    }
} catch {
    Write-Error "PDF Export Error: $_"
} finally {
    $word.Quit()
    [System.Runtime.Interopservices.Marshal]::ReleaseComObject($word) | Out-Null
}
