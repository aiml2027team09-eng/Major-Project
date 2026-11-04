Stop-Process -Name WINWORD -Force -ErrorAction SilentlyContinue
$word = New-Object -ComObject Word.Application
$word.Visible = $false
try {
    $doc = $word.Documents.Open('d:\Users\anshp\Final year project\Major-Project\report\Part B_26AI09.docx')
    Write-Host "Scanning all paragraphs in Part B for Chapter and Backmatter headings..."
    
    for ($i = 1; $i -le $doc.Paragraphs.Count; $i++) {
        $p = $doc.Paragraphs.Item($i)
        $txt = $p.Range.Text.Trim()
        
        # Match CHAPTER 1..7, REFERENCES, APPENDICES, Appendix A, Appendix B
        if ($txt -match "^CHAPTER\s+\d+" -or $txt -eq "REFERENCES" -or $txt -eq "APPENDICES" -or $txt -match "^Appendix\s+[AB]:") {
            $pageNum = $p.Range.Information(3) # wdActiveEndPageNumber
            Write-Host "P$i [Page $pageNum]: '$txt'"
        }
    }
    $doc.Close(0)
}
finally {
    $word.Quit()
    [System.Runtime.Interopservices.Marshal]::ReleaseComObject($word) | Out-Null
}
