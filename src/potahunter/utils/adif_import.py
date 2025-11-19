"""
ADIF file import utilities
"""

import re
from typing import List, Dict, Tuple
from potahunter.models.qso import QSO


class ADIFImporter:
    """Handles importing QSOs from ADIF format files"""

    @staticmethod
    def import_from_file(filename: str) -> Tuple[List[QSO], List[str]]:
        """
        Import QSOs from an ADIF file (.adi or .adif)

        Args:
            filename: Path to ADIF file

        Returns:
            Tuple of (list of QSO objects, list of error messages)
        """
        try:
            with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            return ADIFImporter.parse_adif_content(content)

        except Exception as e:
            return [], [f"Error reading file: {str(e)}"]

    @staticmethod
    def parse_adif_content(content: str) -> Tuple[List[QSO], List[str]]:
        """
        Parse ADIF content and extract QSOs

        Args:
            content: ADIF file content as string

        Returns:
            Tuple of (list of QSO objects, list of error messages)
        """
        qsos = []
        errors = []

        # Remove header (everything before <EOH>)
        content_upper = content.upper()
        if '<EOH>' in content_upper:
            # Find the position of <EOH> case-insensitively
            eoh_pos = content_upper.find('<EOH>')
            # Find the end of the <EOH> or <eoh> tag
            eoh_end = eoh_pos + 5  # Length of '<EOH>'
            content = content[eoh_end:]

        # Split into individual records using <EOR> marker
        records = re.split(r'<EOR>|<eor>', content, flags=re.IGNORECASE)

        for idx, record in enumerate(records):
            if not record.strip():
                continue

            try:
                # Parse fields from the record
                fields = ADIFImporter._parse_record(record)

                if fields:
                    # Create QSO object from parsed fields
                    qso = ADIFImporter._create_qso_from_fields(fields)
                    if qso:
                        # Mark as imported - do not upload to QRZ
                        qso.qrz_uploaded = True  # Set to True so it won't be uploaded
                        qsos.append(qso)
                    else:
                        errors.append(f"Record {idx + 1}: Missing required fields")
            except Exception as e:
                errors.append(f"Record {idx + 1}: {str(e)}")

        return qsos, errors

    @staticmethod
    def _parse_record(record: str) -> Dict[str, str]:
        """
        Parse an ADIF record into field dictionary

        Args:
            record: Single ADIF record string

        Returns:
            Dictionary of field names to values
        """
        fields = {}

        # Regular expression to match ADIF fields: <FIELDNAME:LENGTH[:TYPE]>VALUE
        # Pattern: <field_name:length>value or <field_name:length:type>value
        pattern = r'<([A-Za-z0-9_]+):(\d+)(?::[A-Za-z])?>([^<]*)'

        matches = re.finditer(pattern, record, re.IGNORECASE)

        for match in matches:
            field_name = match.group(1).upper()
            length = int(match.group(2))
            value = match.group(3)[:length]  # Only take specified length

            if value.strip():  # Only add non-empty values
                fields[field_name] = value.strip()

        return fields

    @staticmethod
    def _create_qso_from_fields(fields: Dict[str, str]) -> QSO:
        """
        Create a QSO object from parsed ADIF fields

        Args:
            fields: Dictionary of ADIF field names to values

        Returns:
            QSO object or None if required fields are missing
        """
        # Check for required fields
        required = ['CALL', 'QSO_DATE', 'TIME_ON', 'MODE']

        # Map common field variations
        if 'CALLSIGN' in fields and 'CALL' not in fields:
            fields['CALL'] = fields['CALLSIGN']

        for req in required:
            if req not in fields:
                return None

        # Get frequency - check both FREQ and FREQUENCY
        frequency = fields.get('FREQ') or fields.get('FREQUENCY', '0')

        # Automatically calculate band if not provided
        band = fields.get('BAND')
        if not band:
            band = QSO.frequency_to_band(frequency)

        # Create QSO object with mapped fields
        qso = QSO(
            # Required fields
            callsign=fields['CALL'].upper(),
            qso_date=fields['QSO_DATE'],
            time_on=fields['TIME_ON'],
            mode=fields['MODE'].upper(),
            frequency=frequency,

            # Core optional fields
            rst_sent=fields.get('RST_SENT', '59'),
            rst_rcvd=fields.get('RST_RCVD', '59'),

            # Timing fields
            time_off=fields.get('TIME_OFF'),
            qso_date_off=fields.get('QSO_DATE_OFF'),

            # Band and frequency
            band=band,
            band_rx=fields.get('BAND_RX'),
            freq_rx=fields.get('FREQ_RX'),
            submode=fields.get('SUBMODE'),

            # Contacted station information
            name=fields.get('NAME'),
            qth=fields.get('QTH'),
            state=fields.get('STATE'),
            county=fields.get('CNTY'),
            country=fields.get('COUNTRY'),
            dxcc=fields.get('DXCC'),
            cont=fields.get('CONT'),
            cqz=fields.get('CQZ'),
            gridsquare=fields.get('GRIDSQUARE'),
            lat=fields.get('LAT'),
            lon=fields.get('LON'),
            email=fields.get('EMAIL'),
            web=fields.get('WEB'),
            qsl_via=fields.get('QSL_VIA'),
            qsl_sent=fields.get('QSL_SENT'),

            # My station information
            my_callsign=fields.get('STATION_CALLSIGN'),
            operator=fields.get('OPERATOR'),
            my_gridsquare=fields.get('MY_GRIDSQUARE'),
            my_city=fields.get('MY_CITY'),
            my_state=fields.get('MY_STATE'),
            my_county=fields.get('MY_CNTY'),
            my_country=fields.get('MY_COUNTRY'),
            my_dxcc=fields.get('MY_DXCC'),
            my_lat=fields.get('MY_LAT'),
            my_lon=fields.get('MY_LON'),
            my_postal_code=fields.get('MY_POSTAL_CODE'),
            my_street=fields.get('MY_STREET'),
            my_rig=fields.get('MY_RIG'),
            tx_pwr=fields.get('TX_PWR'),
            ant_az=fields.get('ANT_AZ'),

            # POTA fields
            sig=fields.get('SIG'),
            sig_info=fields.get('SIG_INFO'),
            my_sig=fields.get('MY_SIG'),
            my_sig_info=fields.get('MY_SIG_INFO'),

            # Comments
            comment=fields.get('COMMENT'),

            # Set park_reference from SIG_INFO if SIG is POTA
            park_reference=fields.get('SIG_INFO') if fields.get('SIG') == 'POTA' else None,
        )

        return qso

    @staticmethod
    def validate_adif_file(filename: str) -> Tuple[bool, str]:
        """
        Validate that a file appears to be valid ADIF format

        Args:
            filename: Path to file to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(1000)  # Read first 1000 chars

            # Check for ADIF markers
            content_upper = content.upper()
            has_adif_markers = '<EOH>' in content_upper or '<EOR>' in content_upper
            has_field_format = re.search(r'<[A-Za-z_]+:\d+>', content, re.IGNORECASE)

            if not has_adif_markers and not has_field_format:
                return False, "File does not appear to be in ADIF format"

            return True, ""

        except Exception as e:
            return False, f"Error reading file: {str(e)}"
