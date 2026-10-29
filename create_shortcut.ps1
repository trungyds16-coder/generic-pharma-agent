$ProjectDir = $PSScriptRoot
if (-not $ProjectDir) { $ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path }
if (-not $ProjectDir) { $ProjectDir = (Get-Location).Path }

$WshShell = New-Object -ComObject WScript.Shell
$DesktopPath = [Environment]::GetFolderPath("Desktop")
$Shortcut = $WshShell.CreateShortcut("$DesktopPath\Local Agent.lnk")
$Shortcut.TargetPath = "$ProjectDir\launcher.bat"
$Shortcut.WorkingDirectory = "$ProjectDir"
$Shortcut.Description = "Local AI Agent"

$IconPath = "$ProjectDir\assets\icons\project.ico"
if (Test-Path $IconPath) {
    $Shortcut.IconLocation = "$IconPath"
}
$Shortcut.Save()
Write-Host "Created desktop shortcut: $DesktopPath\Local Agent.lnk"
