# CAT Service Architecture

## Overview

The CAT (Computer Aided Transceiver) service provides serial communication with amateur radios using various CAT protocols. The architecture supports both standard protocols and hybrid radios that use commands from multiple protocols.

## Protocol System

### Base Protocols

Three base protocols are supported:

1. **Kenwood**: ASCII-based protocol using commands like `FA;`, `MD;`
2. **Yaesu**: Binary protocol using BCD (Binary Coded Decimal) encoding
3. **Icom**: CI-V protocol with binary commands

### Radio Configuration

Each radio model is configured with:
- `protocol`: Base protocol (kenwood, yaesu, or icom)
- `baud`: Default baud rate for the radio
- `commands` (optional): Dictionary of command-specific protocol overrides
- `address` (Icom only): CI-V address for the radio

### Command Override System

The command override system allows radios to use commands from different protocols for specific operations. This is essential for hybrid radios like the FT-DX10.

**Available command overrides:**
- `get_frequency`: Protocol for reading frequency
- `set_frequency`: Protocol for setting frequency
- `get_mode`: Protocol for reading mode
- `set_mode`: Protocol for setting mode

## Example: Yaesu FT-DX10

The FT-DX10 is a Yaesu radio but uses Kenwood-compatible ASCII commands instead of Yaesu binary protocol:

```python
"Yaesu FT-DX10": {
    "protocol": "yaesu",        # Base protocol for DTR/RTS control
    "baud": 38400,
    "commands": {                # All commands use Kenwood protocol
        "get_frequency": "kenwood",
        "set_frequency": "kenwood",
        "get_mode": "kenwood",
        "set_mode": "kenwood"
    }
}
```

**Why this matters:**
1. The base `protocol: "yaesu"` ensures DTR/RTS are set correctly (False for Yaesu radios)
2. The command overrides ensure Kenwood ASCII commands are used instead of Yaesu binary
3. The radio is properly classified as a Yaesu model
4. Code is clean and maintainable

## Implementation Details

### Protocol Resolution

The `_get_protocol_for_command(command_name)` method resolves which protocol to use:

1. Check if the radio has command-specific overrides in `radio_config["commands"]`
2. If override exists, return the override protocol
3. Otherwise, return the base protocol

### Command Methods

All command methods (`get_frequency`, `set_frequency`, `get_mode`, `set_mode`) use protocol resolution:

```python
def get_frequency(self) -> Optional[float]:
    protocol = self._get_protocol_for_command("get_frequency")
    if protocol == "kenwood":
        return self._get_frequency_kenwood()
    elif protocol == "yaesu":
        return self._get_frequency_yaesu()
    elif protocol == "icom":
        return self._get_frequency_icom()
```

### Baud Rate Detection

The `detect_baud_rate` static method also respects command overrides:

1. Gets the base protocol from radio config
2. Checks for `get_frequency` command override
3. Uses the appropriate protocol to test communication
4. Uses base protocol for DTR/RTS settings

## Adding New Hybrid Radios

To add a new radio that uses hybrid protocols:

1. Determine the base protocol (for DTR/RTS and general behavior)
2. Identify which commands use different protocols
3. Add radio configuration with command overrides

**Example: Hypothetical Icom radio that uses Kenwood frequency commands:**

```python
"Icom IC-XXXX": {
    "protocol": "icom",
    "baud": 19200,
    "address": 0x98,
    "commands": {
        "get_frequency": "kenwood",  # Uses Kenwood FA; command
        "set_frequency": "kenwood"   # Uses Kenwood FA command
        # get_mode and set_mode will use base "icom" protocol
    }
}
```

## Benefits of This Architecture

1. **Clean Organization**: Radios are classified by their manufacturer/family
2. **Flexibility**: Supports hybrid protocol radios without special cases
3. **Maintainability**: Easy to add new radios and protocol variations
4. **Clarity**: Command overrides are explicit and well-documented
5. **Correctness**: DTR/RTS settings are based on radio family, not command protocol

## Testing

Use the diagnostic script to test new radio configurations:

```bash
python test_cat_connection.py
```

The script will:
1. List available COM ports
2. Test the appropriate protocol(s) based on radio configuration
3. Show exact bytes sent/received
4. Verify frequency parsing

## Future Enhancements

Possible future improvements:
1. Per-command timeout overrides
2. Custom frequency format specifications (e.g., 9 digits vs 11 digits)
3. Protocol-specific initialization sequences
4. Command retry strategies per protocol
