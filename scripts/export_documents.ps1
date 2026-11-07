# Export and paginate the reviewed documents using installed Microsoft Word.
$ErrorActionPreference = 'Stop'
$repositoryRoot = Split-Path -Parent $PSScriptRoot
$documentPaths = @(
    'docs\requirements\Vehicle_Parking_System_SRS.docx',
    'docs\SAD\Vehicle_Parking_System_SAD.docx',
    'docs\testing\Vehicle_Parking_System_Test_Plan.docx'
)
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
$word.AutomationSecurity = 3
try {
    foreach ($relativePath in $documentPaths) {
        $documentPath = Join-Path $repositoryRoot $relativePath
        $document = $word.Documents.Open($documentPath, $false, $false)
        try {
            $document.Fields.Update() | Out-Null
            $document.Repaginate()
            $document.Fields.Update() | Out-Null
            $document.Save()
            $pdfPath = [System.IO.Path]::ChangeExtension($documentPath, '.pdf')
            $document.ExportAsFixedFormat($pdfPath, 17)
            Write-Output $pdfPath
        }
        finally {
            $document.Close(0)
            [System.Runtime.InteropServices.Marshal]::ReleaseComObject($document) | Out-Null
        }
    }
}
finally {
    $word.Quit(0)
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($word) | Out-Null
}
