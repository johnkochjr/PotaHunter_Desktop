# CAT Control Testing Guide

## Recent Architectural Improvements

### Latest Updates

**Intelligent Mode Resolution for SSB, CW, and Digital Modes** (Latest):
- POTA spots often report generic mode names like "SSB", "CW", or "FT8"
- The app now automatically resolves modes to radio-appropriate modes based on frequency:
  - **SSB**: Below 10 MHz → LSB (Lower Sideband), 10 MHz and above → USB (Upper Sideband)
  - **CW**: Below 10 MHz → CW-L (CW Lower), 10 MHz and above → CW-U (CW Upper)
  - **Digital modes** (FT8, FT4, PSK31, RTTY, JS8): Below 10 MHz → DATA-L, 10 MHz and above → DATA-U
- This follows standard amateur radio convention
- Conversion happens when setting the radio mode via CAT control
- Supported digital modes: FT8, FT4, PSK31, PSK, RTTY, JS8, JS8CALL

**Updated Kenwood mode detection to use IF; command**:
- Changed from `MD;` to `IF;` command for reading mode
- `IF;` returns comprehensive radio status in one command
- Parses mode from character positions 20-21 in the response
- More reliable than the older `MD;` command
- Also improved `MD` command for setting mode with verification

**Refactored protocol architecture to support model-specific command overrides**:

The FT-DX10 is now properly classified as a Yaesu radio but with command-level overrides for specific operations. This architecture makes the code cleaner and more maintainable.

**How it works**:
- Each radio has a base `protocol` classification (kenwood, yaesu, or icom)
- Radios can override specific commands using the `commands` dictionary
- Available command overrides: `get_frequency`, `set_frequency`, `get_mode`, `set_mode`
- The FT-DX10 uses base protocol "yaesu" but overrides all commands to use "kenwood" protocol

**Example configuration**:
```python
"Yaesu FT-DX10": {
    "protocol": "yaesu",        # Base protocol for DTR/RTS and general radio behavior
    "baud": 38400,
    "commands": {                # Command-specific overrides
        "get_frequency": "kenwood",
        "set_frequency": "kenwood",
        "get_mode": "kenwood",
        "set_mode": "kenwood"
    }
}
```

This approach allows hybrid protocol radios to be properly organized while maintaining compatibility.

### Previous Fixes

1. **CRITICAL: Frequency Format**: FT-DX10 uses **9 digits in 100 Hz units** (not 10 Hz!)
   - To send: Hz ÷ 100, format as 9 digits with leading zeros
   - To receive: 9 digits × 100 = Hz
   - Example: 14.304 MHz = 14,304,000 Hz ÷ 100 = 143,040 → "014304000"

2. **Implemented working FA; code**: Using exact approach from working implementation
   - FA; command with flush() after write
   - 0.05 second sleep after write (not before!)
   - Read 128 bytes
   - Extract digits only (robust parsing, not fixed positions)

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
