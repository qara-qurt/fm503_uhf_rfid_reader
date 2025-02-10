
class MonzaR6():
    def __init__(self) -> None:
        pass
    
    def interpret_TID(self, binary_TID_data):
        """
        Decode the upper 48 bytes of TID data
        """
        if not binary_TID_data or len(binary_TID_data) < 6:
            print("[ERROR] Invalid binary_TID_data:", binary_TID_data)
            return None  # Return None explicitly if data is invalid
        
        raw = binary_TID_data
        print("Raw lower_48 data:", raw)  # Debugging
        
        # Extract fields (as per the Monza TID documentation)
        try:
            class_identifier = raw[0]
            x = raw[1]
            s = raw[2]
            f = raw[3]
            mdid = raw[4]
            tmn = raw[5]
            epc_TD_standard_header = raw[6] if len(raw) > 6 else "0000000000000000"  # Prevent IndexError
            wafer_mask = raw[7] if len(raw) > 7 else "000"  # Prevent IndexError
            parity = raw[8] if len(raw) > 8 else "0"
            cycle_counter = raw[9] if len(raw) > 9 else "0"
            series_id = raw[10] if len(raw) > 10 else "00"
            reserved = raw[11] if len(raw) > 11 else "000"
            serial_num_38 = (raw[12] if len(raw) > 12 else "00000000000000000000000000000000000000")
            serial_num_96 = (raw[13] if len(raw) > 13 else "00000000000000000000000000000000000000")

            return [
                class_identifier, x, s, f, mdid, tmn, epc_TD_standard_header, wafer_mask,
                parity, cycle_counter, series_id, reserved, serial_num_38, serial_num_96
            ]
        
        except IndexError as e:
            print("[ERROR] Failed to parse binary_TID_data:", e)
            print("[DEBUG] Raw Data:", raw)
            return None


    def extract_38_Bit_serial_number(self, binary_TID_data) -> int:
        """
        input: binary string consisting of all 96 bits of TID data
        """
        return self.interpret_TID(binary_TID_data)[12]

    def extract_96_Bit_serial_number(self, binary_TID_data) -> int:
        """
        input: binary string consisting of all 96 bits of TID data
        """
        return self.interpret_TID(binary_TID_data)[13]
