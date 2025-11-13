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
                my_sig, my_sig_info, sig, sig_info
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            qso.callsign, qso.frequency, qso.mode, qso.qso_date, qso.time_on,
            qso.time_off, qso.rst_sent, qso.rst_rcvd, qso.park_reference,
            qso.gridsquare, qso.name, qso.comment, qso.qth, qso.state,
            qso.country, qso.band, qso.my_gridsquare, qso.my_sig,
            qso.my_sig_info, qso.sig, qso.sig_info
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

        qsos = []
        for row in rows:
            qso = QSO(
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
                id=row['id']
            )
            qsos.append(qso)

        return qsos

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
            id=row['id']
        )
