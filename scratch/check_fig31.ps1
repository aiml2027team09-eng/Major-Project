$docPath = 'd:\Users\anshp\Final year project\Major-Project\report\Major_Project_Report_Final.docx'
$word = New-Object -ComObject Word.Application
$word.Visible = $false
try {
    $doc = $word.Documents.Open($docPath, [ref]$false, [ref]$true)
    foreach ($p in $doc.Paragraphs) {
        $t = $p.Range.Text.Trim()
        if ($t -match '^Figure 3\.1') {
            $isTable = $p.Range.Tables.Count -gt 0
            Write-Output ("Text: " + $t + " | InTable: " + $isTable + " | Page: " + $p.Range.Information(1))
        }
    }
}
finally {
    if ($doc) { $doc.Close([ref]$false) }
    $word.Quit()
}
