"""
QRZ XML API service for callsign lookups
"""
import requests
import xml.etree.ElementTree as ET
from typing import Optional, Dict
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class QRZAPIService:
    """Service for interacting with the QRZ XML API"""

    BASE_URL = "https://xmldata.qrz.com/xml/current/"

    def __init__(self):
        self.username = None
        self.password = None
        self.http_session = requests.Session()
        self._cache = {}  # Cache for callsign lookups
        self._cache_timeout = timedelta(hours=1)  # Cache timeout

    def set_credentials(self, username: str, password: str):
        """
        Set QRZ credentials

        Args:
            username: QRZ username
            password: QRZ password
        """
        self.username = username
        self.password = password
        self.session_key = None  # Reset session key

    def has_credentials(self) -> bool:
        """Check if credentials are set"""
        return bool(self.username and self.password)

    def lookup_callsign(self, callsign: str) -> Optional[Dict]:
        """
        Look up callsign information from QRZ (single-request method)

        Args:
            callsign: Amateur radio callsign

        Returns:
            Dictionary with callsign information or None if not found
        """
        if not self.has_credentials():
            logger.warning("Cannot lookup callsign: No credentials configured")
            return None

        # Check cache first
        callsign_upper = callsign.upper()
        if callsign_upper in self._cache:
            cached_data, cached_time = self._cache[callsign_upper]
            if datetime.now() - cached_time < self._cache_timeout:
                return cached_data

        try:
            # Single request with credentials and callsign
            params = {
                'username': self.username,
                'password': self.password,
                'callsign': callsign.upper()
            }

            response = self.http_session.get(self.BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            
            root = ET.fromstring(response.content)
            
            # QRZ XML has a namespace, need to handle it
            # Extract namespace from root tag
            namespace = ''
            if '}' in root.tag:
                namespace = root.tag.split('}')[0] + '}'


            # Check for session errors
            session = root.find(f'{namespace}Session')
            if session is not None:
                error = session.find(f'{namespace}Error')
                if error is not None:
                    logger.error(f"QRZ Error: {error.text}")
                    return None

                # Log session info for debugging
                key = session.find(f'{namespace}Key')
                

            # Parse callsign data
            callsign_data = root.find(f'{namespace}Callsign')
            if callsign_data is not None:
                data = self._parse_callsign_data(callsign_data, namespace)
                # Cache the result
                self._cache[callsign_upper] = (data, datetime.now())
                return data

            logger.warning(f"No callsign data found for {callsign}")
            # Cache negative result (with None) to avoid repeated lookups
            self._cache[callsign_upper] = (None, datetime.now())
            return None

        except requests.RequestException as e:
            logger.exception(f"QRZ Lookup request error for {callsign}: {e}")
            return None
        except ET.ParseError as e:
            logger.exception(f"QRZ XML parsing error for {callsign}: {e}")
            logger.error(f"Response content: {response.text}")
            return None
    
    def authenticate(self) -> bool:
        """
        Test authentication with QRZ (for settings dialog test)

        Returns:
            True if authentication successful, False otherwise
        """
        if not self.has_credentials():
            logger.warning("Cannot authenticate: No credentials set")
            return False

        try:

            # Just lookup a known callsign to test credentials
            params = {
                'username': self.username,
                'password': self.password,
                'callsign': 'W1AW'  # Test with a known callsign
            }

            response = self.http_session.get(self.BASE_URL, params=params, timeout=10)
            response.raise_for_status()

            root = ET.fromstring(response.content)

            # Extract namespace from root tag
            namespace = ''
            if '}' in root.tag:
                namespace = root.tag.split('}')[0] + '}'


            session = root.find(f'{namespace}Session')
            if session is not None:
                error = session.find(f'{namespace}Error')
                if error is not None:
                    logger.error(f"QRZ Auth Error: {error.text}")
                    return False

                key = session.find(f'{namespace}Key')
                if key is not None:
                    return True

            return False

        except requests.RequestException as e:
            logger.exception(f"QRZ Authentication request failed: {e}")
            return False
        except ET.ParseError as e:
            logger.exception(f"QRZ XML parsing error: {e}")
            return False
    

    def _parse_callsign_data(self, callsign_element, namespace: str = '') -> Dict:
        """
        Parse XML callsign element into dictionary

        Args:
            callsign_element: XML element containing callsign data
            namespace: XML namespace prefix (e.g., '{http://xmldata.qrz.com}')

        Returns:
            Dictionary with callsign information
        """
        data = {}

        # Map of XML tags to dictionary keys
        fields = {
            'call': 'callsign',
            'fname': 'first_name',
            'name': 'last_name',
            'addr1': 'address1',
            'addr2': 'address2',
            'state': 'state',
            'zip': 'zip',
            'country': 'country',
            'ccode': 'country_code',
            'lat': 'latitude',
            'lon': 'longitude',
            'grid': 'grid',
            'county': 'county',
            'fips': 'fips',
            'land': 'land',
            'efdate': 'effective_date',
            'expdate': 'expiration_date',
            'class': 'license_class',
            'codes': 'license_codes',
            'qslmgr': 'qsl_manager',
            'email': 'email',
            'url': 'url',
            'u_views': 'views',
            'bio': 'bio',
            'image': 'image_url',
            'moddate': 'modified_date',
            'MSA': 'msa',
            'AreaCode': 'area_code',
            'TimeZone': 'timezone',
            'GMTOffset': 'gmt_offset',
            'DST': 'dst',
            'eqsl': 'eqsl',
            'mqsl': 'mail_qsl',
            'cqzone': 'cq_zone',
            'ituzone': 'itu_zone',
            'born': 'born_year',
            'user': 'user',
            'lotw': 'lotw',
            'iota': 'iota',
            'geoloc': 'geoloc'
        }

        for xml_tag, dict_key in fields.items():
            element = callsign_element.find(f'{namespace}{xml_tag}')
            if element is not None and element.text:
                data[dict_key] = element.text.strip()

        return data

    def format_callsign_info(self, info: Dict) -> str:
        """
        Format callsign information for display with HTML links

        Args:
            info: Dictionary with callsign information

        Returns:
            HTML formatted string for display
        """
        if not info:
            return "No information available"

        lines = []

        # Name
        fname = info.get('first_name', '')
        lname = info.get('last_name', '')
        if fname or lname:
            lines.append(f"Name: {fname} {lname}".strip())

        # Location
        addr1 = info.get('address1', '')
        addr2 = info.get('address2', '')
        state = info.get('state', '')
        country = info.get('country', '')

        if addr1:
            lines.append(f"Address: {addr1}")
        if addr2:
            lines.append(f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{addr2}")
        if state or country:
            location = f"{state}, {country}" if state and country else (state or country)
            lines.append(f"Location: {location}")

        # Grid square
        if 'grid' in info:
            lines.append(f"Grid: {info['grid']}")

        # License info
        if 'license_class' in info:
            lines.append(f"Class: {info['license_class']}")

        # Email (clickable mailto link)
        if 'email' in info:
            email = info['email']
            lines.append(f"Email: <a href='mailto:{email}'>{email}</a>")

        # QSL info
        qsl_info = []
        if info.get('eqsl') == '1':
            qsl_info.append('eQSL')
        if info.get('lotw') == '1':
            qsl_info.append('LoTW')
        if info.get('mqsl') == '1':
            qsl_info.append('Mail')

        if qsl_info:
            lines.append(f"QSL: {', '.join(qsl_info)}")

        # QSL Manager (clickable mailto link if it looks like an email)
        if 'qsl_manager' in info:
            qsl_mgr = info['qsl_manager']
            # Check if it's an email address (contains @)
            if '@' in qsl_mgr:
                lines.append(f"QSL Mgr: <a href='mailto:{qsl_mgr}'>{qsl_mgr}</a>")
            else:
                lines.append(f"QSL Mgr: {qsl_mgr}")

        # Zones
        zones = []
        if 'cq_zone' in info:
            zones.append(f"CQ {info['cq_zone']}")
        if 'itu_zone' in info:
            zones.append(f"ITU {info['itu_zone']}")
        if zones:
            lines.append(f"Zones: {', '.join(zones)}")

        return '<br>'.join(lines)

    def get_image_url(self, info: Dict) -> str:
        """
        Get QSL card image URL from callsign info

        Args:
            info: Dictionary with callsign information

        Returns:
            Image URL string or empty string if not available
        """
        return info.get('image_url', '')
