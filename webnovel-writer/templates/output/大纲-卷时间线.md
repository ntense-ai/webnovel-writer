# Volume {volume_id} Timeline

> This table is the single source of truth for this volume's timeline. Chapter-outline time fields must match it.

## Volume-Level Time Settings

| Item | Value |
|------|-----|
| Time baseline | {e.g. apocalypse day 1 / spring of year 3021 / March 2026} |
| Time span of this volume | {e.g. apocalypse days 1–30 / about one month} |
| Key countdown events | {e.g. supplies run out D-7 / sect tournament D-10 / none} |

## Chapter Timeline

| Chapter | Time anchor | Time covered | Gap from previous chapter | Countdown status | Notes |
|------|---------|---------|-----------|-----------|------|
| Chapter 1 | {apocalypse day 1, dawn} | {4 hours} | {-} | {supplies run out D-7} | {opening} |
| Chapter 2 | {apocalypse day 1, noon} | {3 hours} | {0 (immediately afterward)} | {D-7} | {} |
| Chapter 3 | {apocalypse day 1, evening} | {2 hours} | {2 hours} | {D-7} | {} |
| Chapter 4 | {apocalypse day 2, dawn} | {6 hours} | {overnight} | {D-6} | {account for the night} |
| ... | ... | ... | ... | ... | ... |

## Time-Skip Rules

### Permitted Time Progression
- Continuous action within the same day: no special explanation required.
- Overnight (6-12 hours): use 1-2 transitional sentences (such as "The night passed uneventfully" / "After a night's rest").
- Across days (1-3 days): use a transitional paragraph or chapter to explain what happened during the interval.
- Large skips (>3 days): a transitional chapter or explicit time marker ("Three days later") is mandatory.

### Prohibited Time Manipulations
- ❌ Moving backward in time (unless explicitly presented as a memory/flashback).
- ❌ Skipping countdown steps (D-5 cannot jump directly to D-2).
- ❌ Large unexplained time jumps.

## Countdown Event Tracking

| Event name | Start | Current status | Trigger chapter | Outcome |
|---------|------|---------|---------|------|
| {supplies run out} | {D-7} | {in progress / triggered / resolved} | {chapter N} | {} |
| {sect tournament} | {D-10} | {} | {} | {} |

## Validation Checklist

After completing this volume's chapter outlines, check the following:

- [ ] Every chapter has a time anchor.
- [ ] Time increases monotonically (no backward jumps).
- [ ] Chapters crossing nights/days include transitions.
- [ ] Countdowns advance correctly (each passing day: D-N → D-(N-1)).
- [ ] Large time skips have reasonable explanations.
