"""
ADIF file export utilities
"""

from typing import List
from datetime import datetime
import os

from potahunter.models.qso import QSO
from potahunter.version import __version__, APP_NAME


class ADIFExporter:
    """Handles exporting QSOs to ADIF format"""

    ADIF_VERSION = "3.1.4"

    @staticmethod
    def export_to_file(qsos: List[QSO], filename: str) -> bool:
        """
        Export QSOs to an ADIF file

        Args:
            qsos: List of QSO objects
            filename: Output filename

        Returns:
            True if successful, False otherwise
        """
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                # Write ADIF header
                f.write(ADIFExporter._create_header())

                # Write each QSO
                for qso in qsos:
                    f.write(ADIFExporter._qso_to_adif(qso))

            return True

        except Exception as e:
            print(f"Error exporting ADIF: {e}")
            return False

    @staticmethod
    def _create_header() -> str:
        """Create ADIF file header"""
        now = datetime.utcnow()
        program_id_len = len(APP_NAME)
        version_len = len(__version__)
        header = f"""ADIF Export from {APP_NAME}
<ADIF_VER:{len(ADIFExporter.ADIF_VERSION)}>{ADIFExporter.ADIF_VERSION}
<PROGRAMID:{program_id_len}>{APP_NAME}
<PROGRAMVERSION:{version_len}>{__version__}
<CREATED_TIMESTAMP:15>{now.strftime('%Y%m%d %H%M%S')}
<EOH>

"""
        return header

    @staticmethod
    def _qso_to_adif(qso: QSO) -> str:
        """
        Convert a QSO object to ADIF record format

        Args:
            qso: QSO object

        Returns:
            ADIF formatted string
        """
        fields = []

        # Required fields
        fields.append(ADIFExporter._field('CALL', qso.callsign))
        fields.append(ADIFExporter._field('QSO_DATE', qso.qso_date))
        fields.append(ADIFExporter._field('TIME_ON', qso.time_on))
        fields.append(ADIFExporter._field('MODE', qso.mode))
        fields.append(ADIFExporter._field('FREQ', qso.frequency))

        # Core optional fields
        fields.append(ADIFExporter._field('RST_SENT', qso.rst_sent))
        fields.append(ADIFExporter._field('RST_RCVD', qso.rst_rcvd))

        # Timing fields
        if qso.time_off:
            fields.append(ADIFExporter._field('TIME_OFF', qso.time_off))
        if qso.qso_date_off:
            fields.append(ADIFExporter._field('QSO_DATE_OFF', qso.qso_date_off))

        # Band and frequency
        if qso.band:
            fields.append(ADIFExporter._field('BAND', qso.band))
        if qso.band_rx:
            fields.append(ADIFExporter._field('BAND_RX', qso.band_rx))
        if qso.freq_rx:
            fields.append(ADIFExporter._field('FREQ_RX', qso.freq_rx))
        if qso.submode:
            fields.append(ADIFExporter._field('SUBMODE', qso.submode))

        # Contacted station information
        if qso.name:
            fields.append(ADIFExporter._field('NAME', qso.name))
        if qso.qth:
            fields.append(ADIFExporter._field('QTH', qso.qth))
        if qso.state:
            fields.append(ADIFExporter._field('STATE', qso.state))
        if qso.county:
            fields.append(ADIFExporter._field('CNTY', qso.county))
        if qso.country:
            fields.append(ADIFExporter._field('COUNTRY', qso.country))
        if qso.dxcc:
            fields.append(ADIFExporter._field('DXCC', qso.dxcc))
        if qso.cont:
            fields.append(ADIFExporter._field('CONT', qso.cont))
        if qso.cqz:
            fields.append(ADIFExporter._field('CQZ', qso.cqz))
        if qso.gridsquare:
            fields.append(ADIFExporter._field('GRIDSQUARE', qso.gridsquare))
        if qso.lat:
            fields.append(ADIFExporter._field('LAT', qso.lat))
        if qso.lon:
            fields.append(ADIFExporter._field('LON', qso.lon))
        if qso.email:
            fields.append(ADIFExporter._field('EMAIL', qso.email))
        if qso.web:
            fields.append(ADIFExporter._field('WEB', qso.web))
        if qso.qsl_via:
            fields.append(ADIFExporter._field('QSL_VIA', qso.qsl_via))
        if qso.qsl_sent:
            fields.append(ADIFExporter._field('QSL_SENT', qso.qsl_sent))

        # My station information
        if qso.my_callsign:
            fields.append(ADIFExporter._field('STATION_CALLSIGN', qso.my_callsign))
        if qso.operator:
            fields.append(ADIFExporter._field('OPERATOR', qso.operator))
        if qso.my_gridsquare:
            fields.append(ADIFExporter._field('MY_GRIDSQUARE', qso.my_gridsquare))
        if qso.my_city:
            fields.append(ADIFExporter._field('MY_CITY', qso.my_city))
        if qso.my_state:
            fields.append(ADIFExporter._field('MY_STATE', qso.my_state))
        if qso.my_county:
            fields.append(ADIFExporter._field('MY_CNTY', qso.my_county))
        if qso.my_country:
            fields.append(ADIFExporter._field('MY_COUNTRY', qso.my_country))
        if qso.my_dxcc:
            fields.append(ADIFExporter._field('MY_DXCC', qso.my_dxcc))
        if qso.my_lat:
            fields.append(ADIFExporter._field('MY_LAT', qso.my_lat))
        if qso.my_lon:
            fields.append(ADIFExporter._field('MY_LON', qso.my_lon))
        if qso.my_postal_code:
            fields.append(ADIFExporter._field('MY_POSTAL_CODE', qso.my_postal_code))
        if qso.my_street:
            fields.append(ADIFExporter._field('MY_STREET', qso.my_street))
        if qso.my_rig:
            fields.append(ADIFExporter._field('MY_RIG', qso.my_rig))
        if qso.tx_pwr:
            fields.append(ADIFExporter._field('TX_PWR', qso.tx_pwr))
        if qso.ant_az:
            fields.append(ADIFExporter._field('ANT_AZ', qso.ant_az))

        # POTA-specific fields
        if qso.sig:
            fields.append(ADIFExporter._field('SIG', qso.sig))
        if qso.sig_info:
            fields.append(ADIFExporter._field('SIG_INFO', qso.sig_info))
        if qso.my_sig:
            fields.append(ADIFExporter._field('MY_SIG', qso.my_sig))
        if qso.my_sig_info:
            fields.append(ADIFExporter._field('MY_SIG_INFO', qso.my_sig_info))

        # Comments - append park information if present
        comment_text = qso.comment or ''

        # Append park reference to comments if present
        if qso.park_reference:
            if comment_text:
                comment_text += f" | Park: {qso.park_reference}"
            else:
                comment_text = f"Park: {qso.park_reference}"

        if comment_text:
            fields.append(ADIFExporter._field('COMMENT', comment_text))

        # Join all fields and add end of record marker
        return ''.join(fields) + '<EOR>\n\n'

    @staticmethod
    def _field(name: str, value: str) -> str:
        """
        Format a single ADIF field

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
        return f'<{name}:{length}>{value_str} '

    @staticmethod
    def get_adif_string(qsos: List[QSO]) -> str:
        """
        Generate ADIF content as string

        Args:
            qsos: List of QSO objects

        Returns:
            Complete ADIF file content as string
        """
        content = ADIFExporter._create_header()

        for qso in qsos:
            content += ADIFExporter._qso_to_adif(qso)

        return content

    @staticmethod
    def validate_adif_filename(filename: str) -> str:
        """
        Validate and correct ADIF filename

        Args:
            filename: Proposed filename

        Returns:
            Corrected filename with proper extension
        """
        base, ext = os.path.splitext(filename)

        # Ensure proper extension
        if ext.lower() not in ['.adi', '.adif']:
            filename = f"{filename}.adi"

        return filename
