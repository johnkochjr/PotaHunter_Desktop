"""
CAT (Computer Aided Transceiver) control service for amateur radio equipment

This module provides serial communication with amateur radios using various
CAT protocols including Kenwood, Yaesu, Icom, and generic CI-V protocols.
"""

import logging
import serial
import serial.tools.list_ports
from typing import Optional, Dict, List
from PySide6.QtCore import QObject, Signal, QTimer

logger = logging.getLogger(__name__)


class CATService(QObject):
    """Service for controlling amateur radio equipment via CAT protocol"""

    # Signals for frequency and mode changes
    frequency_changed = Signal(float)  # Frequency in Hz
    mode_changed = Signal(str)  # Mode (USB, LSB, CW, FM, AM, etc.)
    connection_status_changed = Signal(bool)  # True if connected, False if disconnected

    # Supported radio models with their CAT protocols
    #
    # Protocol options:
    #   - "kenwood": Kenwood ASCII protocol (e.g., FA;, MD;)
    #   - "yaesu": Yaesu binary protocol (BCD encoded)
    #   - "icom": Icom CI-V protocol
    #
    # Command overrides allow specific models to use commands from different protocols
    # Format: "command_name": "protocol_to_use"
    # Available commands: get_frequency, set_frequency, get_mode, set_mode
    RADIO_MODELS = {
        "Kenwood TS-480": {"protocol": "kenwood", "baud": 57600},
        "Kenwood TS-590": {"protocol": "kenwood", "baud": 115200},
        "Kenwood TS-890": {"protocol": "kenwood", "baud": 115200},
        "Yaesu FT-450": {"protocol": "yaesu", "baud": 38400},
        "Yaesu FT-891": {"protocol": "yaesu", "baud": 38400},
        "Yaesu FT-991": {"protocol": "yaesu", "baud": 38400},
        "Yaesu FT-DX10": {
            "protocol": "yaesu",
            "baud": 38400,
            # FT-DX10 uses Kenwood-compatible ASCII commands instead of Yaesu binary
            "commands": {
                "get_frequency": "kenwood",
                "set_frequency": "kenwood",
                "get_mode": "kenwood",
                "set_mode": "kenwood"
            }
        },
        "Icom IC-7300": {"protocol": "icom", "baud": 19200, "address": 0x94},
        "Icom IC-705": {"protocol": "icom", "baud": 19200, "address": 0xA4},
        "Icom IC-9700": {"protocol": "icom", "baud": 19200, "address": 0xA2},
        "Generic Kenwood": {"protocol": "kenwood", "baud": 9600},
        "Generic Yaesu": {"protocol": "yaesu", "baud": 4800},
        "Generic Icom": {"protocol": "icom", "baud": 19200, "address": 0x00},
    }

    # Mode mappings from radio-specific codes to standard modes SSB, CW, FT8, FT4, RTTY, AM, FM, etc.
    KENWOOD_MODES = {
        "1": "LSB", "2": "USB", "3": "CW", "4": "FM", "5": "AM",
        "6": "RTTY", "7": "CW-R", "8": "RTTY-R", "9": "DATA"
    }

    YAESU_MODES = {
        "01": "LSB", "02": "USB", "03": "CW", "04": "FM", "05": "AM",
        "06": "RTTY-LSB", "07": "CW-R", "08": "PKT-LSB", "09": "RTTY-USB",
        "0A": "PKT-FM", "0B": "FM-N", "0C": "PKT-USB", "0D": "AM-N",
        "82": "C4FM"
    }

    ICOM_MODES = {
        0x00: "LSB", 0x01: "USB", 0x02: "AM", 0x03: "CW",
        0x04: "RTTY", 0x05: "FM", 0x06: "WFM", 0x07: "CW-R",
        0x08: "RTTY-R", 0x17: "DATA"
    }

    def __init__(self):
        super().__init__()
        self.serial_port: Optional[serial.Serial] = None
        self.radio_model: Optional[str] = None
        self.protocol: Optional[str] = None
        self.radio_config: Optional[Dict] = None
        self.is_connected: bool = False
        self.current_frequency: float = 0.0
        self.current_mode: str = ""

        # Poll timer for reading radio status
        self.poll_timer = QTimer()
        self.poll_timer.timeout.connect(self._poll_radio)
        self.poll_interval = 2000  # 2 seconds - less frequent to reduce lag

    def _get_protocol_for_command(self, command_name: str) -> str:
        """
        Resolve which protocol to use for a specific command

        Args:
            command_name: Name of the command (e.g., "get_frequency", "set_mode")

        Returns:
            Protocol name to use for this command
        """
        if not self.radio_config:
            return self.protocol

        # Check if this radio has command-specific overrides
        commands = self.radio_config.get("commands", {})
        if command_name in commands:
            return commands[command_name]

        # Fall back to the radio's default protocol
        return self.protocol

    @staticmethod
    def get_available_ports() -> List[str]:
        """
        Get list of available serial ports

        Returns:
            List of port names (e.g., ['COM3', 'COM4'] on Windows or ['/dev/ttyUSB0'] on Linux)
        """
        ports = serial.tools.list_ports.comports()
        return [port.device for port in ports]

    @staticmethod
    def get_radio_models() -> List[str]:
        """
        Get list of supported radio models

        Returns:
            List of radio model names
        """
        return list(CATService.RADIO_MODELS.keys())

    @staticmethod
    def detect_baud_rate(port: str, radio_model: str) -> Optional[int]:
        """
        Try to auto-detect the correct baud rate for a radio

        Args:
            port: Serial port name
            radio_model: Radio model name

        Returns:
            Detected baud rate or None if detection failed
        """
        if radio_model not in CATService.RADIO_MODELS:
            return None

        radio_config = CATService.RADIO_MODELS[radio_model]
        protocol = radio_config["protocol"]

        # Check if this radio has command overrides for frequency reading
        commands = radio_config.get("commands", {})
        freq_protocol = commands.get("get_frequency", protocol)

        # Common baud rates to try, in order of likelihood
        # Use the frequency command protocol to determine which baud rates to try
        if freq_protocol == "kenwood":
            baud_rates = [57600, 115200, 38400, 19200, 9600, 4800]
        elif freq_protocol == "yaesu":
            baud_rates = [38400, 19200, 9600, 4800]
        elif freq_protocol == "icom":
            baud_rates = [19200, 9600, 4800]
        else:
            baud_rates = [9600, 19200, 38400, 57600, 4800]


        for baud_rate in baud_rates:
            try:
                ser = serial.Serial(
                    port=port,
                    baudrate=baud_rate,
                    bytesize=serial.EIGHTBITS,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE,
                    timeout=1.0,
                    write_timeout=1.0
                )

                # Set DTR/RTS based on radio manufacturer (base protocol)
                # Yaesu radios need DTR and RTS off regardless of protocol
                if protocol == "yaesu" or "Yaesu" in radio_model or "FT-" in radio_model:
                    ser.dtr = False
                    ser.rts = False
                else:
                    ser.dtr = True
                    ser.rts = True

                import time
                time.sleep(0.05)

                # Try to read frequency based on command protocol (not base protocol)
                ser.reset_input_buffer()

                if freq_protocol == "kenwood":
                    # Send FA; command and flush (per FT-DX10 working implementation)
                    ser.write(b"FA;")
                    ser.flush()
                    time.sleep(0.05)  # Short sleep after write
                    response = ser.read(128)
                    if response:
                        # Extract digits from response
                        text = response.decode('ascii', errors='replace')
                        digits = ''.join(ch for ch in text if ch.isdigit())
                        if digits and len(digits) >= 8:
                            ser.close()
                            return baud_rate

                elif freq_protocol == "yaesu":
                    ser.write(bytes([0x00, 0x00, 0x00, 0x00, 0x03]))
                    response = ser.read(28)
                    if response and len(response) >= 5:
                        ser.close()
                        return baud_rate

                elif freq_protocol == "icom":
                    address = radio_config.get("address", 0x00)
                    command = bytes([0xFE, 0xFE, address, 0xE0, 0x03, 0xFD])
                    ser.write(command)
                    response = ser.read(17)
                    if response and len(response) >= 6 and response[0:2] == bytes([0xFE, 0xFE]):
                        ser.close()
                        return baud_rate

                ser.close()

            except Exception as e:
                logger.error(f"Baud rate {baud_rate} failed: {e}")
                continue

        logger.warning("Could not auto-detect baud rate")
        return None

    def connect(self, port: str, radio_model: str, custom_baud: Optional[int] = None) -> bool:
        """
        Connect to radio via serial port

        Args:
            port: Serial port name (e.g., 'COM3' or '/dev/ttyUSB0')
            radio_model: Radio model name from RADIO_MODELS
            custom_baud: Optional custom baud rate (overrides model default)

        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Disconnect if already connected
            if self.is_connected:
                self.disconnect()

            # Get radio configuration
            if radio_model not in self.RADIO_MODELS:
                logger.error(f"Unsupported radio model: {radio_model}")
                return False

            self.radio_config = self.RADIO_MODELS[radio_model]
            self.radio_model = radio_model
            self.protocol = self.radio_config["protocol"]
            baud_rate = custom_baud if custom_baud else self.radio_config["baud"]

            # Open serial port
            try:
                self.serial_port = serial.Serial(
                    port=port,
                    baudrate=baud_rate,
                    bytesize=serial.EIGHTBITS,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE,
                    timeout=1.0,  # Increased timeout for slower radios
                    write_timeout=2.0,
                    exclusive=True,  # Prevent other apps from using the port
                    rtscts=False,
                    dsrdtr=False
                )
            except serial.SerialException as e:
                if "PermissionError" in str(e) or "Access is denied" in str(e):
                    logger.error(f"Port {port} is already in use by another application. Close Ham Radio Deluxe or other radio software.")
                    raise Exception(f"Port {port} is in use by another application")
                raise

            # Set DTR and RTS based on radio manufacturer
            # Yaesu radios need RTS and DTR off regardless of protocol used
            # Kenwood and Icom typically use DTR/RTS on
            if self.protocol == "yaesu" or "Yaesu" in self.radio_model or "FT-" in self.radio_model:
                self.serial_port.dtr = False
                self.serial_port.rts = False
            else:
                # Kenwood and Icom typically use DTR/RTS on
                self.serial_port.dtr = True
                self.serial_port.rts = True

            # Test connection by reading frequency (removed blocking sleep)
            freq = self.get_frequency()
            if freq is not None and freq > 0:
                self.is_connected = True
                self.current_frequency = freq
                self.connection_status_changed.emit(True)

                # Start polling timer - DISABLED for now to prevent lag
                # self.poll_timer.start(self.poll_interval)

                return True
            else:
                logger.error("Failed to communicate with radio")
                if self.serial_port:
                    self.serial_port.close()
                    self.serial_port = None
                return False

        except serial.SerialException as e:
            logger.error(f"Serial port error: {e}")
            if self.serial_port:
                self.serial_port.close()
                self.serial_port = None
            return False
        except Exception as e:
            logger.error(f"Unexpected error connecting to radio: {e}")
            if self.serial_port:
                self.serial_port.close()
                self.serial_port = None
            return False

    def disconnect(self):
        """Disconnect from radio"""
        self.poll_timer.stop()

        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()

        self.serial_port = None
        self.is_connected = False
        self.connection_status_changed.emit(False)

    def get_frequency(self) -> Optional[float]:
        """
        Get current frequency from radio

        Returns:
            Frequency in Hz, or None if error
        """
        if not self.serial_port:
            return None
        try:
            protocol = self._get_protocol_for_command("get_frequency")
            if protocol == "kenwood":
                return self._get_frequency_kenwood()
            elif protocol == "yaesu":
                return self._get_frequency_yaesu()
            elif protocol == "icom":
                return self._get_frequency_icom()
        except Exception as e:
            logger.error(f"Error reading frequency: {e}")
            return None

    def set_frequency(self, frequency: float) -> bool:
        """
        Set radio frequency

        Args:
            frequency: Frequency in Hz

        Returns:
            True if successful, False otherwise
        """
        if not self.is_connected or not self.serial_port:
            return False

        try:
            protocol = self._get_protocol_for_command("set_frequency")
            if protocol == "kenwood":
                return self._set_frequency_kenwood(frequency)
            elif protocol == "yaesu":
                return self._set_frequency_yaesu(frequency)
            elif protocol == "icom":
                return self._set_frequency_icom(frequency)
        except Exception as e:
            logger.error(f"Error setting frequency: {e}")
            return False

    def get_mode(self) -> Optional[str]:
        """
        Get current mode from radio

        Returns:
            Mode string (USB, LSB, CW, FM, AM, etc.), or None if error
        """
        logger.debug("Getting mode from radio")
        logger.debug(f"is_connected: {self.is_connected}, serial_port: {self.serial_port}, protocol: {self.protocol}")
        if not self.is_connected or not self.serial_port:
            return None

        try:
            protocol = self._get_protocol_for_command("get_mode")
            if protocol == "kenwood":
                return self._get_mode_kenwood()
            elif protocol == "yaesu":
                return self._get_mode_yaesu()
            elif protocol == "icom":
                return self._get_mode_icom()
        except Exception as e:
            logger.error(f"Error reading mode: {e}")
            return None

    def _resolve_mode_for_radio(self, mode: str) -> str:
        """
        Resolve mode strings to radio-appropriate modes based on current frequency

        Args:
            mode: The mode string (e.g., 'SSB', 'FT8', 'FT4', 'PSK31')

        Returns:
            Resolved mode appropriate for CAT control

        Conversions based on frequency:
        - 'SSB' → 'USB' or 'LSB'
        - 'FT8', 'FT4', 'PSK31', 'RTTY' → 'DATA-U' or 'DATA-L'
        - Other modes returned unchanged
        """
        mode_upper = mode.upper()

        # Digital modes that should be converted to DATA-U or DATA-L
        digital_modes = {'FT8', 'FT4', 'PSK31', 'PSK', 'RTTY', 'JS8', 'JS8CALL'}

        # Get current frequency to determine sideband
        freq = self.current_frequency if self.current_frequency > 0 else self.get_frequency()
        if not freq:
            # If we can't get frequency, assume upper sideband (safer default for modern bands)
            logger.warning(f"Cannot determine frequency for mode conversion, using upper sideband")
            freq_mhz = 14.0  # Default to 20m band
        else:
            freq_mhz = freq / 1_000_000

        if mode_upper == "SSB":
            # SSB voice mode
            resolved = "LSB" if freq_mhz < 10.0 else "USB"
            logger.info(f"Resolved SSB to {resolved} based on frequency {freq_mhz:.3f} MHz")
            return resolved
        elif mode_upper in digital_modes:
            # Digital modes use DATA-L or DATA-U
            resolved = "DATA-L" if freq_mhz < 10.0 else "DATA-U"
            logger.info(f"Resolved {mode} to {resolved} based on frequency {freq_mhz:.3f} MHz")
            return resolved

        return mode

    def set_mode(self, mode: str) -> bool:
        """
        Set radio mode

        Args:
            mode: Mode string (USB, LSB, CW, FM, AM, FT8, FT4, PSK31, etc.)

        Returns:
            True if successful, False otherwise
        """
        logger.debug(f"Setting mode to: {mode}")
        logger.debug(f"is_connected: {self.is_connected}, serial_port: {self.serial_port}, protocol: {self.protocol}")
        if not self.is_connected or not self.serial_port:
            return False

        try:
            # Resolve mode to radio-appropriate mode (SSB→USB/LSB, FT8→DATA-U/DATA-L, etc.)
            resolved_mode = self._resolve_mode_for_radio(mode)

            protocol = self._get_protocol_for_command("set_mode")
            logger.debug(f"Using protocol for set_mode: {protocol}")
            if protocol == "kenwood":
                return self._set_mode_kenwood(resolved_mode)
            elif protocol == "yaesu":
                return self._set_mode_yaesu(resolved_mode)
            elif protocol == "icom":
                return self._set_mode_icom(resolved_mode)
        except Exception as e:
            logger.error(f"Error setting mode: {e}")
            return False

    def _poll_radio(self):
        """Poll radio for frequency and mode changes"""
        if not self.is_connected:
            return

        # Read frequency
        freq = self.get_frequency()
        if freq and freq != self.current_frequency:
            self.current_frequency = freq
            self.frequency_changed.emit(freq)

        # Read mode
        mode = self.get_mode()
        if mode and mode != self.current_mode:
            self.current_mode = mode
            self.mode_changed.emit(mode)

    # Kenwood protocol implementation
    def _get_frequency_kenwood(self) -> Optional[float]:
        """Get frequency using Kenwood protocol"""
        try:
            # Flush input buffer
            self.serial_port.reset_input_buffer()

            # Send FA; command (VFO-A frequency read) - preferred for Yaesu radios
            self.serial_port.write(b"FA;")
            self.serial_port.flush()  # Ensure command is sent immediately

            # Short sleep after write (per FT-DX10 working implementation)
            import time
            time.sleep(0.05)

            # Read response (use 128 bytes like working implementation)
            response = self.serial_port.read(128)

            if not response:
                logger.warning("Kenwood: No response received")
                return None

            # Decode and extract digits (more robust than fixed-position parsing)
            try:
                text = response.decode('ascii', errors='replace')

                # Extract all digits from response
                digits = ''.join(ch for ch in text if ch.isdigit())

                if digits and len(digits) >= 8:  # Need at least 8 digits for valid frequency
                    # FT-DX10 returns 9 digits representing frequency in 100 Hz units
                    # Need to multiply by 100 to get actual frequency in Hz
                    freq_100hz = float(digits)
                    freq = freq_100hz * 100  # Convert from 100 Hz units to Hz
                    freq_mhz = freq / 1_000_000
                    return freq
                else:
                    logger.warning(f"Kenwood: Insufficient digits in response: {digits}")
            except Exception as parse_error:
                logger.error(f"Kenwood: Error parsing response: {parse_error}")

            return None
        except Exception as e:
            logger.error(f"Kenwood: Error reading frequency: {e}")
            return None

    def _set_frequency_kenwood(self, frequency: float) -> bool:
        """Set frequency using Kenwood protocol"""
        try:
            import time

            # Flush the input buffer to clear any pending data
            self.serial_port.reset_input_buffer()
            self.serial_port.reset_output_buffer()

            freq_int = int(frequency)

            # FT-DX10 uses Kenwood protocol with 9-digit format
            # The 9 digits represent frequency in 100 Hz units (not 10 Hz!)
            # Example: 14.304 MHz = 14,304,000 Hz ÷ 100 = 143,040 → "014304000"
            # Example: 7.243 MHz = 7,243,000 Hz ÷ 100 = 72,430 → "000724300"
            freq_100hz = freq_int 
            freq_str = f"{freq_100hz:09d}"  # Exactly 9 digits with leading zeros
            command = f"FA{freq_str};".encode('ascii')

            # First, read the current frequency to verify communication is working
            current_freq = self._get_frequency_kenwood()
            if current_freq:
                logger.info(f"Kenwood: Current radio frequency before set: {current_freq} Hz ({current_freq/1_000_000:.6f} MHz)")
            else:
                logger.warning(f"Kenwood: Could not read current frequency before attempting set")

            self.serial_port.write(command)
            self.serial_port.flush()

            # # Short delay - just enough for radio to respond if it will
            # time.sleep(0.1)

            # # Try to read any response/acknowledgment from radio
            # response = self.serial_port.read(128)
            # if response:
            #     # Check for error response
            #     if response == b'?;':
            #         logger.error(f"Kenwood: Radio rejected frequency command with '?;' error!")
            #         logger.error(f"Kenwood: This usually means frequency is out of range or radio is locked")
            #         logger.error(f"Kenwood: Check radio settings: band edges, frequency lock, or operating mode")
            #         return False
            # else:
            #     logger.warning(f"Kenwood: No response from radio after set frequency")

            # Verify the frequency was set by reading it back
            time.sleep(0.05)
            actual_freq = self._get_frequency_kenwood()
            if actual_freq:
                # Check if it's close (within 100 Hz tolerance for rounding)
                if abs(actual_freq - (frequency * 100)) < 100:
                    return True
                else:
                    return False
            else:
                logger.warning(f"Kenwood: Could not verify frequency was set")
                return False

        except Exception as e:
            logger.error(f"Kenwood: Error setting frequency: {e}")
            return False

    def _get_mode_kenwood(self) -> Optional[str]:
        """Get mode using Kenwood protocol IF; command"""
        import time
        try:
            logger.info("Kenwood: Getting mode with IF; command")
            # Flush input buffer
            self.serial_port.reset_input_buffer()
            self.serial_port.write(b"IF;")
            self.serial_port.flush()
            time.sleep(0.05)   # 50 ms
            response = self.serial_port.read(128)
            logger.debug(f"Kenwood: Received {len(response)} bytes: {response}")

            if response and len(response) >= 21:
                # IF; response format from FT-DX10: IF001018145000+000000200000;
                # Breaking this down:
                #   IF           - Command prefix
                #   00101814500  - Frequency (11 chars, positions 2-12)
                #   0            - Clarifier on/off (position 13)
                #   +000         - RIT/XIT offset (4 chars, positions 14-17)
                #   0            - RIT on/off (position 18)
                #   00           - Memory channel (2 chars, positions 19-20)
                #   2            - TX/RX status (position 21)
                #   0            - Mode digit 1 (position 22)
                #   0            - VFO/memory (position 23)
                #   000          - Other flags (positions 24-26)
                #   ;            - Terminator
                #
                # Wait - re-examining: IF001018145000+000000200000;
                # The actual spec says mode is at char positions 17-18 in the table
                # Let me map this exactly:
                #   P: 2  3  4  5  6  7  8  9 10 11 12 13 14 15 16 17 18 19 20 21 22
                #   C: 0  0  1  0  1  8  1  4  5  0  0  0  +  0  0  0  0  0  0  2  0
                #
                # The "Example" column shows: 02 at position "Operating Mode" 17-18
                # In your actual response the "02" appears at positions 20-21 (0-indexed from IF)
                try:
                    # Decode response
                    text = response.decode('ascii', errors='replace')
                    logger.debug(f"Kenwood: Full IF response: '{text}'")

                    # Check if response starts with "IF"
                    if text.startswith('IF') and len(text) >= 23:
                        # The mode appears at positions 20-21 (0-indexed from IF prefix start)
                        # That's positions 18-19 counting from after "IF"
                        mode_code = text[20:22]
                        logger.debug(f"Kenwood: Mode code from IF positions [20:22]: '{mode_code}'")

                        # Map mode code to mode name
                        mode_map = {
                            "01": "LSB",
                            "02": "USB",
                            "03": "CW-U",
                            "04": "FM",
                            "05": "AM",
                            "06": "RTTY-L",
                            "07": "CW-L",
                            "08": "DATA-L",
                            "09": "RTTY-U",
                            "10": "PSK",
                            "0C": "DATA-U"
                        }

                        mode = mode_map.get(mode_code, "UNKNOWN")
                        logger.info(f"Kenwood: Parsed mode: {mode} from code '{mode_code}'")
                        return mode
                    else:
                        logger.warning(f"Kenwood: Invalid IF response format: {text[:10]}")
                except Exception as parse_error:
                    logger.error(f"Kenwood: Error parsing IF response: {parse_error}")

            return None
        except Exception as e:
            logger.error(f"Kenwood: Error getting mode: {e}")
            return None

    def _set_mode_kenwood(self, mode: str) -> bool:
        """Set mode using Kenwood protocol MD command"""
        import time
        try:
            # Map mode name to code for MD command
            # MD command format: MD + code + ;
            mode_map = {
                "01": "LSB",
                "02": "USB",
                "03": "CW-U",
                "04": "FM",
                "05": "AM",
                "06": "RTTY-L",
                "07": "CW-L",
                "08": "DATA-L",
                "09": "RTTY-U",
                "10": "PSK",
                "0C": "DATA-U"
            }
            reverse_mode_map = {v: k for k, v in mode_map.items()}
    
            mode_code = reverse_mode_map.get(mode.upper().strip())
            if not mode_code:
                logger.warning(f"Kenwood: Unknown mode '{mode}'")
                return False

            # Send MD command
            command = f"MD{mode_code};".encode('ascii')
            logger.debug(f"Kenwood: Setting mode with command: {command}")

            self.serial_port.reset_input_buffer()
            self.serial_port.write(command)
            self.serial_port.flush()
            time.sleep(0.05)

            # Verify by reading back the mode
            actual_mode = self._get_mode_kenwood()
            if actual_mode and actual_mode.upper() == mode.upper():
                logger.info(f"Kenwood: Mode set successfully to {mode}")
                return True
            else:
                logger.warning(f"Kenwood: Mode verification failed. Expected {mode}, got {actual_mode}")
                return False

        except Exception as e:
            logger.error(f"Kenwood: Error setting mode: {e}")
            return False

    # Yaesu protocol implementation
    def _get_frequency_yaesu(self) -> Optional[float]:
        """Get frequency using Yaesu protocol"""
        try:
            # Flush input buffer
            self.serial_port.reset_input_buffer()

            logger.debug("Yaesu: Sending read status command")
            self.serial_port.write(bytes([0x00, 0x00, 0x00, 0x00, 0x03]))
            response = self.serial_port.read(28)
            logger.debug(f"Yaesu: Received {len(response)} bytes: {response.hex() if response else 'None'}")

            if response and len(response) >= 5:
                # BCD format: 4 bytes for frequency
                # Each byte contains two decimal digits in BCD format
                def bcd_to_int(byte):
                    return ((byte >> 4) * 10) + (byte & 0x0F)

                freq = (bcd_to_int(response[0]) * 100000000 +
                       bcd_to_int(response[1]) * 1000000 +
                       bcd_to_int(response[2]) * 10000 +
                       bcd_to_int(response[3]) * 100)
                result = float(freq) * 10  # Multiply by 10 to get Hz
                logger.debug(f"Yaesu: Parsed frequency: {result}")
                return result
            else:
                logger.warning(f"Yaesu: Invalid response length: {len(response)}")
            return None
        except Exception as e:
            logger.error(f"Yaesu: Error reading frequency: {e}")
            return None

    def _set_frequency_yaesu(self, frequency: float) -> bool:
        """Set frequency using Yaesu protocol"""
        def int_to_bcd(value):
            """Convert integer to BCD byte"""
            return ((value // 10) << 4) | (value % 10)

        freq_int = int(frequency / 10)
        b1 = int_to_bcd((freq_int // 100000000) % 100)
        b2 = int_to_bcd((freq_int // 1000000) % 100)
        b3 = int_to_bcd((freq_int // 10000) % 100)
        b4 = int_to_bcd((freq_int // 100) % 100)
        command = bytes([b1, b2, b3, b4, 0x01])
        self.serial_port.write(command)
        return True

    def _get_mode_yaesu(self) -> Optional[str]:
        """Get mode using Yaesu protocol"""
        self.serial_port.write(bytes([0x00, 0x00, 0x00, 0x00, 0x03]))
        response = self.serial_port.read(28)
        if response and len(response) >= 5:
            mode_code = f"{response[4]:02X}"
            return self.YAESU_MODES.get(mode_code, "UNKNOWN")
        return None

    def _set_mode_yaesu(self, mode: str) -> bool:
        """Set mode using Yaesu protocol"""
        mode_map = {v: k for k, v in self.YAESU_MODES.items()}
        mode_code = mode_map.get(mode.upper())
        if mode_code:
            mode_byte = int(mode_code, 16)
            command = bytes([mode_byte, 0x00, 0x00, 0x00, 0x07])
            self.serial_port.write(command)
            return True
        return False

    # Icom CI-V protocol implementation
    def _get_frequency_icom(self) -> Optional[float]:
        """Get frequency using Icom CI-V protocol"""
        try:
            radio_config = self.RADIO_MODELS.get(self.radio_model, {})
            address = radio_config.get("address", 0x00)

            # Flush input buffer
            self.serial_port.reset_input_buffer()

            # CI-V command: FE FE [radio] E0 03 FD
            command = bytes([0xFE, 0xFE, address, 0xE0, 0x03, 0xFD])
            logger.debug(f"Icom: Sending command: {command.hex()}")
            self.serial_port.write(command)
            response = self.serial_port.read(17)
            logger.debug(f"Icom: Received {len(response)} bytes: {response.hex() if response else 'None'}")

            if response and len(response) >= 11 and response[0:2] == bytes([0xFE, 0xFE]):
                # Extract BCD frequency (5 bytes)
                freq_bcd = response[6:11]
                freq = 0
                for i, byte in enumerate(freq_bcd):
                    freq += ((byte & 0x0F) + ((byte >> 4) * 10)) * (100 ** i)
                logger.debug(f"Icom: Parsed frequency: {freq}")
                return float(freq)
            else:
                logger.warning(f"Icom: Invalid response: {response.hex() if response else 'None'}")
            return None
        except Exception as e:
            logger.error(f"Icom: Error reading frequency: {e}")
            return None

    def _set_frequency_icom(self, frequency: float) -> bool:
        """Set frequency using Icom CI-V protocol"""
        radio_config = self.RADIO_MODELS.get(self.radio_model, {})
        address = radio_config.get("address", 0x00)

        # Convert frequency to BCD
        freq_int = int(frequency)
        bcd_bytes = []
        for _ in range(5):
            digit1 = (freq_int // 1) % 10
            digit2 = (freq_int // 10) % 10
            bcd_bytes.append((digit2 << 4) | digit1)
            freq_int //= 100

        # CI-V command: FE FE [radio] E0 05 [freq] FD
        command = bytes([0xFE, 0xFE, address, 0xE0, 0x05] + bcd_bytes + [0xFD])
        self.serial_port.write(command)
        return True

    def _get_mode_icom(self) -> Optional[str]:
        """Get mode using Icom CI-V protocol"""
        radio_config = self.RADIO_MODELS.get(self.radio_model, {})
        address = radio_config.get("address", 0x00)

        # CI-V command: FE FE [radio] E0 04 FD
        command = bytes([0xFE, 0xFE, address, 0xE0, 0x04, 0xFD])
        self.serial_port.write(command)
        response = self.serial_port.read(14)

        if response and len(response) >= 8 and response[0:2] == bytes([0xFE, 0xFE]):
            mode_byte = response[6]
            return self.ICOM_MODES.get(mode_byte, "UNKNOWN")
        return None

    def _set_mode_icom(self, mode: str) -> bool:
        """Set mode using Icom CI-V protocol"""
        radio_config = self.RADIO_MODELS.get(self.radio_model, {})
        address = radio_config.get("address", 0x00)

        mode_map = {v: k for k, v in self.ICOM_MODES.items()}
        mode_byte = mode_map.get(mode.upper())

        if mode_byte is not None:
            # CI-V command: FE FE [radio] E0 06 [mode] [filter] FD
            command = bytes([0xFE, 0xFE, address, 0xE0, 0x06, mode_byte, 0x01, 0xFD])
            self.serial_port.write(command)
            return True
        return False
