"""Unit tests for main.py issue filtering and context building."""
import json
from unittest.mock import call, patch

import pytest

from main import OWNER_LOGIN, build_issue_context, get_qualifying_issues


def _issue_detail(author_login: str, comments: list) -> str:
    return json.dumps({"author": {"login": author_login}, "comments": comments})


def _issue_full(number: int, title: str, body: str, author_login: str, comments: list) -> str:
    return json.dumps(
        {
            "number": number,
            "title": title,
            "body": body,
            "author": {"login": author_login},
            "comments": comments,
        }
    )


class TestGetQualifyingIssues:
    def test_no_open_issues(self):
        with patch("main.gh") as mock_gh:
            mock_gh.return_value = json.dumps([])
            assert get_qualifying_issues() == []

    def test_issue_by_owner_no_comments_qualifies(self):
        with patch("main.gh") as mock_gh:
            mock_gh.side_effect = [
                json.dumps([{"number": 1}]),
                _issue_detail(OWNER_LOGIN, []),
            ]
            assert get_qualifying_issues() == [1]

    def test_issue_by_other_user_no_comments_skipped(self):
        with patch("main.gh") as mock_gh:
            mock_gh.side_effect = [
                json.dumps([{"number": 1}]),
                _issue_detail("stranger", []),
            ]
            assert get_qualifying_issues() == []

    def test_last_comment_by_owner_qualifies(self):
        comments = [
            {"author": {"login": "ai-paul[bot]"}, "body": "Bot reply"},
            {"author": {"login": OWNER_LOGIN}, "body": "Follow-up"},
        ]
        with patch("main.gh") as mock_gh:
            mock_gh.side_effect = [
                json.dumps([{"number": 2}]),
                _issue_detail("anyone", comments),
            ]
            assert get_qualifying_issues() == [2]

    def test_last_comment_by_bot_skipped(self):
        comments = [
            {"author": {"login": OWNER_LOGIN}, "body": "Question"},
            {"author": {"login": "ai-paul[bot]"}, "body": "Already answered"},
        ]
        with patch("main.gh") as mock_gh:
            mock_gh.side_effect = [
                json.dumps([{"number": 3}]),
                _issue_detail(OWNER_LOGIN, comments),
            ]
            assert get_qualifying_issues() == []

    def test_multiple_issues_filters_correctly(self):
        with patch("main.gh") as mock_gh:
            mock_gh.side_effect = [
                json.dumps([{"number": 1}, {"number": 2}, {"number": 3}]),
                _issue_detail(OWNER_LOGIN, []),        # #1: qualifies
                _issue_detail("stranger", []),          # #2: skipped
                _issue_detail(OWNER_LOGIN, [           # #3: bot was last, skipped
                    {"author": {"login": "ai-paul[bot]"}, "body": "done"},
                ]),
            ]
            assert get_qualifying_issues() == [1]


class TestBuildIssueContext:
    def test_no_comments(self):
        with patch("main.gh") as mock_gh:
            mock_gh.return_value = _issue_full(
                5, "problem", "How does X work?", OWNER_LOGIN, []
            )
            context = build_issue_context(5)
        assert "Issue #5" in context
        assert "problem" in context
        assert "How does X work?" in context
        assert "评论记录" not in context

    def test_with_comments(self):
        comments = [
            {"author": {"login": OWNER_LOGIN}, "body": "Can you clarify?"},
            {"author": {"login": "ai-paul[bot]"}, "body": "Sure!"},
        ]
        with patch("main.gh") as mock_gh:
            mock_gh.return_value = _issue_full(5, "title", "body", OWNER_LOGIN, comments)
            context = build_issue_context(5)
        assert "评论记录" in context
        assert "Can you clarify?" in context
        assert "Sure!" in context

    def test_gh_called_with_correct_args(self):
        with patch("main.gh") as mock_gh:
            mock_gh.return_value = _issue_full(7, "t", "b", OWNER_LOGIN, [])
            build_issue_context(7)
        mock_gh.assert_called_once_with(
            "issue", "view", "7", "--json", "number,title,body,author,comments"
        )
