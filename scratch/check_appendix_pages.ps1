$word = New-Object -ComObject Word.Application
$word.Visible = $false
try {
    $doc = $word.Documents.Open('d:\Users\anshp\Final year project\Major-Project\report\Part B_26AI09.docx')
    $find = $doc.Content.Find
    $find.ClearFormatting()
    if ($find.Execute("Appendix B: Scapy Live Packet Sniffing")) {
        Write-Host "Found Appendix B on page: $($find.Parent.Information(3))"
    } else {
        Write-Host "Appendix B NOT FOUND via Find"
    }
    if ($find.Execute("Listing B.1: Real-Time Promiscuous")) {
        Write-Host "Found Listing B.1 on page: $($find.Parent.Information(3))"
    }
    $doc.Close(0)
} finally {
    $word.Quit()
    [System.Runtime.Interopservices.Marshal]::ReleaseComObject($word) | Out-Null
}
