"""
Tests for Supabase database operations
"""
import pytest
from datetime import datetime


@pytest.mark.supabase
@pytest.mark.integration
class TestSupabaseReadOperations:
    """Test reading from Supabase tables"""

    def test_read_settings(self, supabase_client):
        """Test reading settings table"""
        result = supabase_client.table('settings').select('*').execute()

        assert result.data is not None
        assert len(result.data) >= 3  # Should have at least default settings

        # Check for expected settings
        keys = [row['key'] for row in result.data]
        assert 'account_equity' in keys
        assert 'risk_pct' in keys
        assert 'max_positions' in keys

    def test_read_journal_with_filter(self, supabase_client, test_journal_entry):
        """Test reading journal with filter"""
        entry_id = test_journal_entry['id']

        result = supabase_client.table('journal') \
            .select('*') \
            .eq('id', entry_id) \
            .single() \
            .execute()

        assert result.data is not None
        assert result.data['id'] == entry_id
        assert result.data['agent_name'] == 'TestAgent'
        assert result.data['category'] == 'Test'

    def test_read_alerts(self, supabase_client, test_alert):
        """Test reading alerts table"""
        result = supabase_client.table('alerts').select('*').execute()

        assert result.data is not None
        # Should at least have our test alert
        alert_ids = [alert['id'] for alert in result.data]
        assert test_alert['id'] in alert_ids


@pytest.mark.supabase
@pytest.mark.integration
class TestSupabaseWriteOperations:
    """Test writing to Supabase tables"""

    def test_insert_journal_entry(self, supabase_client, clean_test_data):
        """Test inserting a journal entry"""
        entry_data = {
            'agent_name': 'TestAgent',
            'category': 'Test',
            'content': f'Test insert at {datetime.now().isoformat()}',
            'meta': {'operation': 'insert'}
        }

        result = supabase_client.table('journal').insert(entry_data).execute()

        assert result.data is not None
        assert len(result.data) == 1

        entry = result.data[0]
        assert entry['agent_name'] == 'TestAgent'
        assert entry['category'] == 'Test'
        assert 'id' in entry
        assert 'created_at' in entry

        # Cleanup
        supabase_client.table('journal').delete().eq('id', entry['id']).execute()

    def test_insert_alert(self, supabase_client, clean_test_data):
        """Test inserting an alert"""
        alert_data = {
            'ticker': 'TEST',
            'condition': 'below',
            'price': 50.0,
            'triggered': False
        }

        result = supabase_client.table('alerts').insert(alert_data).execute()

        assert result.data is not None
        assert len(result.data) == 1

        alert = result.data[0]
        assert alert['ticker'] == 'TEST'
        assert alert['condition'] == 'below'
        assert alert['price'] == 50.0
        assert alert['triggered'] is False

        # Cleanup
        supabase_client.table('alerts').delete().eq('id', alert['id']).execute()


@pytest.mark.supabase
@pytest.mark.integration
class TestSupabaseUpdateOperations:
    """Test updating Supabase records"""

    def test_update_journal_entry(self, supabase_client, test_journal_entry):
        """Test updating a journal entry"""
        entry_id = test_journal_entry['id']
        new_content = f'Updated at {datetime.now().isoformat()}'

        result = supabase_client.table('journal') \
            .update({'content': new_content}) \
            .eq('id', entry_id) \
            .execute()

        assert result.data is not None
        assert len(result.data) == 1
        assert result.data[0]['content'] == new_content

    def test_upsert_setting(self, supabase_client):
        """Test upserting a setting"""
        # Insert new setting
        result = supabase_client.table('settings') \
            .upsert({'key': 'test_setting', 'value': 'test_value'}) \
            .execute()

        assert result.data is not None

        # Update same setting
        result = supabase_client.table('settings') \
            .upsert({'key': 'test_setting', 'value': 'updated_value'}) \
            .execute()

        assert result.data is not None

        # Read back and verify
        result = supabase_client.table('settings') \
            .select('*') \
            .eq('key', 'test_setting') \
            .single() \
            .execute()

        assert result.data['value'] == 'updated_value'

        # Cleanup
        supabase_client.table('settings').delete().eq('key', 'test_setting').execute()


@pytest.mark.supabase
@pytest.mark.integration
class TestSupabaseDeleteOperations:
    """Test deleting from Supabase tables"""

    def test_delete_journal_entry(self, supabase_client):
        """Test deleting a journal entry"""
        # Create entry
        entry_data = {
            'agent_name': 'TestAgent',
            'category': 'Test',
            'content': 'Entry to be deleted',
        }
        result = supabase_client.table('journal').insert(entry_data).execute()
        entry_id = result.data[0]['id']

        # Delete entry
        supabase_client.table('journal').delete().eq('id', entry_id).execute()

        # Verify deletion
        result = supabase_client.table('journal') \
            .select('*') \
            .eq('id', entry_id) \
            .execute()

        assert len(result.data) == 0

    def test_delete_alert(self, supabase_client):
        """Test deleting an alert"""
        # Create alert
        alert_data = {
            'ticker': 'TEST',
            'condition': 'above',
            'price': 100.0,
            'triggered': False
        }
        result = supabase_client.table('alerts').insert(alert_data).execute()
        alert_id = result.data[0]['id']

        # Delete alert
        supabase_client.table('alerts').delete().eq('id', alert_id).execute()

        # Verify deletion
        result = supabase_client.table('alerts') \
            .select('*') \
            .eq('id', alert_id) \
            .execute()

        assert len(result.data) == 0


@pytest.mark.supabase
@pytest.mark.integration
class TestSupabaseComplexQueries:
    """Test complex Supabase queries"""

    def test_order_by(self, supabase_client):
        """Test ordering results"""
        result = supabase_client.table('journal') \
            .select('*') \
            .order('created_at', desc=True) \
            .limit(5) \
            .execute()

        assert result.data is not None
        # Verify descending order
        if len(result.data) >= 2:
            assert result.data[0]['created_at'] >= result.data[1]['created_at']

    def test_multiple_filters(self, supabase_client, test_journal_entry):
        """Test combining multiple filters"""
        result = supabase_client.table('journal') \
            .select('*') \
            .eq('agent_name', 'TestAgent') \
            .eq('category', 'Test') \
            .execute()

        assert result.data is not None
        assert all(entry['agent_name'] == 'TestAgent' for entry in result.data)
        assert all(entry['category'] == 'Test' for entry in result.data)

    def test_limit_and_offset(self, supabase_client):
        """Test pagination with limit and offset"""
        # Get first page
        page1 = supabase_client.table('journal') \
            .select('*') \
            .order('created_at', desc=True) \
            .limit(2) \
            .execute()

        # Get second page
        page2 = supabase_client.table('journal') \
            .select('*') \
            .order('created_at', desc=True) \
            .limit(2) \
            .range(2, 3) \
            .execute()

        assert page1.data is not None
        assert page2.data is not None

        # Pages should not overlap (if enough data exists)
        if len(page1.data) == 2 and len(page2.data) >= 1:
            page1_ids = {entry['id'] for entry in page1.data}
            page2_ids = {entry['id'] for entry in page2.data}
            assert page1_ids.isdisjoint(page2_ids)
