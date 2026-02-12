"""
Tests for utility functions in app/dashboard/utils.py
"""
import pytest
from datetime import date


@pytest.mark.supabase
@pytest.mark.integration
class TestSettingsHelpers:
    """Test settings helper functions"""

    def test_get_settings(self, supabase_client):
        """Test getting settings"""
        from app.dashboard.utils import get_settings

        settings = get_settings()

        assert settings is not None
        assert 'account_equity' in settings
        assert 'risk_pct' in settings
        assert 'max_positions' in settings

        # Check default values are applied if missing
        assert settings['account_equity'] is not None
        assert settings['risk_pct'] is not None
        assert settings['max_positions'] is not None

    def test_update_setting(self, supabase_client):
        """Test updating a setting"""
        from app.dashboard.utils import update_setting, get_settings

        # Update setting
        result = update_setting('test_key', 'test_value')
        assert result is True

        # Verify update
        settings = get_settings()
        assert settings.get('test_key') == 'test_value'

        # Cleanup
        supabase_client.table('settings').delete().eq('key', 'test_key').execute()


@pytest.mark.supabase
@pytest.mark.integration
class TestAlertHelpers:
    """Test alert helper functions"""

    def test_get_all_alerts(self, supabase_client, test_alert):
        """Test getting all alerts"""
        from app.dashboard.utils import get_all_alerts

        alerts = get_all_alerts()

        assert alerts is not None
        assert isinstance(alerts, list)
        # Should include our test alert
        alert_ids = [a['id'] for a in alerts]
        assert test_alert['id'] in alert_ids

    def test_add_alert(self, supabase_client, clean_test_data):
        """Test adding an alert"""
        from app.dashboard.utils import add_alert

        alert = add_alert('TEST', 'above', 150.0)

        assert alert is not None
        assert alert['ticker'] == 'TEST'
        assert alert['condition'] == 'above'
        assert alert['price'] == 150.0
        assert alert['triggered'] is False

        # Cleanup
        supabase_client.table('alerts').delete().eq('id', alert['id']).execute()

    def test_delete_alert(self, supabase_client, test_alert):
        """Test deleting an alert"""
        from app.dashboard.utils import delete_alert

        result = delete_alert(test_alert['id'])
        assert result is True

        # Verify deletion
        alerts = supabase_client.table('alerts') \
            .select('*') \
            .eq('id', test_alert['id']) \
            .execute()
        assert len(alerts.data) == 0


@pytest.mark.supabase
@pytest.mark.integration
class TestPositionHelpers:
    """Test position helper functions"""

    def test_get_all_positions(self, supabase_client):
        """Test getting all positions"""
        from app.dashboard.utils import get_all_positions

        positions = get_all_positions()

        assert positions is not None
        assert isinstance(positions, list)

    def test_add_position(self, supabase_client, clean_test_data):
        """Test adding a position"""
        from app.dashboard.utils import add_position

        position_data = {
            'ticker': 'TEST',
            'entry_date': date.today().isoformat(),
            'entry_price': 100.0,
            'shares': 100,
            'cost_basis': 10000.0,
            'stop_price': 95.0,
            'status': 'open'
        }

        position = add_position(position_data)

        assert position is not None
        assert position['ticker'] == 'TEST'
        assert position['shares'] == 100

        # Cleanup
        supabase_client.table('positions').delete().eq('id', position['id']).execute()

    def test_get_positions_by_status(self, supabase_client):
        """Test filtering positions by status"""
        from app.dashboard.utils import get_all_positions

        # Create test positions with different statuses
        open_pos = {
            'ticker': 'TEST1',
            'entry_date': date.today().isoformat(),
            'entry_price': 100.0,
            'shares': 100,
            'cost_basis': 10000.0,
            'status': 'open'
        }

        closed_pos = {
            'ticker': 'TEST2',
            'entry_date': date.today().isoformat(),
            'entry_price': 100.0,
            'shares': 100,
            'cost_basis': 10000.0,
            'status': 'closed'
        }

        pos1 = supabase_client.table('positions').insert(open_pos).execute().data[0]
        pos2 = supabase_client.table('positions').insert(closed_pos).execute().data[0]

        # Test filtering
        open_positions = get_all_positions(status='open')
        assert any(p['id'] == pos1['id'] for p in open_positions)
        assert not any(p['id'] == pos2['id'] for p in open_positions)

        # Cleanup
        supabase_client.table('positions').delete().eq('id', pos1['id']).execute()
        supabase_client.table('positions').delete().eq('id', pos2['id']).execute()


@pytest.mark.supabase
@pytest.mark.integration
class TestScanHelpers:
    """Test scan helper functions"""

    def test_get_latest_scan(self, supabase_client):
        """Test getting latest scan"""
        from app.dashboard.utils import get_latest_scan

        scan = get_latest_scan()

        # May be None if no scans exist yet
        if scan:
            assert 'id' in scan
            assert 'market_regime' in scan
            assert 'scan_time' in scan

    def test_get_all_scans(self, supabase_client):
        """Test getting all scans"""
        from app.dashboard.utils import get_all_scans

        scans = get_all_scans(limit=10)

        assert scans is not None
        assert isinstance(scans, list)
        assert len(scans) <= 10
