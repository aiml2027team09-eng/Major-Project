$word = New-Object -ComObject Word.Application
$word.Visible = $false
try {
    $doc = $word.Documents.Open('d:\Users\anshp\Final year project\Major-Project\report\Part B_26AI09.docx')
    $idx = 0
    foreach ($p in $doc.Paragraphs) {
        $idx++
        $txt = $p.Range.Text.Trim()
        if ($idx -le 25 -or $txt -match "Listing B\.1" -or $txt -match "Appendix B") {
            $page = $p.Range.Information(3)
            $vert = $p.Range.Information(6)
            $disp = $txt
            if ($disp.Length -gt 45) { $disp = $disp.Substring(0, 45) + "..." }
            Write-Host "P $idx [Page $page, Vert $vert pt]: $disp"
        }
    }
    $doc.Close(0)
} finally {
    $word.Quit()
    [System.Runtime.Interopservices.Marshal]::ReleaseComObject($word) | Out-Null
}
