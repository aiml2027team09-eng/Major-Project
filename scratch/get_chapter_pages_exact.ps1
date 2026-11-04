Stop-Process -Name WINWORD -Force -ErrorAction SilentlyContinue
Start-Sleep -Milliseconds 300

$word = New-Object -ComObject Word.Application
$word.Visible = $false
try {
    $doc = $word.Documents.Open('d:\Users\anshp\Final year project\Major-Project\report\Major_Project_Report_Final_Updated.docx')
    $offset = 11
    $targets = @('CHAPTER 1', 'CHAPTER 2', 'CHAPTER 3', 'CHAPTER 4', 'CHAPTER 5', 'CHAPTER 6', 'CHAPTER 7', 'REFERENCES', 'APPENDICES')
    foreach ($p in $doc.Paragraphs) {
        $txt = $p.Range.Text.Trim()
        if ($p.Range.Start -gt 12000) {
            foreach ($target in $targets) {
                if ($txt.StartsWith($target)) {
                    $mp = $p.Range.Information(3)
                    $pp = $mp - $offset
                    Write-Host "$target -> Master Page $mp , Part B Page $pp"
                }
            }
        }
    }
    $doc.Close(0)
} finally {
    $word.Quit()
    [System.Runtime.Interopservices.Marshal]::ReleaseComObject($word) | Out-Null
}
