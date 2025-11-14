"""
Migration script to populate missing band fields from frequency
"""

from potahunter.models.database import DatabaseManager
from potahunter.models.qso import QSO


def migrate_bands():
    """
    Update all QSOs with missing band fields by calculating from frequency
    """
    db_manager = DatabaseManager()

    # Get all QSOs
    qsos = db_manager.get_all_qsos()

    updated_count = 0
    skipped_count = 0

    print(f"Found {len(qsos)} QSOs in database")
    print("Checking for missing band fields...")

    for qso in qsos:
        # Skip if band is already set
        if qso.band:
            skipped_count += 1
            continue

        # Skip if no frequency
        if not qso.frequency:
            print(f"Warning: QSO {qso.id} ({qso.callsign}) has no frequency, skipping")
            skipped_count += 1
            continue

        # Calculate band from frequency
        try:
            # Try to parse frequency and detect if it's in kHz vs MHz
            freq_float = float(qso.frequency)

            # If frequency is > 1000, it's likely in kHz, convert to MHz
            if freq_float > 1000:
                freq_mhz = freq_float / 1000
                print(f"Note: QSO {qso.id} frequency appears to be in kHz ({freq_float}), converting to MHz ({freq_mhz})")
                qso.frequency = str(freq_mhz)

            qso.band = QSO.frequency_to_band(qso.frequency)

            # Update in database
            if db_manager.update_qso(qso):
                print(f"Updated QSO {qso.id} ({qso.callsign}): {qso.frequency} MHz -> {qso.band}")
                updated_count += 1
            else:
                print(f"Failed to update QSO {qso.id}")
        except Exception as e:
            print(f"Error processing QSO {qso.id} ({qso.callsign}): {e}")

    print("\n" + "="*60)
    print(f"Migration complete!")
    print(f"Updated: {updated_count} QSOs")
    print(f"Skipped: {skipped_count} QSOs (already had band or no frequency)")
    print("="*60)


if __name__ == "__main__":
    print("="*60)
    print("Band Field Migration Script")
    print("="*60)
    print("This script will update all QSOs with missing band fields")
    print("by calculating the band from the frequency.")
    print("="*60 + "\n")

    response = input("Continue? (y/n): ")
    if response.lower() == 'y':
        migrate_bands()
    else:
        print("Migration cancelled")
