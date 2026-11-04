$word = New-Object -ComObject Word.Application
$word.Visible = $false
Write-Output "Word version: $($word.Version)"
$word.Quit()
