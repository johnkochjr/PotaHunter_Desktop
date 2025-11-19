"""
Simple diagnostic script to test CAT connection
Run this from command line to see detailed output about your radio connection
"""

import serial
import serial.tools.list_ports
import time

def list_ports():
    """List all available COM ports"""
    print("\n=== Available COM Ports ===")
    ports = serial.tools.list_ports.comports()
    if not ports:
        print("No COM ports found!")
        return []

    for i, port in enumerate(ports):
        print(f"{i+1}. {port.device}")
        print(f"   Description: {port.description}")
        print(f"   Manufacturer: {port.manufacturer}")
        print(f"   VID:PID: {port.vid}:{port.pid}" if port.vid else "")
        print()

    return [port.device for port in ports]

def test_kenwood(port, baud_rates=[9600, 19200, 38400, 57600, 115200]):
    """Test Kenwood protocol"""
    print(f"\n=== Testing Kenwood Protocol on {port} ===")

    for baud in baud_rates:
        print(f"\nTrying {baud} baud...")
        try:
            ser = serial.Serial(
                port=port,
                baudrate=baud,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=2.0
            )

            time.sleep(0.05)
            ser.reset_input_buffer()

            # Send IF command
            print(f"  Sending: IF;")
            ser.write(b"IF;")

            # Read response
            response = ser.read(100)
            print(f"  Received {len(response)} bytes: {response}")

            if response and len(response) >= 38:
                print(f"  ✓ SUCCESS! Got valid response")
                try:
                    freq_str = response[2:13].decode('ascii')
                    freq = float(freq_str)
                    print(f"  Frequency: {freq/1000000:.6f} MHz")
                    ser.close()
                    return baud
                except:
                    pass

            ser.close()

        except Exception as e:
            print(f"  ✗ Error: {e}")

    return None

def test_yaesu(port, baud_rates=[4800, 9600, 19200, 38400]):
    """Test Yaesu protocol"""
    print(f"\n=== Testing Yaesu Protocol on {port} ===")

    for baud in baud_rates:
        print(f"\nTrying {baud} baud...")
        try:
            ser = serial.Serial(
                port=port,
                baudrate=baud,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=2.0
            )

            # Yaesu radios need DTR and RTS off
            ser.dtr = False
            ser.rts = False

            time.sleep(0.05)
            ser.reset_input_buffer()

            # Send read status command
            command = bytes([0x00, 0x00, 0x00, 0x00, 0x03])
            print(f"  Sending: {command.hex()}")
            ser.write(command)

            # Read response
            response = ser.read(100)
            print(f"  Received {len(response)} bytes: {response.hex() if response else 'None'}")

            if response and len(response) >= 5:
                print(f"  ✓ SUCCESS! Got valid response")
                # Try to decode frequency from BCD
                try:
                    def bcd_to_int(byte):
                        return ((byte >> 4) * 10) + (byte & 0x0F)

                    freq = (bcd_to_int(response[0]) * 100000000 +
                           bcd_to_int(response[1]) * 1000000 +
                           bcd_to_int(response[2]) * 10000 +
                           bcd_to_int(response[3]) * 100)
                    freq_mhz = freq * 10 / 1000000
                    print(f"  Frequency: {freq_mhz:.6f} MHz")
                except:
                    pass
                ser.close()
                return baud

            ser.close()

        except Exception as e:
            print(f"  ✗ Error: {e}")

    return None

def test_icom(port, addresses=[0x94, 0xA4, 0xA2, 0x00], baud_rates=[4800, 9600, 19200]):
    """Test Icom CI-V protocol"""
    print(f"\n=== Testing Icom CI-V Protocol on {port} ===")

    for baud in baud_rates:
        for addr in addresses:
            print(f"\nTrying {baud} baud with address 0x{addr:02X}...")
            try:
                ser = serial.Serial(
                    port=port,
                    baudrate=baud,
                    bytesize=serial.EIGHTBITS,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE,
                    timeout=2.0
                )

                time.sleep(0.05)
                ser.reset_input_buffer()

                # Send read frequency command
                command = bytes([0xFE, 0xFE, addr, 0xE0, 0x03, 0xFD])
                print(f"  Sending: {command.hex()}")
                ser.write(command)

                # Read response
                response = ser.read(100)
                print(f"  Received {len(response)} bytes: {response.hex() if response else 'None'}")

                if response and len(response) >= 6 and response[0:2] == bytes([0xFE, 0xFE]):
                    print(f"  ✓ SUCCESS! Got valid response")
                    print(f"  Correct address: 0x{addr:02X}")
                    ser.close()
                    return (baud, addr)

                ser.close()

            except Exception as e:
                print(f"  ✗ Error: {e}")

    return None

def main():
    print("===========================================")
    print("CAT Connection Diagnostic Tool")
    print("===========================================")

    # List available ports
    ports = list_ports()

    if not ports:
        print("\nNo COM ports found. Make sure your radio is connected and drivers are installed.")
        return

    # Ask user to select port
    print("\nSelect a COM port to test (or 'q' to quit):")
    for i, port in enumerate(ports):
        print(f"{i+1}. {port}")

    try:
        choice = input("\nEnter port number: ").strip()
        if choice.lower() == 'q':
            return

        port_index = int(choice) - 1
        if port_index < 0 or port_index >= len(ports):
            print("Invalid selection")
            return

        selected_port = ports[port_index]

    except (ValueError, IndexError):
        print("Invalid input")
        return

    # Ask which protocol to test
    print("\nSelect protocol to test:")
    print("1. Kenwood")
    print("2. Yaesu")
    print("3. Icom CI-V")
    print("4. Test all protocols")

    try:
        protocol = input("\nEnter choice (1-4): ").strip()

        if protocol == '1':
            result = test_kenwood(selected_port)
            if result:
                print(f"\n✓✓✓ SUCCESS! Kenwood protocol working at {result} baud")
            else:
                print("\n✗✗✗ No successful connection with Kenwood protocol")

        elif protocol == '2':
            result = test_yaesu(selected_port)
            if result:
                print(f"\n✓✓✓ SUCCESS! Yaesu protocol working at {result} baud")
            else:
                print("\n✗✗✗ No successful connection with Yaesu protocol")

        elif protocol == '3':
            result = test_icom(selected_port)
            if result:
                baud, addr = result
                print(f"\n✓✓✓ SUCCESS! Icom protocol working at {baud} baud, address 0x{addr:02X}")
            else:
                print("\n✗✗✗ No successful connection with Icom protocol")

        elif protocol == '4':
            print("\n=== Testing all protocols ===")

            kenwood_result = test_kenwood(selected_port)
            yaesu_result = test_yaesu(selected_port)
            icom_result = test_icom(selected_port)

            print("\n" + "="*50)
            print("SUMMARY")
            print("="*50)

            if kenwood_result:
                print(f"✓ Kenwood: SUCCESS at {kenwood_result} baud")
            else:
                print("✗ Kenwood: Failed")

            if yaesu_result:
                print(f"✓ Yaesu: SUCCESS at {yaesu_result} baud")
            else:
                print("✗ Yaesu: Failed")

            if icom_result:
                baud, addr = icom_result
                print(f"✓ Icom: SUCCESS at {baud} baud, address 0x{addr:02X}")
            else:
                print("✗ Icom: Failed")

        else:
            print("Invalid choice")

    except Exception as e:
        print(f"\n✗ Error: {e}")

    print("\n===========================================")
    print("Diagnostic complete!")
    print("===========================================")

if __name__ == "__main__":
    main()
