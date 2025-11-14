"""
QRZ Logbook API upload service
"""

import requests
from typing import List, Optional, Dict
from datetime import datetime

from potahunter.models.qso import QSO


class QRZUploadService:
    """Service for uploading QSOs to QRZ Logbook"""

    BASE_URL = "https://logbook.qrz.com/api"

    def __init__(self, api_key: str = None):
        """
        Initialize QRZ upload service

        Args:
            api_key: QRZ Logbook API key
        """
        self.api_key = api_key

    def set_api_key(self, api_key: str):
        """
        Set the API key

        Args:
            api_key: QRZ Logbook API key
        """
        self.api_key = api_key

    def upload_qso(self, qso: QSO, station_callsign: str = None) -> Dict:
        """
        Upload a single QSO to QRZ Logbook

        Args:
            qso: QSO object to upload
            station_callsign: Your station callsign (if different from QRZ account)

        Returns:
            Dictionary with status and message
        """
        if not self.api_key:
            return {
                'success': False,
                'message': 'No API key configured'
            }

        # Build ADIF string for the QSO
        adif_fields = []

        # Calculate band from frequency if not set
        if not qso.band and qso.frequency:
            from potahunter.models.qso import QSO as QSOModel
            # Handle frequency that might be in kHz format
            freq_str = qso.frequency
            try:
                freq_float = float(freq_str)
                if freq_float > 1000:
                    # Convert kHz to MHz
                    freq_str = str(freq_float / 1000)
            except (ValueError, TypeError):
                pass
            qso.band = QSOModel.frequency_to_band(freq_str)

        # Required fields
        if qso.band:
            adif_fields.append(self._format_field('band', qso.band.upper()))
        if qso.mode:
            adif_fields.append(self._format_field('mode', qso.mode.upper()))
        if qso.callsign:
            adif_fields.append(self._format_field('call', qso.callsign.upper()))
        if qso.qso_date:
            adif_fields.append(self._format_field('qso_date', qso.qso_date))
        if qso.time_on:
            adif_fields.append(self._format_field('time_on', qso.time_on))

        # Optional fields
        if qso.frequency:
            # Ensure frequency is in MHz format
            try:
                freq_mhz = float(qso.frequency)
                # If frequency is > 1000, it's in kHz, convert to MHz
                if freq_mhz > 1000:
                    freq_mhz = freq_mhz / 1000
                adif_fields.append(self._format_field('freq', str(freq_mhz)))
                adif_fields.append(self._format_field('freq_rx', str(freq_mhz)))
            except:
                adif_fields.append(self._format_field('freq', qso.frequency))
        if qso.rst_sent:
            adif_fields.append(self._format_field('rst_sent', qso.rst_sent))
        if qso.rst_rcvd:
            adif_fields.append(self._format_field('rst_rcvd', qso.rst_rcvd))
        if qso.gridsquare:
            adif_fields.append(self._format_field('gridsquare', qso.gridsquare))
        if qso.name:
            adif_fields.append(self._format_field('name', qso.name))
        if qso.qth:
            adif_fields.append(self._format_field('qth', qso.qth))
        if qso.state:
            adif_fields.append(self._format_field('state', qso.state))
        if qso.country:
            adif_fields.append(self._format_field('country', qso.country))
        if qso.comment:
            adif_fields.append(self._format_field('comment', qso.comment))
        if qso.my_gridsquare:
            adif_fields.append(self._format_field('my_gridsquare', qso.my_gridsquare))

        # POTA-specific fields
        if qso.sig:
            adif_fields.append(self._format_field('sig', qso.sig))
        if qso.sig_info:
            adif_fields.append(self._format_field('sig_info', qso.sig_info))
        if qso.my_sig:
            adif_fields.append(self._format_field('my_sig', qso.my_sig))
        if qso.my_sig_info:
            adif_fields.append(self._format_field('my_sig_info', qso.my_sig_info))

        # Station callsign (optional)
        if station_callsign:
            adif_fields.append(self._format_field('station_callsign', station_callsign))

        # Build the ADIF string
        adif_string = ''.join(adif_fields) + '<eor>'

        # Build the request
        params = {
            'KEY': self.api_key,
            'ACTION': 'INSERT',
            'ADIF': adif_string
        }

        # Debug output
        print("\n" + "="*80)
        print("QRZ UPLOAD DEBUG")
        print("="*80)
        print(f"QSO: {qso.callsign} on {qso.qso_date} at {qso.time_on}")
        print(f"QSO Band: {qso.band}")
        print(f"QSO Mode: {qso.mode}")
        print(f"QSO Freq: {qso.frequency}")
        print(f"\nADIF String:\n{adif_string}")
        print(f"\nHTTP POST to: {self.BASE_URL}")
        print(f"Parameters:")
        print(f"  KEY: {self.api_key}")
        print(f"  ACTION: INSERT")
        print(f"  ADIF: {adif_string}")
        print("="*80 + "\n")

        try:
            response = requests.post(self.BASE_URL, data=params, timeout=10)

            # Debug response
            print(f"Response Status: {response.status_code}")
            print(f"Response Body: {response.text}")
            print("="*80 + "\n")

            # Check response
            if response.status_code == 200:
                result = response.text.strip()

                # QRZ API returns status in the response
                # Typical responses:
                # "OK" = success
                # "DUPLICATE" = duplicate contact
                # "INVALID" = invalid data
                # "FAIL" = general failure

                if 'OK' in result or 'REPLACE' in result:
                    return {
                        'success': True,
                        'message': f'QSO uploaded successfully',
                        'response': result
                    }
                elif 'DUPLICATE' in result:
                    return {
                        'success': False,
                        'message': 'Duplicate QSO (already exists in log)',
                        'response': result
                    }
                else:
                    return {
                        'success': False,
                        'message': f'Upload failed: {result}',
                        'response': result
                    }
            else:
                return {
                    'success': False,
                    'message': f'HTTP error: {response.status_code}'
                }

        except requests.exceptions.Timeout:
            return {
                'success': False,
                'message': 'Upload timed out'
            }
        except requests.exceptions.ConnectionError:
            return {
                'success': False,
                'message': 'Connection error - check internet connection'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Error: {str(e)}'
            }

    def upload_qsos(self, qsos: List[QSO], station_callsign: str = None) -> Dict:
        """
        Upload multiple QSOs to QRZ Logbook

        Args:
            qsos: List of QSO objects to upload
            station_callsign: Your station callsign (if different from QRZ account)

        Returns:
            Dictionary with upload statistics
        """
        results = {
            'total': len(qsos),
            'success': 0,
            'failed': 0,
            'duplicate': 0,
            'errors': []
        }

        for qso in qsos:
            result = self.upload_qso(qso, station_callsign)

            if result['success']:
                results['success'] += 1
            else:
                results['failed'] += 1
                if 'DUPLICATE' in result.get('response', ''):
                    results['duplicate'] += 1

                results['errors'].append({
                    'callsign': qso.callsign,
                    'date': qso.qso_date,
                    'time': qso.time_on,
                    'message': result['message']
                })

        return results

    @staticmethod
    def _format_field(name: str, value: str) -> str:
        """
        Format a single ADIF field for QRZ API

        Args:
            name: Field name
            value: Field value

        Returns:
            Formatted ADIF field string
        """
        if not value:
            return ''

        value_str = str(value)
        length = len(value_str)
        return f'<{name}:{length}>{value_str}'

    def validate_api_key(self) -> bool:
        """
        Test if the API key is valid

        Returns:
            True if API key is valid, False otherwise
        """
        if not self.api_key:
            return False

        # Create a test request with STATUS action
        params = {
            'KEY': self.api_key,
            'ACTION': 'STATUS'
        }

        try:
            response = requests.post(self.BASE_URL, data=params, timeout=10)
            if response.status_code == 200:
                result = response.text.strip()
                # Valid API key should return OK or other valid status
                return 'INVALID' not in result and 'AUTH' not in result
            return False
        except:
            return False
