"""
Database manager for storing QSO logs
"""

import sqlite3
import os
from typing import List, Optional
from datetime import datetime

from potahunter.models.qso import QSO


class DatabaseManager:
    """Manages SQLite database for QSO storage"""

    def __init__(self, db_path: str = None):
        """
        Initialize database manager

        Args:
            db_path: Path to SQLite database file. If None, uses default location.
        """
        if db_path is None:
            # Use data directory in project
            data_dir = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'data')
            os.makedirs(data_dir, exist_ok=True)
            db_path = os.path.join(data_dir, 'potahunter.db')

        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Create database tables if they don't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS qsos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                callsign TEXT NOT NULL,
                frequency TEXT NOT NULL,
                mode TEXT NOT NULL,
                qso_date TEXT NOT NULL,
                time_on TEXT NOT NULL,
                time_off TEXT,
                rst_sent TEXT,
                rst_rcvd TEXT,
                park_reference TEXT,
                gridsquare TEXT,
                name TEXT,
                comment TEXT,
                qth TEXT,
                state TEXT,
                country TEXT,
                band TEXT,
                my_gridsquare TEXT,
                my_sig TEXT,
                my_sig_info TEXT,
                sig TEXT,
                sig_info TEXT,
                qrz_uploaded INTEGER DEFAULT 0,
                qrz_upload_date TEXT,

                -- Contacted station fields
                county TEXT,
                dxcc TEXT,
                cont TEXT,
                cqz TEXT,
                lat TEXT,
                lon TEXT,
                email TEXT,
                web TEXT,
                qsl_via TEXT,
                qsl_sent TEXT,

                -- My station fields
                my_callsign TEXT,
                operator TEXT,
                my_city TEXT,
                my_state TEXT,
                my_county TEXT,
                my_country TEXT,
                my_dxcc TEXT,
                my_lat TEXT,
                my_lon TEXT,
                my_postal_code TEXT,
                my_street TEXT,
                my_rig TEXT,
                tx_pwr TEXT,
                ant_az TEXT,

                -- Technical fields
                band_rx TEXT,
                freq_rx TEXT,
                qso_date_off TEXT,
                submode TEXT,

                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Create index on callsign and date for faster queries
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_callsign_date
            ON qsos(callsign, qso_date)
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_park
            ON qsos(park_reference)
        ''')

        conn.commit()
        conn.close()

        # Migrate existing database if needed
        self._migrate_database()

    def _migrate_database(self):
        """Migrate database schema for new features"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Check existing columns
        cursor.execute("PRAGMA table_info(qsos)")
        columns = [column[1] for column in cursor.fetchall()]

        # QRZ columns
        if 'qrz_uploaded' not in columns:
            cursor.execute('ALTER TABLE qsos ADD COLUMN qrz_uploaded INTEGER DEFAULT 0')
        if 'qrz_upload_date' not in columns:
            cursor.execute('ALTER TABLE qsos ADD COLUMN qrz_upload_date TEXT')

        # Contacted station fields
        if 'county' not in columns:
            cursor.execute('ALTER TABLE qsos ADD COLUMN county TEXT')
        if 'dxcc' not in columns:
            cursor.execute('ALTER TABLE qsos ADD COLUMN dxcc TEXT')
        if 'cont' not in columns:
            cursor.execute('ALTER TABLE qsos ADD COLUMN cont TEXT')
        if 'cqz' not in columns:
            cursor.execute('ALTER TABLE qsos ADD COLUMN cqz TEXT')
        if 'lat' not in columns:
            cursor.execute('ALTER TABLE qsos ADD COLUMN lat TEXT')
        if 'lon' not in columns:
            cursor.execute('ALTER TABLE qsos ADD COLUMN lon TEXT')
        if 'email' not in columns:
            cursor.execute('ALTER TABLE qsos ADD COLUMN email TEXT')
        if 'web' not in columns:
            cursor.execute('ALTER TABLE qsos ADD COLUMN web TEXT')
        if 'qsl_via' not in columns:
            cursor.execute('ALTER TABLE qsos ADD COLUMN qsl_via TEXT')
        if 'qsl_sent' not in columns:
            cursor.execute('ALTER TABLE qsos ADD COLUMN qsl_sent TEXT')

        # My station fields
        if 'my_callsign' not in columns:
            cursor.execute('ALTER TABLE qsos ADD COLUMN my_callsign TEXT')
        if 'operator' not in columns:
            cursor.execute('ALTER TABLE qsos ADD COLUMN operator TEXT')
        if 'my_city' not in columns:
            cursor.execute('ALTER TABLE qsos ADD COLUMN my_city TEXT')
        if 'my_state' not in columns:
            cursor.execute('ALTER TABLE qsos ADD COLUMN my_state TEXT')
        if 'my_county' not in columns:
            cursor.execute('ALTER TABLE qsos ADD COLUMN my_county TEXT')
        if 'my_country' not in columns:
            cursor.execute('ALTER TABLE qsos ADD COLUMN my_country TEXT')
        if 'my_dxcc' not in columns:
            cursor.execute('ALTER TABLE qsos ADD COLUMN my_dxcc TEXT')
        if 'my_lat' not in columns:
            cursor.execute('ALTER TABLE qsos ADD COLUMN my_lat TEXT')
        if 'my_lon' not in columns:
            cursor.execute('ALTER TABLE qsos ADD COLUMN my_lon TEXT')
        if 'my_postal_code' not in columns:
            cursor.execute('ALTER TABLE qsos ADD COLUMN my_postal_code TEXT')
        if 'my_street' not in columns:
            cursor.execute('ALTER TABLE qsos ADD COLUMN my_street TEXT')
        if 'my_rig' not in columns:
            cursor.execute('ALTER TABLE qsos ADD COLUMN my_rig TEXT')
        if 'tx_pwr' not in columns:
            cursor.execute('ALTER TABLE qsos ADD COLUMN tx_pwr TEXT')
        if 'ant_az' not in columns:
            cursor.execute('ALTER TABLE qsos ADD COLUMN ant_az TEXT')

        # Technical fields
        if 'band_rx' not in columns:
            cursor.execute('ALTER TABLE qsos ADD COLUMN band_rx TEXT')
        if 'freq_rx' not in columns:
            cursor.execute('ALTER TABLE qsos ADD COLUMN freq_rx TEXT')
        if 'qso_date_off' not in columns:
            cursor.execute('ALTER TABLE qsos ADD COLUMN qso_date_off TEXT')
        if 'submode' not in columns:
            cursor.execute('ALTER TABLE qsos ADD COLUMN submode TEXT')

        conn.commit()
        conn.close()

    def add_qso(self, qso: QSO) -> int:
        """
        Add a QSO to the database

        Args:
            qso: QSO object to add

        Returns:
            ID of the inserted QSO
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO qsos (
                callsign, frequency, mode, qso_date, time_on, time_off,
                rst_sent, rst_rcvd, park_reference, gridsquare, name,
                comment, qth, state, country, band, my_gridsquare,
                my_sig, my_sig_info, sig, sig_info, qrz_uploaded, qrz_upload_date,
                county, dxcc, cont, cqz, lat, lon, email, web, qsl_via, qsl_sent,
                my_callsign, operator, my_city, my_state, my_county, my_country,
                my_dxcc, my_lat, my_lon, my_postal_code, my_street, my_rig,
                tx_pwr, ant_az, band_rx, freq_rx, qso_date_off, submode
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            qso.callsign, qso.frequency, qso.mode, qso.qso_date, qso.time_on,
            qso.time_off, qso.rst_sent, qso.rst_rcvd, qso.park_reference,
            qso.gridsquare, qso.name, qso.comment, qso.qth, qso.state,
            qso.country, qso.band, qso.my_gridsquare, qso.my_sig,
            qso.my_sig_info, qso.sig, qso.sig_info,
            1 if qso.qrz_uploaded else 0, qso.qrz_upload_date,
            qso.county, qso.dxcc, qso.cont, qso.cqz, qso.lat, qso.lon,
            qso.email, qso.web, qso.qsl_via, qso.qsl_sent,
            qso.my_callsign, qso.operator, qso.my_city, qso.my_state,
            qso.my_county, qso.my_country, qso.my_dxcc, qso.my_lat,
            qso.my_lon, qso.my_postal_code, qso.my_street, qso.my_rig,
            qso.tx_pwr, qso.ant_az, qso.band_rx, qso.freq_rx,
            qso.qso_date_off, qso.submode
        ))

        qso_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return qso_id

    def get_all_qsos(self) -> List[QSO]:
        """
        Retrieve all QSOs from database

        Returns:
            List of QSO objects
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM qsos ORDER BY qso_date DESC, time_on DESC')
        rows = cursor.fetchall()
        conn.close()

        return [self._row_to_qso(row) for row in rows]

    def get_qsos_by_date(self, start_date: str, end_date: str = None) -> List[QSO]:
        """
        Get QSOs within a date range

        Args:
            start_date: Start date in YYYYMMDD format
            end_date: End date in YYYYMMDD format (defaults to start_date)

        Returns:
            List of QSO objects
        """
        if end_date is None:
            end_date = start_date

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM qsos
            WHERE qso_date BETWEEN ? AND ?
            ORDER BY qso_date DESC, time_on DESC
        ''', (start_date, end_date))

        rows = cursor.fetchall()
        conn.close()

        return [self._row_to_qso(row) for row in rows]

    def get_qsos_by_park(self, park_reference: str) -> List[QSO]:
        """
        Get all QSOs for a specific park

        Args:
            park_reference: Park reference code (e.g., "K-0001")

        Returns:
            List of QSO objects
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM qsos
            WHERE park_reference = ?
            ORDER BY qso_date DESC, time_on DESC
        ''', (park_reference,))

        rows = cursor.fetchall()
        conn.close()

        return [self._row_to_qso(row) for row in rows]

    def update_qso(self, qso: QSO) -> bool:
        """
        Update an existing QSO in the database

        Args:
            qso: QSO object with updated data (must have id set)

        Returns:
            True if updated, False otherwise
        """
        if qso.id is None:
            raise ValueError("QSO must have an ID to update")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE qsos SET
                callsign = ?,
                frequency = ?,
                mode = ?,
                qso_date = ?,
                time_on = ?,
                time_off = ?,
                rst_sent = ?,
                rst_rcvd = ?,
                park_reference = ?,
                gridsquare = ?,
                name = ?,
                comment = ?,
                qth = ?,
                state = ?,
                country = ?,
                band = ?,
                my_gridsquare = ?,
                my_sig = ?,
                my_sig_info = ?,
                sig = ?,
                sig_info = ?,
                qrz_uploaded = ?,
                qrz_upload_date = ?,
                county = ?,
                dxcc = ?,
                cont = ?,
                cqz = ?,
                lat = ?,
                lon = ?,
                email = ?,
                web = ?,
                qsl_via = ?,
                qsl_sent = ?,
                my_callsign = ?,
                operator = ?,
                my_city = ?,
                my_state = ?,
                my_county = ?,
                my_country = ?,
                my_dxcc = ?,
                my_lat = ?,
                my_lon = ?,
                my_postal_code = ?,
                my_street = ?,
                my_rig = ?,
                tx_pwr = ?,
                ant_az = ?,
                band_rx = ?,
                freq_rx = ?,
                qso_date_off = ?,
                submode = ?
            WHERE id = ?
        ''', (
            qso.callsign, qso.frequency, qso.mode, qso.qso_date, qso.time_on,
            qso.time_off, qso.rst_sent, qso.rst_rcvd, qso.park_reference,
            qso.gridsquare, qso.name, qso.comment, qso.qth, qso.state,
            qso.country, qso.band, qso.my_gridsquare, qso.my_sig,
            qso.my_sig_info, qso.sig, qso.sig_info,
            1 if qso.qrz_uploaded else 0, qso.qrz_upload_date,
            qso.county, qso.dxcc, qso.cont, qso.cqz, qso.lat, qso.lon,
            qso.email, qso.web, qso.qsl_via, qso.qsl_sent,
            qso.my_callsign, qso.operator, qso.my_city, qso.my_state,
            qso.my_county, qso.my_country, qso.my_dxcc, qso.my_lat,
            qso.my_lon, qso.my_postal_code, qso.my_street, qso.my_rig,
            qso.tx_pwr, qso.ant_az, qso.band_rx, qso.freq_rx,
            qso.qso_date_off, qso.submode, qso.id
        ))

        updated = cursor.rowcount > 0
        conn.commit()
        conn.close()

        return updated

    def delete_qso(self, qso_id: int) -> bool:
        """
        Delete a QSO by ID

        Args:
            qso_id: ID of the QSO to delete

        Returns:
            True if deleted, False otherwise
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('DELETE FROM qsos WHERE id = ?', (qso_id,))
        deleted = cursor.rowcount > 0

        conn.commit()
        conn.close()

        return deleted

    def get_stats(self) -> dict:
        """
        Get statistics about the log

        Returns:
            Dictionary with statistics
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM qsos')
        total_qsos = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(DISTINCT park_reference) FROM qsos WHERE park_reference IS NOT NULL')
        total_parks = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(DISTINCT callsign) FROM qsos')
        total_callsigns = cursor.fetchone()[0]

        conn.close()

        return {
            'total_qsos': total_qsos,
            'total_parks': total_parks,
            'total_callsigns': total_callsigns
        }

    @staticmethod
    def _row_to_qso(row: sqlite3.Row) -> QSO:
        """Convert database row to QSO object"""
        return QSO(
            callsign=row['callsign'],
            frequency=row['frequency'],
            mode=row['mode'],
            qso_date=row['qso_date'],
            time_on=row['time_on'],
            time_off=row['time_off'],
            rst_sent=row['rst_sent'],
            rst_rcvd=row['rst_rcvd'],
            park_reference=row['park_reference'],
            gridsquare=row['gridsquare'],
            name=row['name'],
            comment=row['comment'],
            qth=row['qth'],
            state=row['state'],
            country=row['country'],
            band=row['band'],
            my_gridsquare=row['my_gridsquare'],
            my_sig=row['my_sig'],
            my_sig_info=row['my_sig_info'],
            sig=row['sig'],
            sig_info=row['sig_info'],
            id=row['id'],
            qrz_uploaded=bool(row['qrz_uploaded']) if 'qrz_uploaded' in row.keys() else False,
            qrz_upload_date=row['qrz_upload_date'] if 'qrz_upload_date' in row.keys() else None,
            # Contacted station fields
            county=row['county'] if 'county' in row.keys() else None,
            dxcc=row['dxcc'] if 'dxcc' in row.keys() else None,
            cont=row['cont'] if 'cont' in row.keys() else None,
            cqz=row['cqz'] if 'cqz' in row.keys() else None,
            lat=row['lat'] if 'lat' in row.keys() else None,
            lon=row['lon'] if 'lon' in row.keys() else None,
            email=row['email'] if 'email' in row.keys() else None,
            web=row['web'] if 'web' in row.keys() else None,
            qsl_via=row['qsl_via'] if 'qsl_via' in row.keys() else None,
            qsl_sent=row['qsl_sent'] if 'qsl_sent' in row.keys() else None,
            # My station fields
            my_callsign=row['my_callsign'] if 'my_callsign' in row.keys() else None,
            operator=row['operator'] if 'operator' in row.keys() else None,
            my_city=row['my_city'] if 'my_city' in row.keys() else None,
            my_state=row['my_state'] if 'my_state' in row.keys() else None,
            my_county=row['my_county'] if 'my_county' in row.keys() else None,
            my_country=row['my_country'] if 'my_country' in row.keys() else None,
            my_dxcc=row['my_dxcc'] if 'my_dxcc' in row.keys() else None,
            my_lat=row['my_lat'] if 'my_lat' in row.keys() else None,
            my_lon=row['my_lon'] if 'my_lon' in row.keys() else None,
            my_postal_code=row['my_postal_code'] if 'my_postal_code' in row.keys() else None,
            my_street=row['my_street'] if 'my_street' in row.keys() else None,
            my_rig=row['my_rig'] if 'my_rig' in row.keys() else None,
            tx_pwr=row['tx_pwr'] if 'tx_pwr' in row.keys() else None,
            ant_az=row['ant_az'] if 'ant_az' in row.keys() else None,
            # Technical fields
            band_rx=row['band_rx'] if 'band_rx' in row.keys() else None,
            freq_rx=row['freq_rx'] if 'freq_rx' in row.keys() else None,
            qso_date_off=row['qso_date_off'] if 'qso_date_off' in row.keys() else None,
            submode=row['submode'] if 'submode' in row.keys() else None
        )
