#!/usr/bin/env python3
"""Personal Knowledge Hub CLI."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

DATA_FILE = Path("hub.json")
SPECIAL_COMMANDS = {"dashboard", "weekly-review", "open-loops", "search"}

ENTITIES = {
    "profile": [
        "name",
        "currentRole",
        "backgroundSummary",
        "majorExperiences",
        "strengths",
        "growthAreas",
        "personalityQualities",
        "workingStyle",
        "coreBeliefs",
        "values",
        "motivations",
        "decisionStyle",
        "longTermVision",
    ],
    "goals": [
        "id",
        "title",
        "whyItMatters",
        "status",
        "targetDate",
        "nextAction",
        "tags",
        "linkedProjects",
    ],
    "projects": [
        "id",
        "title",
        "purpose",
        "status",
        "nextAction",
        "milestones",
        "risks",
        "linkedGoals",
        "tags",
    ],
    "daily-notes": [
        "id",
        "date",
        "summary",
        "topPriorities",
        "lessons",
        "concerns",
        "tomorrowFocus",
        "linkedProjects",
        "tags",
    ],
    "knowledge": [
        "id",
        "title",
        "type",
        "summary",
        "source",
        "tags",
        "linkedGoals",
        "linkedProjects",
        "createdAt",
    ],
    "stories": [
        "id",
        "title",
        "context",
        "challenge",
        "action",
        "result",
        "lesson",
        "useCases",
        "linkedProjects",
        "tags",
        "createdAt",
    ],
}

REQUIRED_BY_ENTITY = {
    entity: [f for f in fields if f not in {"id", "createdAt"}] for entity, fields in ENTITIES.items()
}

VALID_STATUS = {"planned", "active", "on-hold", "done"}
DATE_FIELDS = {
    "goals": ["targetDate"],
    "daily-notes": ["date"],
}


class PKHError(Exception):
    pass


def _default_data() -> dict[str, Any]:
    return {
        "profile": {},
        "goals": [],
        "projects": [],
        "daily-notes": [],
        "knowledge": [],
        "stories": [],
    }


def load_data() -> dict[str, Any]:
    if not DATA_FILE.exists():
        data = _default_data()
        save_data(data)
        return data
    with DATA_FILE.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def save_data(data: dict[str, Any]) -> None:
    with DATA_FILE.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)


def parse_set_args(set_args: list[str]) -> dict[str, Any]:
    parsed: dict[str, Any] = {}
    for item in set_args:
        if "=" not in item:
            raise PKHError(f"Invalid --set value '{item}'. Use field=value.")
        field, value = item.split("=", 1)
        if not field:
            raise PKHError(f"Invalid --set value '{item}'. Field name is empty.")
        parsed[field] = value
    return parsed


def ensure_known_fields(entity: str, payload: dict[str, Any]) -> None:
    allowed = set(ENTITIES[entity])
    unknown = [field for field in payload if field not in allowed]
    if unknown:
        allowed_sorted = ", ".join(ENTITIES[entity])
        raise PKHError(
            f"Unknown field(s) for {entity}: {', '.join(unknown)}. Allowed fields: {allowed_sorted}."
        )


def validate_dates(entity: str, payload: dict[str, Any]) -> None:
    for field in DATE_FIELDS.get(entity, []):
        if field in payload:
            value = payload[field]
            try:
                datetime.strptime(value, "%Y-%m-%d")
            except ValueError as exc:
                raise PKHError(
                    f"Field '{field}' must be a valid YYYY-MM-DD date; got '{value}'."
                ) from exc


def validate_status(entity: str, payload: dict[str, Any]) -> None:
    if entity in {"goals", "projects"} and "status" in payload:
        status = payload["status"]
        if status not in VALID_STATUS:
            allowed = ", ".join(sorted(VALID_STATUS))
            raise PKHError(f"Invalid status '{status}'. Allowed values: {allowed}.")


def require_fields(entity: str, payload: dict[str, Any]) -> None:
    missing = [field for field in REQUIRED_BY_ENTITY[entity] if field not in payload or payload[field] == ""]
    if missing:
        raise PKHError(f"Missing required fields for {entity}: {', '.join(missing)}.")


def _next_id(items: list[dict[str, Any]]) -> int:
    if not items:
        return 1
    return max(int(item["id"]) for item in items) + 1


def create_record(data: dict[str, Any], entity: str, payload: dict[str, Any]) -> dict[str, Any]:
    ensure_known_fields(entity, payload)
    require_fields(entity, payload)
    validate_dates(entity, payload)
    validate_status(entity, payload)

    if entity == "profile":
        data[entity] = payload
        save_data(data)
        return payload

    items = data[entity]
    record = dict(payload)
    record["id"] = _next_id(items)
    if entity in {"knowledge", "stories"} and "createdAt" not in record:
        record["createdAt"] = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
    items.append(record)
    save_data(data)
    return record


def _normalize_tags(raw: Any) -> list[str]:
    if isinstance(raw, list):
        return [str(item).strip() for item in raw if str(item).strip()]
    if isinstance(raw, str):
        return [part.strip() for part in raw.split(",") if part.strip()]
    return []


def _has_tag(record: dict[str, Any], tag: str) -> bool:
    target = tag.lower()
    return any(item.lower() == target for item in _normalize_tags(record.get("tags")))


def list_records(
    data: dict[str, Any],
    entity: str,
    status: str | None = None,
    tag: str | None = None,
) -> Any:
    records = data[entity]
    if entity == "profile":
        return records

    filtered = list(records)
    if status is not None:
        if entity not in {"goals", "projects"}:
            raise PKHError("--status is only supported for goals and projects list.")
        filtered = [item for item in filtered if str(item.get("status", "")).lower() == status.lower()]

    if tag is not None:
        if entity not in {"goals", "projects", "daily-notes", "knowledge", "stories"}:
            raise PKHError("--tag is not supported for this entity list.")
        filtered = [item for item in filtered if _has_tag(item, tag)]

    return filtered


def _require_id(entity: str, record_id: str | None) -> int:
    if entity == "profile":
        return 0
    if not record_id:
        raise PKHError("Missing required --id for this action.")
    try:
        return int(record_id)
    except ValueError as exc:
        raise PKHError(f"Invalid --id '{record_id}'. It must be an integer.") from exc


def _find_by_id(items: list[dict[str, Any]], record_id: int) -> dict[str, Any]:
    for item in items:
        if int(item["id"]) == record_id:
            return item
    raise PKHError(f"No record found with id={record_id}.")


def view_record(data: dict[str, Any], entity: str, record_id: str | None) -> Any:
    if entity == "profile":
        return data[entity]
    rid = _require_id(entity, record_id)
    return _find_by_id(data[entity], rid)


def edit_record(data: dict[str, Any], entity: str, record_id: str | None, payload: dict[str, Any]) -> Any:
    ensure_known_fields(entity, payload)
    if "id" in payload:
        raise PKHError("Field 'id' is immutable and cannot be edited.")

    if entity == "profile":
        updated = dict(data[entity])
        updated.update(payload)
        data[entity] = updated
        save_data(data)
        return updated

    rid = _require_id(entity, record_id)
    item = _find_by_id(data[entity], rid)
    updated = dict(item)
    updated.update(payload)
    validate_dates(entity, updated)
    validate_status(entity, updated)
    item.update(payload)
    save_data(data)
    return item


def _parse_date_safe(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        return None


def _sort_by_date_desc(records: list[dict[str, Any]], field: str) -> list[dict[str, Any]]:
    return sorted(records, key=lambda x: _parse_date_safe(x.get(field)) or datetime.min, reverse=True)


def _sort_by_created_desc(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    def key(item: dict[str, Any]) -> datetime:
        created = item.get("createdAt")
        if not created:
            return datetime.min
        try:
            return datetime.fromisoformat(created.replace("Z", "+00:00")).replace(tzinfo=None)
        except ValueError:
            return datetime.min

    return sorted(records, key=key, reverse=True)


def _sort_by_id(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(records, key=lambda item: int(item.get("id", 0)))


def _status_badge(status: str | None) -> str:
    mapping = {
        "active": "🟢 active",
        "done": "✅ done",
        "planned": "🟡 planned",
        "on-hold": "⏸️ on-hold",
    }
    return mapping.get((status or "").lower(), f"⚪ {status or 'unknown'}")


def _empty_entity_message(entity: str) -> str:
    return f"No {entity} records yet. Create one with: python pkh.py {entity} create --set field=value ..."


def _format_record_lines(entity: str, record: dict[str, Any]) -> list[str]:
    lines = []
    for field in ENTITIES[entity]:
        if field in record:
            lines.append(f"- {field}: {record[field]}")
    for key in sorted(record.keys()):
        if key not in ENTITIES[entity]:
            lines.append(f"- {key}: {record[key]}")
    return lines


def build_dashboard(data: dict[str, Any]) -> dict[str, Any]:
    today = datetime.utcnow().strftime("%Y-%m-%d")
    todays_note = next((n for n in data["daily-notes"] if n.get("date") == today), None)

    top_priorities: list[str] = []
    if todays_note and todays_note.get("topPriorities"):
        top_priorities = [todays_note["topPriorities"]]

    return {
        "activeGoals": [g for g in data["goals"] if g.get("status") == "active"],
        "activeProjects": [p for p in data["projects"] if p.get("status") == "active"],
        "recentDailyNotes": _sort_by_date_desc(data["daily-notes"], "date")[:5],
        "recentKnowledge": _sort_by_created_desc(data["knowledge"])[:5],
        "recentStories": _sort_by_created_desc(data["stories"])[:5],
        "todayTopPriorities": top_priorities,
    }


def build_weekly_review(data: dict[str, Any]) -> dict[str, Any]:
    today = datetime.utcnow().date()
    horizon = today + timedelta(days=14)

    upcoming_goals = []
    for goal in data["goals"]:
        target = _parse_date_safe(goal.get("targetDate"))
        if target and today <= target.date() <= horizon:
            upcoming_goals.append(goal)

    recent_lessons = []
    for note in _sort_by_date_desc(data["daily-notes"], "date")[:7]:
        lesson_text = note.get("lessons", "")
        if lesson_text:
            recent_lessons.append({"date": note.get("date", ""), "lesson": lesson_text})

    return {
        "upcomingGoals14Days": upcoming_goals,
        "projectsWithNextAction": [p for p in data["projects"] if p.get("nextAction", "").strip()],
        "recentLessons": recent_lessons,
        "recentKnowledge": _sort_by_created_desc(data["knowledge"])[:5],
        "recentStories": _sort_by_created_desc(data["stories"])[:5],
    }


def build_open_loops(data: dict[str, Any]) -> dict[str, Any]:
    required_profile = ["name", "currentRole", "values", "longTermVision"]
    profile = data["profile"]

    return {
        "goalsMissingNextAction": [
            g for g in data["goals"] if g.get("status") != "done" and not g.get("nextAction", "").strip()
        ],
        "projectsMissingNextAction": [
            p for p in data["projects"] if p.get("status") != "done" and not p.get("nextAction", "").strip()
        ],
        "dailyNotesConcernsNoTomorrowFocus": [
            n
            for n in data["daily-notes"]
            if n.get("concerns", "").strip() and not n.get("tomorrowFocus", "").strip()
        ],
        "profileGaps": [field for field in required_profile if not profile.get(field, "").strip()],
    }


def _record_text(record: dict[str, Any]) -> str:
    chunks: list[str] = []
    for value in record.values():
        if isinstance(value, list):
            chunks.extend(str(item) for item in value)
        else:
            chunks.append(str(value))
    return " ".join(chunks).lower()


def search_keyword(data: dict[str, Any], term: str) -> dict[str, list[dict[str, Any]]]:
    needle = term.lower()
    entities = ["goals", "projects", "daily-notes", "knowledge", "stories"]
    return {
        entity: [record for record in data[entity] if needle in _record_text(record)]
        for entity in entities
    }


def search_tag(data: dict[str, Any], tag: str) -> dict[str, list[dict[str, Any]]]:
    entities = ["goals", "projects", "daily-notes", "knowledge", "stories"]
    return {
        entity: [record for record in data[entity] if _has_tag(record, tag)]
        for entity in entities
    }


def human_output(entity: str, action: str, result: Any) -> str:
    if action == "list":
        if entity == "profile":
            if result:
                lines = ["== Profile =="]
                for field in ENTITIES["profile"]:
                    if field in result:
                        lines.append(f"- {field}: {result[field]}")
                return "\n".join(lines)
            return "Profile is empty. Add one with: python pkh.py profile create --set name=... (and other fields)"
        if not result:
            return _empty_entity_message(entity)
        lines = [f"== {entity} list ({len(result)}) =="]
        for item in _sort_by_id(result):
            title = item.get("title") or item.get("name") or "(untitled)"
            status = item.get("status")
            status_text = f" | {_status_badge(status)}" if status else ""
            lines.append(f"- #{item['id']} | {title}{status_text}")
        return "\n".join(lines)

    if entity == "profile":
        if not result:
            return "Profile is empty. Add one with: python pkh.py profile create --set name=... (and other fields)"
        return "\n".join(["== Profile ==", *_format_record_lines("profile", result)])

    record_id = result.get("id", "?")
    heading = f"== {entity} #{record_id} =="
    return "\n".join([heading, *_format_record_lines(entity, result)])


def human_special_output(command: str, result: dict[str, Any]) -> str:
    if command == "dashboard":
        lines = ["== Dashboard =="]
        lines.append(f"Active goals: {len(result['activeGoals'])}")
        for item in _sort_by_id(result["activeGoals"])[:5]:
            lines.append(f"  - #{item['id']} {item.get('title', '(untitled)')} ({_status_badge(item.get('status'))})")
        lines.append(f"Active projects: {len(result['activeProjects'])}")
        for item in _sort_by_id(result["activeProjects"])[:5]:
            lines.append(f"  - #{item['id']} {item.get('title', '(untitled)')} ({_status_badge(item.get('status'))})")
        lines.append(f"Recent daily notes: {len(result['recentDailyNotes'])}")
        lines.append(f"Recent knowledge entries: {len(result['recentKnowledge'])}")
        lines.append(f"Recent stories: {len(result['recentStories'])}")
        lines.append("Today's top priorities:")
        if result["todayTopPriorities"]:
            for item in result["todayTopPriorities"]:
                lines.append(f"  - {item}")
        else:
            lines.append("  - none")
        return "\n".join(lines)

    if command == "weekly-review":
        lines = ["== Weekly Review =="]
        lines.append(f"- Goals due in next 14 days: {len(result['upcomingGoals14Days'])}")
        for item in _sort_by_date_desc(result["upcomingGoals14Days"], "targetDate")[:5]:
            lines.append(
                f"  - #{item['id']} {item.get('title', '(untitled)')} | due {item.get('targetDate', '?')} "
                f"| {_status_badge(item.get('status'))}"
            )
        lines.append(f"- Projects with next actions: {len(result['projectsWithNextAction'])}")
        for item in _sort_by_id(result["projectsWithNextAction"])[:5]:
            lines.append(f"  - #{item['id']} {item.get('title', '(untitled)')} | next: {item.get('nextAction', '')}")
        lines.append(f"- Recent lessons: {len(result['recentLessons'])}")
        for lesson in result["recentLessons"][:5]:
            lines.append(f"  - {lesson.get('date', '?')}: {lesson.get('lesson', '')}")
        lines.append(f"- Recent knowledge entries: {len(result['recentKnowledge'])}")
        lines.append(f"- Recent stories: {len(result['recentStories'])}")
        return "\n".join(lines)

    lines = ["== Open Loops =="]
    lines.append(f"- Goals missing nextAction: {len(result['goalsMissingNextAction'])}")
    for item in _sort_by_id(result["goalsMissingNextAction"])[:5]:
        lines.append(f"  - #{item['id']} {item.get('title', '(untitled)')} ({_status_badge(item.get('status'))})")
    lines.append(f"- Projects missing nextAction: {len(result['projectsMissingNextAction'])}")
    for item in _sort_by_id(result["projectsMissingNextAction"])[:5]:
        lines.append(f"  - #{item['id']} {item.get('title', '(untitled)')} ({_status_badge(item.get('status'))})")
    lines.append(f"- Daily notes with concerns and no tomorrowFocus: {len(result['dailyNotesConcernsNoTomorrowFocus'])}")
    for item in _sort_by_date_desc(result["dailyNotesConcernsNoTomorrowFocus"], "date")[:5]:
        lines.append(f"  - #{item['id']} {item.get('date', '?')} | concerns: {item.get('concerns', '')}")
    if result["profileGaps"]:
        lines.append("- Profile gaps: " + ", ".join(result["profileGaps"]))
    else:
        lines.append("- Profile gaps: none")
    return "\n".join(lines)


def human_search_output(result: dict[str, list[dict[str, Any]]]) -> str:
    lines = ["== Search Results =="]
    total = 0
    for entity in ["goals", "projects", "daily-notes", "knowledge", "stories"]:
        records = result[entity]
        total += len(records)
        lines.append(f"[{entity}] {len(records)} match(es)")
        for item in _sort_by_id(records):
            title = item.get("title") or item.get("summary") or "(untitled)"
            status = item.get("status")
            status_text = f" | {_status_badge(status)}" if status else ""
            lines.append(f"  - #{item.get('id')} | {title}{status_text}")
    if total == 0:
        lines.append("No matches found. Try a broader keyword or a different tag.")
    return "\n".join(lines)


def build_standard_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Personal Knowledge Hub CLI")
    parser.add_argument("entity", choices=ENTITIES.keys())
    parser.add_argument("action", choices=["create", "list", "view", "edit"])
    parser.add_argument("--id", dest="record_id")
    parser.add_argument("--set", action="append", default=[], metavar="field=value")
    parser.add_argument("--status")
    parser.add_argument("--tag")
    parser.add_argument("--json", action="store_true", dest="json_out")
    return parser


def build_special_parser(command: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=f"Personal Knowledge Hub {command}")
    parser.add_argument("command", choices=[command])
    parser.add_argument("--json", action="store_true", dest="json_out")
    return parser


def build_search_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Personal Knowledge Hub search")
    parser.add_argument("command", choices=["search"])
    parser.add_argument("mode", choices=["keyword", "tag"])
    parser.add_argument("term")
    parser.add_argument("--json", action="store_true", dest="json_out")
    return parser


def main(argv: list[str] | None = None) -> int:
    argv = argv or sys.argv[1:]

    if argv and argv[0] in SPECIAL_COMMANDS:
        data = load_data()
        if argv[0] == "search":
            parser = build_search_parser()
            args = parser.parse_args(argv)
            if args.mode == "keyword":
                result = search_keyword(data, args.term)
            else:
                result = search_tag(data, args.term)
            if args.json_out:
                print(json.dumps(result, indent=2))
            else:
                print(human_search_output(result))
            return 0

        parser = build_special_parser(argv[0])
        args = parser.parse_args(argv)
        if args.command == "dashboard":
            result = build_dashboard(data)
        elif args.command == "weekly-review":
            result = build_weekly_review(data)
        else:
            result = build_open_loops(data)

        if args.json_out:
            print(json.dumps(result, indent=2))
        else:
            print(human_special_output(args.command, result))
        return 0

    parser = build_standard_parser()
    args = parser.parse_args(argv)

    try:
        payload = parse_set_args(args.set)
        data = load_data()

        if args.action == "create":
            result = create_record(data, args.entity, payload)
        elif args.action == "list":
            result = list_records(data, args.entity, status=args.status, tag=args.tag)
        elif args.action == "view":
            result = view_record(data, args.entity, args.record_id)
        elif args.action == "edit":
            result = edit_record(data, args.entity, args.record_id, payload)
        else:
            raise PKHError(f"Unsupported action: {args.action}")

        if args.json_out:
            print(json.dumps(result, indent=2))
        else:
            print(human_output(args.entity, args.action, result))
        return 0
    except PKHError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
