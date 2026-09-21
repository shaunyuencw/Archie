param([Parameter(Mandatory=$true)][string]$InputPath,[Parameter(Mandatory=$true)][string]$OutputPath,[string]$View='logical')
$ErrorActionPreference='Stop'
$source=(Resolve-Path -LiteralPath $InputPath).Path
$target=[IO.Path]::GetFullPath($OutputPath)
if ([IO.Path]::GetExtension($target) -ne '.vsdx') { throw 'Output must be .vsdx' }
if (Test-Path -LiteralPath $target) { if ((Read-Host 'Output exists. Type OVERWRITE to replace') -ne 'OVERWRITE') { throw 'Cancelled' } }
$project=Get-Content -LiteralPath $source -Raw | ConvertFrom-Json
# Interactive desktop automation only. Own document; never attach to an existing diagram.
$visio=New-Object -ComObject Visio.Application
$visio.Visible=$true
$doc=$visio.Documents.Add('')
$page=$doc.Pages.Item(1)
$page.PageSheet.CellsU('PageWidth').ResultIU=16
$page.PageSheet.CellsU('PageHeight').ResultIU=12
$shapes=@{}
foreach ($component in $project.components) {
    $p=$project.views.$View.placements.($component.id)
    $x=if($null -ne $p){[double]$p.x / 96 + 1}else{1 + $shapes.Count * 2}
    $y=if($null -ne $p){11 - [double]$p.y / 96}else{8}
    $shape=$page.DrawRectangle($x,$y-0.7,$x+1.7,$y)
    $shape.NameU=$component.id
    $shape.Text=$component.name
    $shapes[$component.id]=$shape
}
foreach ($edge in $project.interfaces) {
    $connector=$page.Drop($visio.ConnectorToolDataObject,0,0)
    $connector.NameU=$edge.id
    $connector.Text=$edge.purpose
    $connector.CellsU('BeginX').GlueTo($shapes[$edge.source].CellsU('PinX'))
    $connector.CellsU('EndX').GlueTo($shapes[$edge.target].CellsU('PinX'))
}
$doc.SaveAs($target)
Write-Output "Saved $target. Visio remains open for the native-editability checklist."
