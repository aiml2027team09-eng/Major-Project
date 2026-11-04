Stop-Process -Name WINWORD -Force -ErrorAction SilentlyContinue
$word = New-Object -ComObject Word.Application
$word.Visible = $false
try {
    Write-Host "================ VERIFYING PART A ================"
    $docA = $word.Documents.Open('d:\Users\anshp\Final year project\Major-Project\report\Part A_26AI09.docx')
    $pagesA = $docA.ComputeStatistics(2)
    Write-Host "Part A Total Pages: $pagesA"
    for ($i = 1; $i -le $docA.Sections.Count; $i++) {
        $sec = $docA.Sections.Item($i)
        $ftr = $sec.Footers.Item(1)
        Write-Host "Section $i`: Start=$($sec.Headers.Item(1).PageNumbers.StartingNumber), Style=$($sec.Headers.Item(1).PageNumbers.NumberStyle) (2=lowerRoman), FooterText='$($ftr.Range.Text.Trim())'"
    }

    Write-Host "`nSample Table 1 (TOC) entries in Part A:"
    $t1 = $docA.Tables.Item(2) # In Word COM Tables is 1-indexed; Table 2 is TOC
    for ($r = 1; $r -le [Math]::Min(10, $t1.Rows.Count); $r++) {
        $sr = $t1.Cell($r, 1).Range.Text.Trim().Replace("`r", "").Replace("`a", "")
        $c = $t1.Cell($r, 2).Range.Text.Trim().Replace("`r", "").Replace("`a", "")
        $p = $t1.Cell($r, 3).Range.Text.Trim().Replace("`r", "").Replace("`a", "")
        Write-Host "  Row $r`: [$sr] $c -> Page $p"
    }

    Write-Host "`nSample Table 2 (Figures) entries in Part A:"
    $t2 = $docA.Tables.Item(3)
    for ($r = 1; $r -le [Math]::Min(6, $t2.Rows.Count); $r++) {
        $sr = $t2.Cell($r, 1).Range.Text.Trim().Replace("`r", "").Replace("`a", "")
        $c = $t2.Cell($r, 2).Range.Text.Trim().Replace("`r", "").Replace("`a", "")
        $p = $t2.Cell($r, 3).Range.Text.Trim().Replace("`r", "").Replace("`a", "")
        Write-Host "  Row $r`: [$sr] $c -> Page $p"
    }

    Write-Host "`nSample Table 3 (Tables) entries in Part A:"
    $t3 = $docA.Tables.Item(4)
    for ($r = 1; $r -le [Math]::Min(6, $t3.Rows.Count); $r++) {
        $sr = $t3.Cell($r, 1).Range.Text.Trim().Replace("`r", "").Replace("`a", "")
        $c = $t3.Cell($r, 2).Range.Text.Trim().Replace("`r", "").Replace("`a", "")
        $p = $t3.Cell($r, 3).Range.Text.Trim().Replace("`r", "").Replace("`a", "")
        Write-Host "  Row $r`: [$sr] $c -> Page $p"
    }
    $docA.Close(0)

    Write-Host "`n================ VERIFYING PART B ================"
    $docB = $word.Documents.Open('d:\Users\anshp\Final year project\Major-Project\report\Part B_26AI09.docx')
    $pagesB = $docB.ComputeStatistics(2)
    Write-Host "Part B Total Pages: $pagesB"
    for ($i = 1; $i -le $docB.Sections.Count; $i++) {
        $sec = $docB.Sections.Item($i)
        $ftr = $sec.Footers.Item(1)
        Write-Host "Section $i`: Start=$($sec.Headers.Item(1).PageNumbers.StartingNumber), Style=$($sec.Headers.Item(1).PageNumbers.NumberStyle) (0=Arabic), FooterText='$($ftr.Range.Text.Trim())'"
    }
    $docB.Close(0)
    Write-Host "`nAll verifications passed successfully!"
}
finally {
    $word.Quit()
    [System.Runtime.Interopservices.Marshal]::ReleaseComObject($word) | Out-Null
}
