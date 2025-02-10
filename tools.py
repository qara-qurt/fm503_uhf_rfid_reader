# Author: Taylor Lindley
# Date: 10/28/2023
# Description: This module provids basic tools for analyzing the lower 48 bytes of 
#    a TID block. There are also other generic tag operations. Nothing specific to a tag brand
#    or model number should be included here.


import time
import json
from knownTags import *


# open json file containing mask designer ID and tag model number info
mdid_json_file = open('mdid_list.json')
# list of designers (element 0 of each one is the MDID)
mdid_data = json.load(mdid_json_file)['registeredMaskDesigners']

# open tag info json
TID_data = json.load(open('TID_info.json'))['associations']

def mdid_lookup(mdid:str) -> tuple:
    """
    look up MDID in json file

    mdid: string binary representation of mdid

    return: (manufacturer name, index)
    """
    json_index = None
    manufacturer_name = None
    for index, designer in enumerate(mdid_data):
        if designer['mdid'] == mdid:
            json_index = index
            manufacturer_name = designer['manufacturer']
    return manufacturer_name, json_index

def model_lookup(mdid_index:int, tmn:str) -> tuple:
    """
    look up tag model number given a manufacturer and the binary 
    string representation of it's model number

    mdid_index: index of the tag manufacturer
    tmn: bniary string representation of tag model number 

    return: (tag model name,  index)
    """
    chips = mdid_data[mdid_index]['chips']
    for index, chip in enumerate(chips):
        if chip['tmnBinary'] == tmn:
            return chip['modelName'], index
        
def segment_TID_data(binary_string_output=False, input=False):
    """
    Reads TID bank from tag and segments into memory parts.

    - binary_string_output: If True, return as binary strings.
    - input: Binary string to segment.

    Returns:
        List of 7 elements: class ID, XTID, Security, File Indicator, MDID, TMN, XTID Header.
    """
    raw = input
    if len(raw) > 8:
        class_identifier = raw[0:8]
        x = raw[8]
        s = raw[9]
        f = raw[10]
        mdid = raw[11:20]
        tmn = raw[20:32]

        # Ensure 7 elements - XTID Header may be missing
        epc_TD_standard_header = raw[32:48] if len(raw) >= 48 else "0000000000000000"

        decoded_segments_bin = [class_identifier, x, s, f, mdid, tmn, epc_TD_standard_header]

        return decoded_segments_bin if binary_string_output else list(map(lambda x: int(x, 2), decoded_segments_bin))


def interpret_lower_48_TID(lower_48):
    """
    Interpret the lower 48 bits of the TID data.
    """
    print("Raw lower_48 data:", lower_48)  # Debugging
    print("Length of lower_48:", len(lower_48))  # Debugging

    # Ensure the list has at least 7 elements before accessing them
    if len(lower_48) < 7:
        print("[ERROR] lower_48 TID data has insufficient elements:", lower_48)
        return ["Error: Invalid Data"] * 7  # Return placeholders to prevent IndexError

    # Extract only the first 8 bits for lookup
    standard_key = lower_48[0][:8]  
    standard = TID_data['standard'].get(standard_key, "Unknown")

    x = TID_data['XTIDBit'].get(lower_48[1], "Unknown")
    s = TID_data['SecurityBit'].get(lower_48[2], "Unknown")
    f = TID_data['FileOpenBit'].get(lower_48[3], "Unknown")

    designer, mdid_index = mdid_lookup(lower_48[4])

    try:
        model_name = model_lookup(mdid_index, lower_48[5])[0]
    except:
        model_name = f"Unknown: {lower_48[5]}"

    binary_XTID = lower_48[6]  # Previously causing IndexError

    return [standard, x, s, f, designer, model_name, binary_XTID]



def interpret_XTID_header(binary_header:str) -> list:
    """
    given a binary string representation of the XTID header,
    decode and return arrayas describit the analyzed header

    binary_header: XTID header in binary string format (MSB is in element 0)

    returns: user readable analysis of XTID header data
    """
    # calculate XTID serialization length (actual bits may mean different things for different manufacturers)
    serialization_bits = binary_header[0:3]
    # calculate xtid serial length
    xtid_ser_length = 48 + ((int(serialization_bits,2)-1)*16)
    # see if optional commands are supported
    optional_commands_supported = "True" if (binary_header[3] == '1') else "False"
    # check if block write and block erase segment is included
    block_we = "True" if (binary_header[4] == '1') else "False"
    # is user memory and block perma lock present?
    user_mem_and_lock = "True" if (binary_header[5] == '1') else "False"
    # lock bit support?
    lock_bit_support = "True" if (binary_header[6] == '1') else "False"
    # 1-8 reserved for future use
    rfu = binary_header[6:14]
    # extended header present? this should be zero if compliant with TDS 2.0
    extended_xtid = "False" if (binary_header[15] == '1') else "True"

    #put into list and return
    return [xtid_ser_length, optional_commands_supported, block_we, user_mem_and_lock, lock_bit_support, rfu, extended_xtid]

def extract_serial_num(interpreted_TID_data:list, raw_bin_string:str) -> int:
    """
    given the manufacturere data (from interpreted_TID_data) extract the tags serial number
    from the raw binary string

    return: serial number
    """
    if interpreted_TID_data[4] == "Impinj":
        if interpreted_TID_data[5] == "Monza R6":
            # extract Monza R6 38-bit serial number
            return impinj_mr6.extract_38_Bit_serial_number(raw_bin_string)

    else:
        return None


green_button_style_shet = """QPushButton{
    background-color: #289c47;
    border-radius:4px;
    padding:4px;
}

QPushButton:hover{
    background-color: #58ae6f;
}"""

red_button_style_shet = """QPushButton{
    background-color: #9d2828;
    border-radius:4px;
    padding:4px;
}

QPushButton:hover{
    background-color: #a44a4a;
}"""

blue_button_style_shet = """QPushButton{
    background-color: #234cc4;
    border-radius:4px;
    padding:4px;
}

QPushButton:hover{
    background-color: #4565c4;
}"""

def flip_hex(input:str) -> str:
    """
    change endianess given a string of hex words as input
    """
    s = split_hex_string(input)
    b = ''
    for hex_word in s:
        b += bin(int(hex_word,16))[2:].zfill(16)
    # flip the binary string
    output = ''
    for i in range(1, len(b)+1):
        output += b[-i]
    return output

def split_hex_string(input_string:str) -> list:
    """
    Split a string of hex words into a list of words
    """
    hex_list = [input_string[i:i+4] for i in range(0, len(input_string), 4)]
    return hex_list

def crc16(data: bytes) -> int:
    """
    Calculate ISO/IEC 13239 CRC

    Defined by:
    initial CRC: 0xFFFF
    reflect input: False
    polynomial: 0x1021 (X^16+X^12+X^5+1)
    reflect output: False
    XOR output: 0xFFFF
    """
    # Define the polynomial (0x1021) used in CRC calculation
    poly = 0x1021
    # Initialize the CRC value to 0xFFFF
    crc = 0xFFFF

    # Iterate over each byte in the input data
    for byte in data:
        # Combine the current byte with the CRC register (XOR operation)
        # Shift left by 8 bits to process the next byte
        crc ^= byte << 8
        # Process each bit in the byte
        for _ in range(8):
            # Check if the leftmost bit of the CRC is a 1
            if (crc & 0x8000):
                # If set, shift CRC left by 1 and XOR with the polynomial
                crc = (crc << 1) ^ poly
            else:
                # If not set, shift the CRC left by 1
                crc = crc << 1
            
            # mask with 0xFFFF to keep the crc value 16 bits
            crc &= 0xFFFF

    # XOR the final crc value with 0xFFFF
    return crc ^ 0xFFFF

# actual_crc = 0x98C3
# input = '3000E280116060000211EBDD7175'
# input_bytes = bytes.fromhex(input)
# print(hex(crc16(input_bytes)))
# print(hex(crc16_man(input_bytes)))
