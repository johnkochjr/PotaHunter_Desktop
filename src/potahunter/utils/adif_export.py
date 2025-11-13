"""
ADIF file export utilities
"""

from typing import List
from datetime import datetime
import os

from potahunter.models.qso import QSO


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
        header = f"""ADIF Export from POTA Hunter
<ADIF_VER:{len(ADIFExporter.ADIF_VERSION)}>{ADIFExporter.ADIF_VERSION}
<PROGRAMID:11>POTA Hunter
<PROGRAMVERSION:5>0.1.0
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

        # Optional fields
        if qso.time_off:
            fields.append(ADIFExporter._field('TIME_OFF', qso.time_off))

        if qso.band:
            fields.append(ADIFExporter._field('BAND', qso.band))

        if qso.rst_sent:
            fields.append(ADIFExporter._field('RST_SENT', qso.rst_sent))

        if qso.rst_rcvd:
            fields.append(ADIFExporter._field('RST_RCVD', qso.rst_rcvd))

        if qso.gridsquare:
            fields.append(ADIFExporter._field('GRIDSQUARE', qso.gridsquare))

        if qso.name:
            fields.append(ADIFExporter._field('NAME', qso.name))

        if qso.comment:
            fields.append(ADIFExporter._field('COMMENT', qso.comment))

        if qso.qth:
            fields.append(ADIFExporter._field('QTH', qso.qth))

        if qso.state:
            fields.append(ADIFExporter._field('STATE', qso.state))

        if qso.country:
            fields.append(ADIFExporter._field('COUNTRY', qso.country))

        # POTA-specific fields
        if qso.sig:
            fields.append(ADIFExporter._field('SIG', qso.sig))

        if qso.sig_info:
            fields.append(ADIFExporter._field('SIG_INFO', qso.sig_info))

        if qso.my_sig:
            fields.append(ADIFExporter._field('MY_SIG', qso.my_sig))

        if qso.my_sig_info:
            fields.append(ADIFExporter._field('MY_SIG_INFO', qso.my_sig_info))

        if qso.my_gridsquare:
            fields.append(ADIFExporter._field('MY_GRIDSQUARE', qso.my_gridsquare))

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
