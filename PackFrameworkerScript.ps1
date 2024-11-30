$scriptVersion = "v3"
. $PSScriptRoot\ScriptConfig.ps1
function Select-NewMPVersion {
    $lastVersion = Get-Content -Path "$PSScriptRoot/beta/lastVersion.txt"
    $global:selectedMPVersion = Read-Host -Prompt "Select the new modpack version (Press Enter to keep $lastVersion)"
    if ([string]::IsNullOrWhiteSpace($global:selectedMPVersion)) {
        $global:selectedMPVersion = $lastVersion
    }
    $global:selectedMPVersion | Out-File -FilePath "$PSScriptRoot/beta/lastVersion.txt"
    Write-Host $global:selectedMPVersion
}
function Update-PackFramework {
    if (Test-Path -Path "$PSScriptRoot\framework") {
        Write-Host "Found a PackFramework folder, trying to update..."
        Set-Location "$PSScriptRoot\framework"
        & git pull origin
    } else {
        Set-Location "$PSScriptRoot"
        & git clone https://github.com/Den4enko/PackFramework framework
    }
}
function Select-MCVersion {
# Prompt the user to select a version to build
Write-Host "[PackFrameworker Script $scriptVersion]" -ForegroundColor Green
Write-Host "Select action to do:"
Write-Host
Write-Host "1) Build"
Write-Host "2) Copy Beta to Release folders"
Write-Host
Write-Host "0) Exit"
Write-Host

# Read the user's input
$selectedMCVersion = Read-Host -Prompt "Enter number"
Clear-Host

# Switch statement to handle the user's input
switch ($selectedMCVersion) {
    "0" {
        exit
    }
    "1" { 
        Select-NewMPVersion
        Update-PackFramework

        $modpacktype = "giga"
        Build-Modpack

        $modpacktype = "nano"
        Build-Modpack

        $modpacktype = "server"
        Build-Modpack

        Select-MCVersion
    }
    "2" {
        # 2) Copy Beta to Release folders
        Remove-Item -Path "release" -Recurse -Include *.*
        Copy-Item -Path "beta\*" -Destination "release" -Recurse -Force
        Remove-Item -Path "release\lastVersion.txt"
    }
    default {
        Write-Host "I’m sorry, but it seems you’ve selected the wrong option." -ForegroundColor Red
        Select-MCVersion
    }
}
}
function Build-Modpack {

    # Set the output path based on the modloader, Minecraft version, and modpack type
    $outputPath = "$PSScriptRoot\beta\$modloader\$mcversion\$modpacktype"

    # Display a message indicating that the build is starting
    Write-Host "[$(Get-Date -Format 'mm:ss')] Building $mcversion-$modpacktype..."

    # Clean up any old files in the output path
    Write-Host "[$(Get-Date -Format 'mm:ss')] Cleaning files..."
    if (Test-Path -PathType Container $outputPath) {
        Remove-Item -Path $outputPath -Recurse -Include *.*
    } else {
        New-Item -ItemType Directory -Path $outputPath
    }
    # Merge the necessary files into the output path
    if ($modpacktype -eq 'server' -or $modpacktype -eq 'nano' -or $modpacktype -eq 'giga') {
        Copy-Item -Path "$PSScriptRoot\framework\packwiz\$modloader\$mcversion\$modpacktype\*" -Destination "$outputPath" -Recurse -Force
        Copy-Item -Path "$PSScriptRoot\mod\$modloader\all\server\*" -Destination "$outputPath" -Recurse -Force
    }
    if ($modpacktype -eq 'nano' -or $modpacktype -eq 'giga') {
        Copy-Item -Path "$PSScriptRoot\mod\$modloader\all\nano\*" -Destination "$outputPath" -Recurse -Force
        if ($modpacktype -eq 'giga') {
            Copy-Item -Path "$PSScriptRoot\mod\$modloader\all\giga\*" -Destination "$outputPath" -Recurse -Force
            }
            }

    # Remove files from the list
    if (Test-Path -Path "$outputPath\filesToRemove.txt" -PathType leaf) {
        Write-Host "[$(Get-Date -Format 'mm:ss')] Removing files from the list..."
        Get-Content -Path "$outputPath\filesToRemove.txt" | ForEach-Object {
            Remove-Item "$outputPath/$_" -Force
        }
        Remove-Item -Path "$outputPath\filesToRemove.txt"
      }

    # Change the versions
    Write-Host "[$(Get-Date -Format 'mm:ss')] Changing versions..."
    
    (Get-Content "$outputPath/pack.toml") | ForEach-Object { $_ -replace "noVersion", "$global:selectedMPVersion" } | Set-Content "$outputPath/pack.toml"
    if ($modpacktype -eq 'nano' -or $modpacktype -eq 'giga') {
    (Get-Content "$outputPath/config/fancymenu/custom_locals/mod/en_us.local") | ForEach-Object { $_ -replace "noVersion", "$global:selectedMPVersion" } | Set-Content "$outputPath/config/fancymenu/custom_locals/mod/en_us.local"
    }
    # Copy the changelog to the output path
    if ($modpacktype -eq 'nano' -or $modpacktype -eq 'giga') {
    Write-Host "[$(Get-Date -Format 'mm:ss')] Copying Changelog..."
    Copy-Item "$PSScriptRoot\CHANGELOG.md" "$outputPath\config\fancymenu\assets\changelog.md"
    }
    # Update the modpack using packwiz
    Write-Host "[$(Get-Date -Format 'mm:ss')] Refreshing..."
    Set-Location "$outputPath"
    & packwiz refresh --build

    # Display a message indicating that the build is complete
    Write-Host "[$(Get-Date -Format 'mm:ss')] Done!"

}
Select-MCVersion