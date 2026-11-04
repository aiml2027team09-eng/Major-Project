Stop-Process -Name WINWORD -Force -ErrorAction SilentlyContinue
$word = New-Object -ComObject Word.Application
$word.Visible = $false
try {
    $docA = $word.Documents.Open('d:\Users\anshp\Final year project\Major-Project\report\Part A_26AI09.docx')
    $pagesA = $docA.ComputeStatistics(2) # 2 = wdStatisticPages
    Write-Host "Part A Pages count: $pagesA"
    $docA.Close(0)

    $docB = $word.Documents.Open('d:\Users\anshp\Final year project\Major-Project\report\Part B_26AI09.docx')
    $pagesB = $docB.ComputeStatistics(2)
    Write-Host "Part B Pages count: $pagesB"
    $docB.Close(0)
}
finally {
    $word.Quit()
    [System.Runtime.Interopservices.Marshal]::ReleaseComObject($word) | Out-Null
}
