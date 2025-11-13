"""
Tests for QSO model
"""

import pytest
from potahunter.models.qso import QSO


def test_frequency_to_band():
    """Test frequency to band conversion"""
    assert QSO.frequency_to_band("14.260") == "20m"
    assert QSO.frequency_to_band("7.200") == "40m"
    assert QSO.frequency_to_band("3.850") == "80m"
    assert QSO.frequency_to_band("21.300") == "15m"
    assert QSO.frequency_to_band("28.400") == "10m"
    assert QSO.frequency_to_band("invalid") is None


def test_qso_creation():
    """Test creating a QSO object"""
    qso = QSO(
        callsign="W1AW",
        frequency="14.260",
        mode="SSB",
        qso_date="20231201",
        time_on="123000",
    )

    assert qso.callsign == "W1AW"
    assert qso.frequency == "14.260"
    assert qso.mode == "SSB"
    assert qso.qso_date == "20231201"
    assert qso.time_on == "123000"


def test_qso_to_dict():
    """Test QSO to dictionary conversion"""
    qso = QSO(
        callsign="K0XYZ",
        frequency="7.200",
        mode="CW",
        qso_date="20231201",
        time_on="140000",
        park_reference="K-0001",
    )

    qso_dict = qso.to_dict()

    assert qso_dict['callsign'] == "K0XYZ"
    assert qso_dict['frequency'] == "7.200"
    assert qso_dict['mode'] == "CW"
    assert qso_dict['park_reference'] == "K-0001"


def test_from_spot_data():
    """Test creating QSO from spot data"""
    spot_data = {
        'callsign': 'N0CALL',
        'frequency': '14.260',
        'mode': 'SSB',
        'park': 'K-0001',
    }

    qso = QSO.from_spot_data(spot_data)

    assert qso.callsign == 'N0CALL'
    assert qso.frequency == '14.260'
    assert qso.mode == 'SSB'
    assert qso.park_reference == 'K-0001'
    assert qso.band == '20m'
