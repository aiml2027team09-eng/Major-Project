Stop-Process -Name WINWORD -Force -ErrorAction SilentlyContinue
$word = New-Object -ComObject Word.Application
$word.Visible = $false
try {
    $doc = $word.Documents.Open('d:\Users\anshp\Final year project\Major-Project\report\Part A_26AI09.docx')
    $pages = $doc.ComputeStatistics(2)
    Write-Host "Total Pages in Part A: $pages"
    
    # Check what headings are on which page
    $headings = @("PROJECT REPORT", "CERTIFICATE", "DECLARATION", "ACKNOWLEDGEMENT", "ABSTRACT", "TABLE OF CONTENTS", "LIST OF FIGURES", "LIST OF TABLES", "ABBREVIATIONS")
    foreach ($h in $headings) {
        $find = $doc.Content.Find
        $find.ClearFormatting()
        $found = $find.Execute($h)
        if ($found) {
            $pageNum = $find.Parent.Information(3) # 3 = wdActiveEndPageNumber
            Write-Host "$h -> Page $pageNum"
        } else {
            Write-Host "$h -> NOT FOUND"
        }
    }
    $doc.Close(0)
}
finally {
    $word.Quit()
    [System.Runtime.Interopservices.Marshal]::ReleaseComObject($word) | Out-Null
}
