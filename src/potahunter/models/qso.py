"""
QSO (contact) data model
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class QSO:
    """Represents a single QSO (contact)"""

    callsign: str
    frequency: str
    mode: str
    qso_date: str  # YYYYMMDD format
    time_on: str  # HHMMSS format
    rst_sent: str = "59"
    rst_rcvd: str = "59"
    park_reference: Optional[str] = None
    gridsquare: Optional[str] = None
    name: Optional[str] = None
    comment: Optional[str] = None
    qth: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    band: Optional[str] = None
    time_off: Optional[str] = None
    my_gridsquare: Optional[str] = None
    my_sig: str = "POTA"
    my_sig_info: Optional[str] = None
    sig: Optional[str] = None
    sig_info: Optional[str] = None
    id: Optional[int] = None
    qrz_uploaded: bool = False
    qrz_upload_date: Optional[str] = None

    @staticmethod
    def from_spot_data(spot_data: dict, additional_data: dict = None) -> 'QSO':
        """
        Create a QSO from spot data

        Args:
            spot_data: Spot information from POTA API
            additional_data: Additional fields from logging dialog

        Returns:
            QSO instance
        """
        now = datetime.utcnow()
        qso_date = now.strftime("%Y%m%d")
        time_on = now.strftime("%H%M%S")

        freq = spot_data.get('frequency', '')
        band = QSO.frequency_to_band(freq)

        qso = QSO(
            callsign=spot_data.get('callsign', ''),
            frequency=freq,
            mode=spot_data.get('mode', ''),
            qso_date=qso_date,
            time_on=time_on,
            park_reference=spot_data.get('park', ''),
            band=band,
            sig="POTA",
            sig_info=spot_data.get('park', '')
        )

        # Add additional data if provided
        if additional_data:
            for key, value in additional_data.items():
                if hasattr(qso, key) and value:
                    setattr(qso, key, value)

        return qso

    @staticmethod
    def frequency_to_band(frequency: str) -> Optional[str]:
        """
        Convert frequency to band designation

        Args:
            frequency: Frequency string in MHz (e.g., "14.260")

        Returns:
            Band string (e.g., "20m") or None
        """
        try:
            freq = float(frequency)
        except (ValueError, TypeError):
            return None

        # Common amateur radio bands
        if 1.8 <= freq < 2.0:
            return "160m"
        elif 3.5 <= freq < 4.0:
            return "80m"
        elif 5.3 <= freq < 5.4:
            return "60m"
        elif 7.0 <= freq < 7.3:
            return "40m"
        elif 10.1 <= freq < 10.15:
            return "30m"
        elif 14.0 <= freq < 14.35:
            return "20m"
        elif 18.068 <= freq < 18.168:
            return "17m"
        elif 21.0 <= freq < 21.45:
            return "15m"
        elif 24.89 <= freq < 24.99:
            return "12m"
        elif 28.0 <= freq < 29.7:
            return "10m"
        elif 50.0 <= freq < 54.0:
            return "6m"
        elif 144.0 <= freq < 148.0:
            return "2m"
        elif 420.0 <= freq < 450.0:
            return "70cm"
        else:
            return None

    def to_dict(self) -> dict:
        """Convert QSO to dictionary for database storage"""
        return {
            'callsign': self.callsign,
            'frequency': self.frequency,
            'mode': self.mode,
            'qso_date': self.qso_date,
            'time_on': self.time_on,
            'rst_sent': self.rst_sent,
            'rst_rcvd': self.rst_rcvd,
            'park_reference': self.park_reference,
            'gridsquare': self.gridsquare,
            'name': self.name,
            'comment': self.comment,
            'qth': self.qth,
            'state': self.state,
            'country': self.country,
            'band': self.band,
            'time_off': self.time_off,
            'my_gridsquare': self.my_gridsquare,
            'my_sig': self.my_sig,
            'my_sig_info': self.my_sig_info,
            'sig': self.sig,
            'sig_info': self.sig_info,
        }
