param([Parameter(Mandatory=$true)][string]$InputPath,[Parameter(Mandatory=$true)][string]$OutputPath,[string]$View='logical')
$ErrorActionPreference='Stop'
$source=(Resolve-Path -LiteralPath $InputPath).Path
$target=[IO.Path]::GetFullPath($OutputPath)
if ([IO.Path]::GetExtension($target) -ne '.vsdx') { throw 'Output must be .vsdx' }
if (Test-Path -LiteralPath $target) { if ((Read-Host 'Output exists. Type OVERWRITE to replace') -ne 'OVERWRITE') { throw 'Cancelled' } }
$project=Get-Content -LiteralPath $source -Raw | ConvertFrom-Json
if ($project.schema_version -ne '1.0') { throw 'Unsupported project schema' }
if ($View -notin @('logical','sv1','sv2')) { throw 'Unknown view' }
if ($View -eq 'sv1') { throw 'This helper currently hands over component views: use logical or sv2. SV-1 image export remains available.' }
# Interactive desktop automation only. Own document; never attach to an existing diagram.
$visio=New-Object -ComObject Visio.Application
$visio.Visible=$true
$doc=$visio.Documents.Add('')
$page=$doc.Pages.Item(1)
$page.PageSheet.CellsU('PageWidth').ResultIU=24
$page.PageSheet.CellsU('PageHeight').ResultIU=18
$shapes=@{}
$containers=@{}
foreach ($zone in $project.zones) {
    $placement=$project.views.$View.placements.($zone.id)
    if ($null -eq $placement) { continue }
    $x=1+[double]$placement.x/96; $y=17-[double]$placement.y/96
    $shape=$page.DrawRectangle($x,$y-[double]$placement.height/96,$x+[double]$placement.width/96,$y)
    $shape.NameU=$zone.id; $shape.Text=$zone.name
    $shape.CellsU('FillForegnd').FormulaU='RGB(237,244,247)'
    $shape.AddNamedRow(242,'msvStructureType',0) | Out-Null
    $shape.CellsU('User.msvStructureType').FormulaU='"Container"'
    $containers[$zone.id]=$shape
}
foreach ($component in $project.components) {
    $p=$project.views.$View.placements.($component.id)
    $deployment=$project.deployments | Where-Object { $_.component_id -eq $component.id } | Select-Object -First 1
    $zonePlacement=$project.views.$View.placements.($deployment.zone_id)
    $offsetX=if($null -ne $zonePlacement){[double]$zonePlacement.x}else{0}
    $offsetY=if($null -ne $zonePlacement){[double]$zonePlacement.y}else{0}
    $x=if($null -ne $p){([double]$p.x+$offsetX) / 96 + 1}else{1 + $shapes.Count * 2}
    $y=if($null -ne $p){17 - ([double]$p.y+$offsetY) / 96}else{8}
    $w=if($null -ne $p){[double]$p.width/96}else{1.7}
    $h=if($null -ne $p){[double]$p.height/96}else{0.9}
    $shape=$page.DrawRectangle($x,$y-$h,$x+$w,$y)
    $shape.NameU=$component.id
    $shape.Text=$component.name
    $shapes[$component.id]=$shape
    if ($deployment.zone_id -and $containers.ContainsKey($deployment.zone_id)) {
        try { $containers[$deployment.zone_id].ContainerProperties.AddMember($shape,0) }
        catch { Write-Warning "Container membership not supported for $($component.id). Verify grouping manually." }
    }
}
foreach ($edge in $project.interfaces) {
    $connector=$page.Drop($visio.ConnectorToolDataObject,0,0)
    $connector.NameU=$edge.id
    $connector.Text=$edge.purpose
    $connector.CellsU('BeginX').GlueTo($shapes[$edge.source].CellsU('PinX'))
    $connector.CellsU('EndX').GlueTo($shapes[$edge.target].CellsU('PinX'))
    $route=$project.views.$View.routes.($edge.id)
    if ($route.style -eq 'straight') { $connector.CellsU('ShapeRouteStyle').ResultIU=2 }
    else { $connector.CellsU('ShapeRouteStyle').ResultIU=1 }
    if ($View -eq 'sv2') { $connector.Text="$($edge.purpose) | $($edge.protocol) | initiator: $($edge.initiator)" }
}
$doc.SaveAs($target)
Write-Output "Saved $target. Visio remains open for the native-editability checklist."
