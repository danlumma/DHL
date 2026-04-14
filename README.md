# Personal Knowledge Hub (PKH)

A minimal, local-first Python CLI for storing personal profile data, goals, projects, daily notes, knowledge snippets, and stories.

## Constraints

- Python only
- Standard library only
- Single CLI file: `pkh.py`
- Tests in `tests/test_pkh.py`
- Local JSON file storage in `hub.json` (auto-created at runtime, not tracked)
- No web UI, no AI features, no cloud sync, no external APIs

## Setup

No dependencies to install.

Run commands with:

```bash
python pkh.py <entity> <action> [--id ...] [--set field=value ...] [--json]
```

## Entities

- `profile`
- `goals`
- `projects`
- `daily-notes`
- `knowledge`
- `stories`

## Actions

- `create`
- `list`
- `view`
- `edit`

## Examples

### Create profile

```bash
python pkh.py profile create \
  --set name="Alex" \
  --set currentRole="Engineer" \
  --set backgroundSummary="Generalist" \
  --set majorExperiences="Built tools" \
  --set strengths="Execution" \
  --set growthAreas="Delegation" \
  --set personalityQualities="Calm" \
  --set workingStyle="Async" \
  --set coreBeliefs="Learn always" \
  --set values="Integrity" \
  --set motivations="Impact" \
  --set decisionStyle="Data-informed" \
  --set longTermVision="Build useful things"
```

### Create a goal

```bash
python pkh.py goals create \
  --set title="Ship MVP" \
  --set whyItMatters="Build momentum" \
  --set status="active" \
  --set targetDate="2026-05-01" \
  --set nextAction="Draft milestones" \
  --set tags="product" \
  --set linkedProjects="1"
```

### View and edit records

```bash
python pkh.py goals view --id 1
python pkh.py goals edit --id 1 --set status=done
python pkh.py projects list --json
```

### List filtering examples

```bash
python pkh.py goals list --status active
python pkh.py goals list --tag career --json
python pkh.py projects list --status done
python pkh.py projects list --tag health
python pkh.py daily-notes list --tag reflection
python pkh.py knowledge list --tag python
python pkh.py stories list --tag leadership --json
```


## Review Commands

These commands are additional read-only views over existing data:

- `python pkh.py dashboard [--json]`
- `python pkh.py weekly-review [--json]`
- `python pkh.py open-loops [--json]`

### Dashboard example

```bash
python pkh.py dashboard
python pkh.py dashboard --json
```

Shows:
- active goals (`status=active`)
- active projects (`status=active`)
- most recent daily notes, knowledge entries, and stories
- today top priorities as a list (empty list when none exist)

### Weekly review example

```bash
python pkh.py weekly-review
python pkh.py weekly-review --json
```

Shows:
- goals with `targetDate` in next 14 days
- projects with non-empty `nextAction`
- recent lessons in `{date, lesson}` shape
- recent knowledge entries and stories

### Open loops example

```bash
python pkh.py open-loops
python pkh.py open-loops --json
```

Shows:
- goals missing `nextAction` where `status != done`
- projects missing `nextAction` where `status != done`
- daily notes with `concerns` but no `tomorrowFocus`
- profile gaps in `name`, `currentRole`, `values`, `longTermVision`

## Search Commands

```bash
python pkh.py search keyword <term> [--json]
python pkh.py search tag <value> [--json]
```

Search scope includes:
- goals
- projects
- daily-notes
- knowledge
- stories

Behavior:
- keyword search: case-insensitive substring match
- tag search: case-insensitive exact tag match
- human-readable output grouped by entity
- JSON output grouped with stable top-level keys:
  - `goals`
  - `projects`
  - `daily-notes`
  - `knowledge`
  - `stories`

## Short workflows

### Daily workflow (5 minutes)

1. Capture or update today’s note.
2. Check open loops.
3. Review dashboard snapshot.

```bash
python pkh.py daily-notes create --set date=2026-04-14 --set summary="..." --set topPriorities="..." --set lessons="..." --set concerns="..." --set tomorrowFocus="..." --set linkedProjects="1" --set tags="daily"
python pkh.py open-loops
python pkh.py dashboard
```

### Weekly workflow (15–20 minutes)

1. Run weekly review to inspect due goals and lessons.
2. Filter active goals/projects to rebalance focus.
3. Search by keyword/tag for context before planning.

```bash
python pkh.py weekly-review
python pkh.py goals list --status active
python pkh.py projects list --status active
python pkh.py search keyword "priority"
python pkh.py search tag planning --json
```

## Validation Rules

- Required fields are validated on `create`.
- `goals.status` and `projects.status` must be one of:
  - `planned`, `active`, `on-hold`, `done`
- Date validation:
  - `goals.targetDate` must be `YYYY-MM-DD`
  - `daily-notes.date` must be `YYYY-MM-DD`
- Friendly errors for:
  - missing `--id` for non-profile `view`/`edit`
  - unknown fields passed via `--set`

## Tests

Canonical command:

```bash
python -m unittest discover -s tests -v
```
