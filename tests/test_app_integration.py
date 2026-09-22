def test_app_js_imports_components():
    with open("frontend/src/App.js") as f:
        content = f.read()
    assert "import WeekPicker" in content
    assert "import Layout" in content
