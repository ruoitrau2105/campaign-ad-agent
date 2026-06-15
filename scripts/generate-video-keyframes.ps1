$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$imagen = "C:\Users\LAP15784-local\.codex\skills\codex-imagen\scripts\codex-imagen.mjs"
$base = Join-Path $root "assets\generated\video"
$out = Join-Path $base "03-keyframes"

$styleA = Join-Path $base "01-style-frames\team-a-midnight-office.png"
$styleB = Join-Path $base "01-style-frames\team-b-bright-office.png"
$a1 = Join-Path $base "02-characters\a1-performance-marketer.png"
$a2 = Join-Path $base "02-characters\a2-ad-ops-specialist.png"
$a3 = Join-Path $base "02-characters\a3-parent-marketer.png"
$bossA = Join-Path $base "02-characters\boss-team-a.png"
$bossB = Join-Path $base "02-characters\boss-team-b.png"

New-Item -ItemType Directory -Force $out | Out-Null

$basePrompt = "modern anime office comedy, Vietnamese advertising agency, clean line art, expressive characters, cinematic lighting, high quality, professional but comedic mood, 16:9, no readable text, no watermark"

$shots = @(
  @{
    Name = "shot-01-midnight-launch"
    Refs = @($styleA, $a1)
    Prompt = "same main character as the reference sheet, tired Vietnamese performance marketer sitting alone at midnight in a dark office, glowing laptop, digital clock showing 23:58 as simple glowing digits, messy desk with coffee cups, anxious expression, campaign dashboard glow, dramatic blue lighting"
  },
  @{
    Name = "shot-02-urgent-messages"
    Refs = @($styleA, $a1)
    Prompt = "same main character as the reference sheet, close-up office desk with smartphone and laptop, urgent message bubbles represented by abstract notification icons, the marketer looks anxious in the background, blue night lighting, tense composition"
  },
  @{
    Name = "shot-03-supermarket-laptop"
    Refs = @($styleA, $a2)
    Prompt = "same female ad ops specialist as the reference sheet, standing in a supermarket aisle with a laptop balanced on a shopping cart, grocery shelves around her, stressed but competent expression, comedic real-life work pressure"
  },
  @{
    Name = "shot-04-budget-zero-error"
    Refs = @($styleA, $a2)
    Prompt = "same female ad ops specialist as the reference sheet, dramatic close-up of laptop budget input field with one extra zero highlighted in red, her shocked eyes reflected on screen, money risk mood, tense blue lighting"
  },
  @{
    Name = "shot-05-last-minute-brief-change"
    Refs = @($styleA, $a1, $a2)
    Prompt = "same Team A characters as references, office team finally relieved then frozen by a sudden phone notification, campaign workstations around them, comedic timing, piles of task cards and campaign sheets"
  },
  @{
    Name = "shot-06-red-performance-report"
    Refs = @($styleA, $a1)
    Prompt = "same main character as the reference sheet looking at a red performance dashboard, rising CPL chart represented with red warning cards and abstract graphs, worried expression, campaign optimization pressure"
  },
  @{
    Name = "shot-07-boss-scolding-meeting"
    Refs = @($styleA, $a1, $a2, $bossA)
    Prompt = "same Team A manager and marketers as references, tense meeting room, manager pointing at red performance chart on screen, tired team sitting at table, serious office drama with slight comedy"
  },
  @{
    Name = "shot-08-we-are-not-robots"
    Refs = @($styleA, $a1, $a2, $a3, $bossA)
    Prompt = "same Team A characters as references, main marketer stands up in meeting room with determined expression, coworkers surprised and inspired, dramatic lighting, office rebellion moment"
  },
  @{
    Name = "shot-09-door-to-team-b"
    Refs = @($styleA, $styleB, $a1, $a2)
    Prompt = "Team A characters from references turning toward a bright doorway, warm light coming from the next room, strong contrast between dark stressful office and bright calm office, curious expressions"
  },
  @{
    Name = "shot-10-team-b-intro"
    Refs = @($styleB, $bossB)
    Prompt = "same calm Team B marketing lead as the reference sheet, bright modern office, relaxed team with coffee and clean desks, AI campaign assistant dashboard behind them, warm lighting, confident introduction moment"
  },
  @{
    Name = "shot-11-agent-brief-to-campaign"
    Refs = @($styleB, $bossB)
    Prompt = "bright clean AI campaign assistant dashboard, campaign brief visually transforms into organized campaign structure with cards and flow lines, Team B marketing lead calmly explaining beside the screen, no readable UI text"
  },
  @{
    Name = "shot-12-prelaunch-qa"
    Refs = @($styleB, $bossB)
    Prompt = "AI campaign assistant dashboard performing pre-launch quality check, budget issue warning, missing creative warning, tracking check represented by green and amber cards, calm Team B office mood, no readable UI text"
  },
  @{
    Name = "shot-13-insight-dashboard"
    Refs = @($styleB, $bossB)
    Prompt = "same Team B marketing lead discussing strategy with teammates around a clean analytics dashboard, insight cards, performance charts, optimization suggestions represented visually, warm professional mood, no readable UI text"
  },
  @{
    Name = "shot-14-final-cta"
    Refs = @($styleA, $styleB, $a1, $a2, $a3, $bossB)
    Prompt = "Team A and Team B characters together in a bright modern office, confident smiles, campaign dashboard in background, clear empty space on the right for Campaign Ad Agent logo and tagline, upbeat ending shot"
  }
)

foreach ($shot in $shots) {
  $target = Join-Path $out ($shot.Name + ".png")
  if (Test-Path $target) {
    Write-Host "Skipping existing $target"
    continue
  }

  $refArgs = @()
  foreach ($ref in $shot.Refs) {
    $refArgs += "--input-ref"
    $refArgs += $ref
  }

  $prompt = "generate one 16:9 anime keyframe, $($shot.Prompt), $basePrompt"
  Write-Host "Generating $($shot.Name)..."
  & node $imagen --timeout 300 --no-retry @refArgs -o $target --prompt $prompt
}

