$docPath = 'd:\Users\anshp\Final year project\Major-Project\report\Major_Project_Report_Final.docx'
$targetsJson = Get-Content -Raw -Path 'scratch/target_paragraphs.json' -Encoding UTF8 | ConvertFrom-Json

$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0

try {
    $doc = $word.Documents.Open($docPath, [ref]$false, [ref]$true)
    
    # We want to search only starting from Section 4 (Chapter 1 onwards)
    # Get the start position of Section 4
    $sec4Start = $doc.Sections.Item(4).Range.Start
    Write-Output "Section 4 start position: $sec4Start"

    $results = @()
    $currentPos = $sec4Start

    foreach ($item in $targetsJson) {
        $searchText = $item.text.Trim()
        # Clean text for search: take first 30 chars, remove newlines
        $firstLine = ($searchText -split "`r`n|`r|`n")[0]
        if ($firstLine.Length -gt 35) {
            $firstLine = $firstLine.Substring(0, 35)
        }
        
        $range = $doc.Range($currentPos, $doc.Content.End)
        $find = $range.Find
        $find.ClearFormatting()
        $find.Text = $firstLine
        $find.Forward = $true
        $find.Wrap = 0 # wdFindStop = 0
        $find.MatchCase = $false
        $find.MatchWholeWord = $false

        $found = $find.Execute()
        if ($found) {
            $page = $range.Information(1) # wdActiveEndAdjustedPageNumber
            $currentPos = $range.Start # keep advancing forward
            $results += [PSCustomObject]@{
                Type = $item.type
                OriginalText = $item.text
                SearchText = $firstLine
                Page = $page
            }
        } else {
            # Try searching from sec4Start if not found
            $rangeRetry = $doc.Range($sec4Start, $doc.Content.End)
            $findRetry = $rangeRetry.Find
            $findRetry.ClearFormatting()
            $findRetry.Text = $firstLine
            $findRetry.Forward = $true
            $findRetry.Wrap = 0
            if ($findRetry.Execute()) {
                $page = $rangeRetry.Information(1)
                $results += [PSCustomObject]@{
                    Type = $item.type
                    OriginalText = $item.text
                    SearchText = $firstLine
                    Page = $page
                }
            } else {
                $results += [PSCustomObject]@{
                    Type = $item.type
                    OriginalText = $item.text
                    SearchText = $firstLine
                    Page = -1
                }
            }
        }
    }

    $json = $results | ConvertTo-Json -Depth 3
    $json | Set-Content -Path 'scratch/exact_pages.json' -Encoding UTF8
    Write-Output "Successfully mapped $($results.Count) items to pages."
}
finally {
    if ($doc) { $doc.Close([ref]$false) }
    $word.Quit()
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($word) | Out-Null
    [System.GC]::Collect()
    [System.GC]::WaitForPendingFinalizers()
}
