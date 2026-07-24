[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$codexHome = if ([string]::IsNullOrWhiteSpace($env:CODEX_HOME)) {
  Join-Path $HOME '.codex'
} else {
  $env:CODEX_HOME
}

# ~/.agents/skills is the universal location (pi and other Agent Skills
# harnesses read it); ~/.codex/skills is Codex-specific.
$targets = @(
  (Join-Path $codexHome 'skills')
  (Join-Path $HOME '.agents\skills')
)

function Add-SkillLinks {
  param(
    [Parameter(Mandatory)]
    [string] $SkillsDirectory
  )

  New-Item -ItemType Directory -Path $SkillsDirectory -Force | Out-Null

  foreach ($skill in Get-ChildItem -LiteralPath $PSScriptRoot -Directory) {
    $manifest = Join-Path $skill.FullName 'SKILL.md'
    if (-not (Test-Path -LiteralPath $manifest -PathType Leaf)) {
      Write-Output "skip (no SKILL.md): $($skill.FullName)"
      continue
    }

    $destination = Join-Path $SkillsDirectory $skill.Name
    $existing = Get-Item -LiteralPath $destination -Force -ErrorAction SilentlyContinue
    if ($null -ne $existing) {
      Write-Output "exists: $destination"
      continue
    }

    New-Item -ItemType SymbolicLink -Path $destination -Target $skill.FullName | Out-Null
    Write-Output "linked: $destination -> $($skill.FullName)"
  }
}

foreach ($target in $targets) {
  Write-Output "`n== $target =="
  Add-SkillLinks -SkillsDirectory $target
}
