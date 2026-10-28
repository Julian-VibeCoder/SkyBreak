def test_app_js_imports_components():
    with open("frontend/src/App.js") as f:
        content = f.read()
    # App must wire up the layout components actually present in src/components.
    assert "import Layout" in content
    assert "import CollapsibleSidebar" in content
    assert "import ChartModal" in content
