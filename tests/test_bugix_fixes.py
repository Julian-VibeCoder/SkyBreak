import os

def test_orphan_init_db_fixed_removed():
    assert not os.path.exists('init_db_fixed.py'), 'init_db_fixed.py should be removed'

def test_empty_db_files_removed():
    for f in ['skybreak_fixed.db', 'test_local.db', 'tmpbkhkvsou.db']:
        assert not os.path.exists(f), f'{f} should be removed'

def test_dockerignore_exists():
    assert os.path.exists('.dockerignore'), '.dockerignore missing'
