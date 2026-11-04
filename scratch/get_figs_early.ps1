$docPath = 'd:\Users\anshp\Final year project\Major-Project\report\Major_Project_Report_Final.docx'
$word = New-Object -ComObject Word.Application
$word.Visible = $false
try {
    $doc = $word.Documents.Open($docPath, [ref]$false, [ref]$true)
    foreach ($p in $doc.Paragraphs) {
        $t = $p.Range.Text.Trim()
        if ($t -match '^Figure (3\.1|4\.1|4\.2|4\.3)') {
            Write-Output ($t + ' --> Page: ' + $p.Range.Information(1))
        }
    }
}
finally {
    if ($doc) { $doc.Close([ref]$false) }
    $word.Quit()
}
