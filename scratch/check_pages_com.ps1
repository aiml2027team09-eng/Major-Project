$word = New-Object -ComObject Word.Application
$word.Visible = $false
try {
    $doc = $word.Documents.Open('d:\Users\anshp\Final year project\Major-Project\report\Part B_26AI09.docx')
    Write-Host "Total Pages: $($doc.ComputeStatistics(2))"
    
    # 1. Section 1.3 and 1.4
    $find = $doc.Content.Find
    $find.ClearFormatting()
    if ($find.Execute("1.3 Motivation")) {
        Write-Host "1.3 Motivation -> Page $($find.Parent.Information(3)), Vert $($find.Parent.Information(6)) pt"
    }
    if ($find.Execute("1.4 Objectives")) {
        Write-Host "1.4 Objectives -> Page $($find.Parent.Information(3)), Vert $($find.Parent.Information(6)) pt"
    }
    if ($find.Execute("Listing B.1 provides")) {
        Write-Host "Listing B.1 intro -> Page $($find.Parent.Information(3)), Vert $($find.Parent.Information(6)) pt"
    }
    if ($find.Execute("Listing B.1: Real-Time")) {
        Write-Host "Listing B.1 title -> Page $($find.Parent.Information(3)), Vert $($find.Parent.Information(6)) pt"
    }
    $doc.Close(0)
} finally {
    $word.Quit()
    [System.Runtime.Interopservices.Marshal]::ReleaseComObject($word) | Out-Null
}
