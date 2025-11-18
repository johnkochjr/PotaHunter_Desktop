# CAT Control Testing Guide

## Recent Fixes

I've just fixed several critical issues with the FT-DX10 CAT implementation:

1. **MAJOR: Protocol Change**: Changed FT-DX10 to use **Kenwood ASCII protocol** instead of Yaesu binary
   - The FT-DX10 uses ASCII commands like "FA;" (Kenwood-compatible)
   - Not the binary Yaesu protocol used by older radios
   - Added fallback option "Yaesu FT-DX10 (Binary)" if you want to try binary mode

2. **CRITICAL: Implemented your working FA; code**: Now using **exact same approach** as your working implementation
   - FA; command with flush() after write
   - 0.05 second sleep after write (not before!)
   - Read 128 bytes
   - Extract digits only (robust parsing, not fixed positions)
   - Based on your proven working code for FT-DX10

3. **BCD Encoding/Decoding**: Fixed improper BCD (Binary Coded Decimal) conversion for binary Yaesu protocol
   - Now properly decoding: `0x14` = 14 (not 20)

4. **DTR/RTS Control**: Set to False for ALL Yaesu radios regardless of protocol used
   - Critical for USB serial connections

5. **Diagnostic Script**: Updated test script with proper DTR/RTS and BCD decoding

## Testing Steps

### Option 1: Test with Diagnostic Script (Recommended First)

This will show you exactly what's happening at the protocol level:

1. **Close Ham Radio Deluxe** (or any other software using the COM port)

2. Run the diagnostic script:
   ```bash
   python test_cat_connection.py
   ```

3. Select COM5 when prompted

4. Select option 2 (Test Yaesu) or option 4 (Test all protocols)

5. The script will show:
   - Exact bytes sent to the radio
   - Exact bytes received from the radio
   - Decoded frequency if successful

### Option 2: Test in Application

1. **Close Ham Radio Deluxe** first

2. Open POTA Hunter

3. Go to Tools → Settings → CAT Control tab

4. Configure:
   - Radio Model: Yaesu FT-DX10
   - COM Port: COM5
   - Baud Rate: 38400
   - Enable CAT control: ✓

5. Click "Test Connection"

## What Changed

### Before (Broken):
```python
# Wrong - treating BCD bytes as raw integers
freq = (response[0] * 100000000 + response[1] * 1000000 + ...)
# Example: byte 0x14 would be interpreted as 20 (0x14 = 20 decimal)
```

### After (Fixed):
```python
# Correct - converting BCD to decimal
def bcd_to_int(byte):
    return ((byte >> 4) * 10) + (byte & 0x0F)

freq = (bcd_to_int(response[0]) * 100000000 + bcd_to_int(response[1]) * 1000000 + ...)
# Example: byte 0x14 is now correctly interpreted as 14
```

## Expected Results

For a radio on 14.074 MHz (FT8 frequency):
- Hex response might be: `01 40 74 00 ...` (BCD format)
- Decoded: 01 = 01, 40 = 40, 74 = 74, 00 = 00
- Frequency: 01407400 × 10 = 14,074,000 Hz = 14.074 MHz

## Troubleshooting

### Still not working?

1. **Verify COM port**: In Device Manager, confirm the radio shows as COM5

2. **Check radio CAT settings**:
   - CAT enabled in radio menu
   - CAT baud rate: 38400
   - CAT RTS: OFF (you confirmed this)

3. **Check USB cable**: Some cheap USB cables are charge-only and don't pass data

4. **Try different baud rates**: Even though radio says 38400, try others:
   - 9600 (common default)
   - 4800
   - 19200

5. **Check radio CAT mode**: Some Yaesu radios have different CAT modes (FT-DX10 should use standard)

## Common Error Messages

- **"Port in use"**: Close Ham Radio Deluxe or other radio software
- **"Connection failed"**: Wrong baud rate, or radio CAT not enabled
- **"No response"**: Check USB cable, drivers, or COM port number

## Next Steps

After testing with the diagnostic script, we'll see exactly what the radio is returning and can fine-tune if needed.
