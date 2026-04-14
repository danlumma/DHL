import json
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PKH = ROOT / "pkh.py"


def run_cli(args, cwd):
    cmd = ["python", str(PKH)] + args
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)


class TestPKH(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.cwd = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def read_hub(self):
        with (self.cwd / "hub.json").open("r", encoding="utf-8") as fh:
            return json.load(fh)

    def test_profile_flow_create_view_edit(self):
        create = run_cli(
            [
                "profile",
                "create",
                "--set",
                "name=Alex",
                "--set",
                "currentRole=Engineer",
                "--set",
                "backgroundSummary=Generalist",
                "--set",
                "majorExperiences=Built tools",
                "--set",
                "strengths=Execution",
                "--set",
                "growthAreas=Delegation",
                "--set",
                "personalityQualities=Calm",
                "--set",
                "workingStyle=Async",
                "--set",
                "coreBeliefs=Learn always",
                "--set",
                "values=Integrity",
                "--set",
                "motivations=Impact",
                "--set",
                "decisionStyle=Data-informed",
                "--set",
                "longTermVision=Build useful things",
            ],
            self.cwd,
        )
        self.assertEqual(create.returncode, 0, create.stderr)
        self.assertTrue((self.cwd / "hub.json").exists())

        view = run_cli(["profile", "view", "--json"], self.cwd)
        self.assertEqual(view.returncode, 0, view.stderr)
        profile = json.loads(view.stdout)
        self.assertEqual(profile["name"], "Alex")

        edit = run_cli(["profile", "edit", "--set", "workingStyle=Hybrid", "--json"], self.cwd)
        self.assertEqual(edit.returncode, 0, edit.stderr)
        edited = json.loads(edit.stdout)
        self.assertEqual(edited["workingStyle"], "Hybrid")

    def test_goals_flow_and_validations(self):
        bad_status = run_cli(
            [
                "goals",
                "create",
                "--set",
                "title=Ship MVP",
                "--set",
                "whyItMatters=Momentum",
                "--set",
                "status=invalid",
                "--set",
                "targetDate=2026-04-30",
                "--set",
                "nextAction=Draft plan",
                "--set",
                "tags=core",
                "--set",
                "linkedProjects=1",
            ],
            self.cwd,
        )
        self.assertNotEqual(bad_status.returncode, 0)
        self.assertIn("Invalid status", bad_status.stderr)

        good = run_cli(
            [
                "goals",
                "create",
                "--set",
                "title=Ship MVP",
                "--set",
                "whyItMatters=Momentum",
                "--set",
                "status=active",
                "--set",
                "targetDate=2026-04-30",
                "--set",
                "nextAction=Draft plan",
                "--set",
                "tags=core",
                "--set",
                "linkedProjects=1",
                "--json",
            ],
            self.cwd,
        )
        self.assertEqual(good.returncode, 0, good.stderr)
        goal = json.loads(good.stdout)
        self.assertEqual(goal["id"], 1)

        view = run_cli(["goals", "view", "--id", "1", "--json"], self.cwd)
        self.assertEqual(view.returncode, 0)

        edit = run_cli(["goals", "edit", "--id", "1", "--set", "status=done", "--json"], self.cwd)
        self.assertEqual(edit.returncode, 0)
        edited = json.loads(edit.stdout)
        self.assertEqual(edited["status"], "done")

        missing_id = run_cli(["goals", "view"], self.cwd)
        self.assertNotEqual(missing_id.returncode, 0)
        self.assertIn("Missing required --id", missing_id.stderr)

    def test_projects_create_view_edit(self):
        create = run_cli(
            [
                "projects",
                "create",
                "--set",
                "title=PKH CLI",
                "--set",
                "purpose=Track personal context",
                "--set",
                "status=planned",
                "--set",
                "nextAction=Outline",
                "--set",
                "milestones=v1",
                "--set",
                "risks=time",
                "--set",
                "linkedGoals=1",
                "--set",
                "tags=python",
                "--json",
            ],
            self.cwd,
        )
        self.assertEqual(create.returncode, 0, create.stderr)

        view = run_cli(["projects", "view", "--id", "1", "--json"], self.cwd)
        self.assertEqual(view.returncode, 0, view.stderr)

        edit = run_cli(["projects", "edit", "--id", "1", "--set", "status=active", "--json"], self.cwd)
        self.assertEqual(edit.returncode, 0, edit.stderr)

    def test_daily_notes_create_view_edit(self):
        create = run_cli(
            [
                "daily-notes",
                "create",
                "--set",
                "date=2026-04-14",
                "--set",
                "summary=Good day",
                "--set",
                "topPriorities=Finish tests",
                "--set",
                "lessons=Keep simple",
                "--set",
                "concerns=Scope creep",
                "--set",
                "tomorrowFocus=Refactor",
                "--set",
                "linkedProjects=1",
                "--set",
                "tags=journal",
                "--json",
            ],
            self.cwd,
        )
        self.assertEqual(create.returncode, 0, create.stderr)

        view = run_cli(["daily-notes", "view", "--id", "1", "--json"], self.cwd)
        self.assertEqual(view.returncode, 0, view.stderr)

        edit = run_cli(["daily-notes", "edit", "--id", "1", "--set", "summary=Great day", "--json"], self.cwd)
        self.assertEqual(edit.returncode, 0, edit.stderr)

    def test_knowledge_create_view_edit(self):
        create = run_cli(
            [
                "knowledge",
                "create",
                "--set",
                "title=Atomic notes",
                "--set",
                "type=method",
                "--set",
                "summary=Small connected notes",
                "--set",
                "source=book",
                "--set",
                "tags=notes",
                "--set",
                "linkedGoals=1",
                "--set",
                "linkedProjects=1",
                "--json",
            ],
            self.cwd,
        )
        self.assertEqual(create.returncode, 0, create.stderr)
        created = json.loads(create.stdout)
        self.assertIn("createdAt", created)

        view = run_cli(["knowledge", "view", "--id", "1", "--json"], self.cwd)
        self.assertEqual(view.returncode, 0, view.stderr)

        edit = run_cli(["knowledge", "edit", "--id", "1", "--set", "summary=Tiny linked notes", "--json"], self.cwd)
        self.assertEqual(edit.returncode, 0, edit.stderr)

    def test_stories_create_view_edit(self):
        create = run_cli(
            [
                "stories",
                "create",
                "--set",
                "title=Launch recovery",
                "--set",
                "context=Late release",
                "--set",
                "challenge=Stability issues",
                "--set",
                "action=Rollback and patch",
                "--set",
                "result=Stable deploy",
                "--set",
                "lesson=Use canaries",
                "--set",
                "useCases=Interviews",
                "--set",
                "linkedProjects=1",
                "--set",
                "tags=leadership",
                "--json",
            ],
            self.cwd,
        )
        self.assertEqual(create.returncode, 0, create.stderr)

        view = run_cli(["stories", "view", "--id", "1", "--json"], self.cwd)
        self.assertEqual(view.returncode, 0, view.stderr)

        edit = run_cli(["stories", "edit", "--id", "1", "--set", "lesson=Canary first", "--json"], self.cwd)
        self.assertEqual(edit.returncode, 0, edit.stderr)

    def test_unknown_field_friendly_error(self):
        res = run_cli(
            [
                "projects",
                "create",
                "--set",
                "title=One",
                "--set",
                "purpose=Two",
                "--set",
                "status=planned",
                "--set",
                "nextAction=Three",
                "--set",
                "milestones=Four",
                "--set",
                "risks=Five",
                "--set",
                "linkedGoals=Six",
                "--set",
                "tags=Seven",
                "--set",
                "unknownField=oops",
            ],
            self.cwd,
        )
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("Unknown field", res.stderr)


    def test_dashboard_command_json_shape(self):
        run_cli(
            [
                "goals", "create", "--set", "title=G1", "--set", "whyItMatters=W", "--set", "status=active",
                "--set", "targetDate=2026-04-20", "--set", "nextAction=Do", "--set", "tags=t", "--set", "linkedProjects=1",
            ],
            self.cwd,
        )
        run_cli(
            [
                "projects", "create", "--set", "title=P1", "--set", "purpose=Purpose", "--set", "status=active",
                "--set", "nextAction=Act", "--set", "milestones=m", "--set", "risks=r", "--set", "linkedGoals=1", "--set", "tags=t",
            ],
            self.cwd,
        )
        run_cli(
            [
                "daily-notes", "create", "--set", "date=2026-04-14", "--set", "summary=s", "--set", "topPriorities=Top one",
                "--set", "lessons=l", "--set", "concerns=c", "--set", "tomorrowFocus=tf", "--set", "linkedProjects=1", "--set", "tags=t",
            ],
            self.cwd,
        )
        run_cli(
            [
                "knowledge", "create", "--set", "title=K1", "--set", "type=note", "--set", "summary=s", "--set", "source=src",
                "--set", "tags=t", "--set", "linkedGoals=1", "--set", "linkedProjects=1",
            ],
            self.cwd,
        )
        run_cli(
            [
                "stories", "create", "--set", "title=S1", "--set", "context=c", "--set", "challenge=ch", "--set", "action=a",
                "--set", "result=r", "--set", "lesson=l", "--set", "useCases=u", "--set", "linkedProjects=1", "--set", "tags=t",
            ],
            self.cwd,
        )

        res = run_cli(["dashboard", "--json"], self.cwd)
        self.assertEqual(res.returncode, 0, res.stderr)
        payload = json.loads(res.stdout)
        self.assertIn("activeGoals", payload)
        self.assertIn("activeProjects", payload)
        self.assertIn("recentDailyNotes", payload)
        self.assertIn("recentKnowledge", payload)
        self.assertIn("recentStories", payload)
        self.assertIn("todayTopPriorities", payload)
        self.assertIsInstance(payload["todayTopPriorities"], list)

    def test_weekly_review_and_open_loops_json_shape(self):
        run_cli(
            [
                "goals", "create", "--set", "title=G2", "--set", "whyItMatters=W", "--set", "status=planned",
                "--set", "targetDate=2026-04-20", "--set", "nextAction=Start", "--set", "tags=t", "--set", "linkedProjects=1",
            ],
            self.cwd,
        )
        run_cli(
            [
                "projects", "create", "--set", "title=P2", "--set", "purpose=Purpose", "--set", "status=active",
                "--set", "nextAction=Start", "--set", "milestones=m", "--set", "risks=r", "--set", "linkedGoals=1", "--set", "tags=t",
            ],
            self.cwd,
        )
        run_cli(
            [
                "daily-notes", "create", "--set", "date=2026-04-13", "--set", "summary=s", "--set", "topPriorities=Top",
                "--set", "lessons=Lesson text", "--set", "concerns=Concern", "--set", "tomorrowFocus=Tomorrow", "--set", "linkedProjects=1", "--set", "tags=t",
            ],
            self.cwd,
        )
        run_cli(
            [
                "knowledge", "create", "--set", "title=K2", "--set", "type=note", "--set", "summary=s", "--set", "source=src",
                "--set", "tags=t", "--set", "linkedGoals=1", "--set", "linkedProjects=1",
            ],
            self.cwd,
        )
        run_cli(
            [
                "stories", "create", "--set", "title=S2", "--set", "context=c", "--set", "challenge=ch", "--set", "action=a",
                "--set", "result=r", "--set", "lesson=l", "--set", "useCases=u", "--set", "linkedProjects=1", "--set", "tags=t",
            ],
            self.cwd,
        )

        run_cli(["goals", "edit", "--id", "1", "--set", "nextAction="], self.cwd)
        run_cli(["projects", "edit", "--id", "1", "--set", "nextAction="], self.cwd)
        run_cli(["daily-notes", "edit", "--id", "1", "--set", "tomorrowFocus="], self.cwd)

        weekly = run_cli(["weekly-review", "--json"], self.cwd)
        self.assertEqual(weekly.returncode, 0, weekly.stderr)
        weekly_payload = json.loads(weekly.stdout)
        self.assertIn("recentLessons", weekly_payload)
        if weekly_payload["recentLessons"]:
            self.assertIn("date", weekly_payload["recentLessons"][0])
            self.assertIn("lesson", weekly_payload["recentLessons"][0])
            self.assertNotIn("id", weekly_payload["recentLessons"][0])

        open_loops = run_cli(["open-loops", "--json"], self.cwd)
        self.assertEqual(open_loops.returncode, 0, open_loops.stderr)
        loops_payload = json.loads(open_loops.stdout)
        self.assertIn("goalsMissingNextAction", loops_payload)
        self.assertIn("projectsMissingNextAction", loops_payload)
        self.assertIn("dailyNotesConcernsNoTomorrowFocus", loops_payload)
        self.assertIn("profileGaps", loops_payload)

    def test_list_filtering_status_and_tag(self):
        run_cli(
            [
                "goals", "create", "--set", "title=Goal A", "--set", "whyItMatters=W", "--set", "status=active",
                "--set", "targetDate=2026-04-20", "--set", "nextAction=Do", "--set", "tags=health", "--set", "linkedProjects=1",
            ],
            self.cwd,
        )
        run_cli(
            [
                "goals", "create", "--set", "title=Goal B", "--set", "whyItMatters=W", "--set", "status=done",
                "--set", "targetDate=2026-05-20", "--set", "nextAction=Done", "--set", "tags=career", "--set", "linkedProjects=1",
            ],
            self.cwd,
        )
        run_cli(
            [
                "projects", "create", "--set", "title=Proj A", "--set", "purpose=P", "--set", "status=active",
                "--set", "nextAction=Act", "--set", "milestones=m", "--set", "risks=r", "--set", "linkedGoals=1", "--set", "tags=health",
            ],
            self.cwd,
        )
        run_cli(
            [
                "projects", "create", "--set", "title=Proj B", "--set", "purpose=P", "--set", "status=done",
                "--set", "nextAction=Act", "--set", "milestones=m", "--set", "risks=r", "--set", "linkedGoals=1", "--set", "tags=career",
            ],
            self.cwd,
        )
        run_cli(
            [
                "daily-notes", "create", "--set", "date=2026-04-14", "--set", "summary=S", "--set", "topPriorities=P",
                "--set", "lessons=L", "--set", "concerns=C", "--set", "tomorrowFocus=T", "--set", "linkedProjects=1", "--set", "tags=career",
            ],
            self.cwd,
        )
        run_cli(
            [
                "knowledge", "create", "--set", "title=Know", "--set", "type=note", "--set", "summary=S", "--set", "source=src",
                "--set", "tags=career", "--set", "linkedGoals=1", "--set", "linkedProjects=1",
            ],
            self.cwd,
        )
        run_cli(
            [
                "stories", "create", "--set", "title=Story", "--set", "context=c", "--set", "challenge=ch", "--set", "action=a",
                "--set", "result=r", "--set", "lesson=l", "--set", "useCases=u", "--set", "linkedProjects=1", "--set", "tags=career",
            ],
            self.cwd,
        )

        goals_active = run_cli(["goals", "list", "--status", "active", "--json"], self.cwd)
        self.assertEqual(goals_active.returncode, 0, goals_active.stderr)
        goals_active_payload = json.loads(goals_active.stdout)
        self.assertEqual(len(goals_active_payload), 1)
        self.assertEqual(goals_active_payload[0]["title"], "Goal A")

        goals_tag = run_cli(["goals", "list", "--tag", "career", "--json"], self.cwd)
        self.assertEqual(goals_tag.returncode, 0, goals_tag.stderr)
        goals_tag_payload = json.loads(goals_tag.stdout)
        self.assertEqual(len(goals_tag_payload), 1)
        self.assertEqual(goals_tag_payload[0]["title"], "Goal B")

        projects_status = run_cli(["projects", "list", "--status", "active", "--json"], self.cwd)
        self.assertEqual(projects_status.returncode, 0, projects_status.stderr)
        projects_status_payload = json.loads(projects_status.stdout)
        self.assertEqual(len(projects_status_payload), 1)
        self.assertEqual(projects_status_payload[0]["title"], "Proj A")

        projects_tag = run_cli(["projects", "list", "--tag", "career", "--json"], self.cwd)
        self.assertEqual(projects_tag.returncode, 0, projects_tag.stderr)
        projects_tag_payload = json.loads(projects_tag.stdout)
        self.assertEqual(len(projects_tag_payload), 1)
        self.assertEqual(projects_tag_payload[0]["title"], "Proj B")

        notes_tag = run_cli(["daily-notes", "list", "--tag", "career", "--json"], self.cwd)
        self.assertEqual(notes_tag.returncode, 0, notes_tag.stderr)
        self.assertEqual(len(json.loads(notes_tag.stdout)), 1)

        knowledge_tag = run_cli(["knowledge", "list", "--tag", "career", "--json"], self.cwd)
        self.assertEqual(knowledge_tag.returncode, 0, knowledge_tag.stderr)
        self.assertEqual(len(json.loads(knowledge_tag.stdout)), 1)

        stories_tag = run_cli(["stories", "list", "--tag", "career", "--json"], self.cwd)
        self.assertEqual(stories_tag.returncode, 0, stories_tag.stderr)
        self.assertEqual(len(json.loads(stories_tag.stdout)), 1)

    def test_search_keyword_tag_no_match_and_json_shape(self):
        run_cli(
            [
                "goals", "create", "--set", "title=Learn Guitar", "--set", "whyItMatters=Joy", "--set", "status=active",
                "--set", "targetDate=2026-04-22", "--set", "nextAction=Practice", "--set", "tags=music", "--set", "linkedProjects=1",
            ],
            self.cwd,
        )
        run_cli(
            [
                "projects", "create", "--set", "title=Music Project", "--set", "purpose=Build routine", "--set", "status=active",
                "--set", "nextAction=Schedule", "--set", "milestones=m", "--set", "risks=r", "--set", "linkedGoals=1", "--set", "tags=music",
            ],
            self.cwd,
        )
        run_cli(
            [
                "daily-notes", "create", "--set", "date=2026-04-14", "--set", "summary=Practiced scales", "--set", "topPriorities=Practice",
                "--set", "lessons=Consistency matters", "--set", "concerns=None", "--set", "tomorrowFocus=Rhythm", "--set", "linkedProjects=1", "--set", "tags=music",
            ],
            self.cwd,
        )
        run_cli(
            [
                "knowledge", "create", "--set", "title=Chord Shapes", "--set", "type=note", "--set", "summary=Major/minor chords", "--set", "source=book",
                "--set", "tags=music", "--set", "linkedGoals=1", "--set", "linkedProjects=1",
            ],
            self.cwd,
        )
        run_cli(
            [
                "stories", "create", "--set", "title=Recital", "--set", "context=Beginner", "--set", "challenge=Nerves", "--set", "action=Practice",
                "--set", "result=Finished", "--set", "lesson=Preparation helps", "--set", "useCases=Interview", "--set", "linkedProjects=1", "--set", "tags=music",
            ],
            self.cwd,
        )

        keyword = run_cli(["search", "keyword", "music", "--json"], self.cwd)
        self.assertEqual(keyword.returncode, 0, keyword.stderr)
        keyword_payload = json.loads(keyword.stdout)
        self.assertEqual(list(keyword_payload.keys()), ["goals", "projects", "daily-notes", "knowledge", "stories"])
        self.assertGreaterEqual(len(keyword_payload["projects"]), 1)

        tag = run_cli(["search", "tag", "MUSIC", "--json"], self.cwd)
        self.assertEqual(tag.returncode, 0, tag.stderr)
        tag_payload = json.loads(tag.stdout)
        self.assertEqual(list(tag_payload.keys()), ["goals", "projects", "daily-notes", "knowledge", "stories"])
        self.assertEqual(len(tag_payload["goals"]), 1)
        self.assertEqual(len(tag_payload["projects"]), 1)

        no_match = run_cli(["search", "keyword", "no-such-term"], self.cwd)
        self.assertEqual(no_match.returncode, 0, no_match.stderr)
        self.assertIn("No matches found.", no_match.stdout)

    def test_empty_state_human_output_messages(self):
        goals_empty = run_cli(["goals", "list"], self.cwd)
        self.assertEqual(goals_empty.returncode, 0, goals_empty.stderr)
        self.assertIn("No goals records yet.", goals_empty.stdout)

        profile_empty = run_cli(["profile", "view"], self.cwd)
        self.assertEqual(profile_empty.returncode, 0, profile_empty.stderr)
        self.assertIn("Profile is empty.", profile_empty.stdout)

    def test_human_list_sorted_and_status_badges(self):
        run_cli(
            [
                "goals", "create", "--set", "title=First", "--set", "whyItMatters=W", "--set", "status=done",
                "--set", "targetDate=2026-04-20", "--set", "nextAction=Done", "--set", "tags=t", "--set", "linkedProjects=1",
            ],
            self.cwd,
        )
        run_cli(
            [
                "goals", "create", "--set", "title=Second", "--set", "whyItMatters=W", "--set", "status=active",
                "--set", "targetDate=2026-04-21", "--set", "nextAction=Do", "--set", "tags=t", "--set", "linkedProjects=1",
            ],
            self.cwd,
        )

        out = run_cli(["goals", "list"], self.cwd)
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertIn("== goals list (2) ==", out.stdout)
        self.assertIn("✅ done", out.stdout)
        self.assertIn("🟢 active", out.stdout)
        self.assertLess(out.stdout.find("#1"), out.stdout.find("#2"))

    def test_search_human_grouped_readability(self):
        run_cli(
            [
                "knowledge", "create", "--set", "title=Python Tips", "--set", "type=note", "--set", "summary=use unittest", "--set", "source=docs",
                "--set", "tags=python", "--set", "linkedGoals=1", "--set", "linkedProjects=1",
            ],
            self.cwd,
        )
        out = run_cli(["search", "keyword", "python"], self.cwd)
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertIn("== Search Results ==", out.stdout)
        self.assertIn("[knowledge]", out.stdout)


if __name__ == "__main__":
    unittest.main()
