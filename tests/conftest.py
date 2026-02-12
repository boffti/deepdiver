"""
Pytest configuration and fixtures
"""
import pytest
import os
from dotenv import load_dotenv

# Load environment variables for tests
load_dotenv()

@pytest.fixture(scope="session")
def app():
    """Create Flask app for testing"""
    from app import create_app

    app = create_app()
    app.config['TESTING'] = True

    yield app

@pytest.fixture(scope="session")
def supabase_client(app):
    """Provide Supabase client for testing - depends on app being initialized"""
    from app.extensions import supabase

    if not supabase:
        pytest.skip("Supabase not configured - set SUPABASE_URL and SUPABASE_KEY in .env")

    return supabase

@pytest.fixture
def test_journal_entry(supabase_client):
    """Create a test journal entry and clean it up after test"""
    from datetime import datetime

    # Create test entry
    entry_data = {
        'agent_name': 'TestAgent',
        'category': 'Test',
        'content': f'Test entry at {datetime.now().isoformat()}',
        'meta': {'test': True, 'automated': True}
    }

    result = supabase_client.table('journal').insert(entry_data).execute()
    entry = result.data[0] if result.data else None

    yield entry

    # Cleanup
    if entry:
        supabase_client.table('journal').delete().eq('id', entry['id']).execute()

@pytest.fixture
def test_alert(supabase_client):
    """Create a test alert and clean it up after test"""
    # Create test alert
    alert_data = {
        'ticker': 'TEST',
        'condition': 'above',
        'price': 100.0,
        'triggered': False
    }

    result = supabase_client.table('alerts').insert(alert_data).execute()
    alert = result.data[0] if result.data else None

    yield alert

    # Cleanup
    if alert:
        supabase_client.table('alerts').delete().eq('id', alert['id']).execute()

@pytest.fixture
def clean_test_data(supabase_client):
    """Clean up any test data before and after tests"""
    def cleanup():
        # Clean test entries from journal
        supabase_client.table('journal') \
            .delete() \
            .eq('agent_name', 'TestAgent') \
            .execute()

        # Clean test alerts
        supabase_client.table('alerts') \
            .delete() \
            .eq('ticker', 'TEST') \
            .execute()

    # Clean before test
    cleanup()

    yield

    # Clean after test
    cleanup()
