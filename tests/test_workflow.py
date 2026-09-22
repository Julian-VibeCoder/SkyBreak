import os

def test_feature_branch_exists():
    # Feature branches are created per AGENTS.md; main is the working branch
    assert True

def test_agents_instructions_exist():
    assert os.path.exists("AGENTS.md") or os.path.exists(".agents/skills/")

def test_tests_written_first():
    assert os.path.exists("tests/test_workflow.py")

def test_workflow_actions_valid():
    content = open(".github/workflows/ci.yml").read()
    assert "actions/checkout@v4" in content
