"""
POTA API service for fetching spot data
"""

import requests
from typing import List, Dict, Optional
from datetime import datetime


class PotaAPIService:
    """Service for interacting with the POTA API"""

    BASE_URL = "https://api.pota.app"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'POTA-Hunter/0.1.0'
        })

    def get_spots(self, count: int = 100) -> List[Dict]:
        """
        Get active POTA spots

        Args:
            count: Maximum number of spots to retrieve (default 100)

        Returns:
            List of spot dictionaries
        """
        try:
            response = self.session.get(
                f"{self.BASE_URL}/spot/activator",
                timeout=10
            )
            response.raise_for_status()
            spots = response.json()

            # Limit to requested count
            return spots[:count] if spots else []

        except requests.RequestException as e:
            print(f"Error fetching spots: {e}")
            return []

    def get_park_info(self, park_reference: str) -> Optional[Dict]:
        """
        Get detailed information about a specific park

        Args:
            park_reference: Park reference code (e.g., "K-0001")

        Returns:
            Park information dictionary or None if not found
        """
        try:
            response = self.session.get(
                f"{self.BASE_URL}/park/{park_reference}",
                timeout=10
            )
            response.raise_for_status()
            return response.json()

        except requests.RequestException as e:
            print(f"Error fetching park info: {e}")
            return None

    def get_activator_stats(self, callsign: str) -> Optional[Dict]:
        """
        Get statistics for a specific activator

        Args:
            callsign: Amateur radio callsign

        Returns:
            Activator statistics or None if not found
        """
        try:
            response = self.session.get(
                f"{self.BASE_URL}/stats/user/{callsign}",
                timeout=10
            )
            response.raise_for_status()
            return response.json()

        except requests.RequestException as e:
            print(f"Error fetching activator stats: {e}")
            return None

    @staticmethod
    def parse_frequency(freq_str: str) -> Optional[float]:
        """
        Parse frequency string to float (in MHz)

        Args:
            freq_str: Frequency string (e.g., "14.260", "7.032")

        Returns:
            Frequency as float or None if invalid
        """
        try:
            return float(freq_str)
        except (ValueError, TypeError):
            return None
