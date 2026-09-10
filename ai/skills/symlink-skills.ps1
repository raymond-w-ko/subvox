[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$codexHome = if ([string]::IsNullOrWhiteSpace($env:CODEX_HOME)) {
  Join-Path $HOME '.codex'
} else {
  $env:CODEX_HOME
}

$claudeSkillsDirectory = Join-Path $HOME '.claude\skills'

# ~/.agents/skills is the universal location (pi and other Agent Skills
# harnesses read it); ~/.codex/skills and ~/.claude/skills are harness-specific.
$targets = @(
  (Join-Path $codexHome 'skills')
  (Join-Path $HOME '.agents\skills')
  $claudeSkillsDirectory
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

    # Do not expose Claude-spawning subagent skills inside Claude itself.
    if (
      $SkillsDirectory -eq $claudeSkillsDirectory -and
      $skill.Name -in @('claude-subagent', 'fable-subagent')
    ) {
      Write-Output "skip (Claude subagent skill): $($skill.FullName)"
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
