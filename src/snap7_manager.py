import json
import struct
import re

import snap7

class Snap7Manager:
    def __init__(self, ip, rack, slot, db_number):
        self.scheme = None
        self.scheme_flat = None
        
        self._array_check_pattern = re.compile(r'^Array')
        self._array_size_pattern = re.compile(r'\[0\.\.(\d+)\]')
        self._array_datatype_pattern = re.compile(r"of (\w+)")
        # self._string_check_pattern = re.compile(r'^String')
        
        self.db_number = db_number
        self.plc = snap7.client.Client()
        self.plc.connect(ip, rack, slot)
        
        self._datatype_read_map = {
            'Bool'          : self.read_bool,
            'Byte'          : self.read_byte,
            'Char'          : self.read_char,
            'DInt'          : self.read_dint,
            'DWord'         : self.read_dword,
            # 'Date'          : TODO:
            # 'Date_And_Time' : TODO:
            'Int'           : self.read_int,
            'LInt'          : self.read_lint,
            'LReal'         : self.read_lreal,
            # 'LTime'         : TODO:
            # 'LTime_Of_Day'  : TODO:
            'LWord'         : self.read_lword,
            'Real'          : self.read_real,
            'SInt'          : self.read_sint,
            'String'        : self.read_string,
            # 'Time'          : TODO:
            # 'Time_Of_Day'   : TODO:
            'UDInt'         : self.read_udint,
            'UInt'          : self.read_uint,
            'ULInt'         : self.read_ulint,
            'USInt'         : self.read_usint,
            'WChar'         : self.read_wchar,
            # 'WString'       : TODO:
            'Word'          : self.read_word,
        }
        
        self._datatype_write_map = {
            'Bool'          : self.write_bool,
            'Byte'          : self.write_byte,
            'Char'          : self.write_char,
            'DInt'          : self.write_dint,
            'DWord'         : self.write_dword,
            # 'Date'          : TODO:
            # 'Date_And_Time' : TODO:
            'Int'           : self.write_int,
            'LInt'          : self.write_lint,
            'LReal'         : self.write_lreal,
            # 'LTime'         : TODO:
            # 'LTime_Of_Day'  : TODO:
            'LWord'         : self.write_lword,
            'Real'          : self.write_real,
            'SInt'          : self.write_sint,
            'String'        : self.write_string,
            # 'Time'          : TODO:
            # 'Time_Of_Day'   : TODO:
            'UDInt'         : self.write_udint,
            'UInt'          : self.write_uint,
            # 'ULInt'         : self.write_ulint, FIXME: see bellow
            'USInt'         : self.write_usint,
            # 'WChar'         : self.write_wchar, FIXME: see below
            # 'WString'       : TODO:
            'Word'          : self.write_word,
        }
        
    def load(self, json_path: str):
        """loads json which defines read/write structure.
        
        example:
        [
            {
                "name": "var_string",
                "datatype": "String",
                "offset": 0.0
            },
            {
                "var_bool": "bl1",
                "datatype": "Bool",
                "offset": 256.0
            },
            {
                "var_bool": "bl2",
                "datatype": "Bool",
                "offset": 256.1
            },
            {
                "name": "var_struct",
                "datatype": "Struct",
                "offset": 260.0,
                "children": [
                    {
                        "name": "var_struct_string",
                        "datatype": "String",
                        "offset": 260.0
                    },
                    {
                        "name": "var_struct_bool",
                        "datatype": "Bool",
                        "offset": 516.0
                    }
                ]
            }
        ]
        

        Args:
            json_path (str): path to json structure
        """
        with open(json_path, 'r') as fp:
            self.scheme = json.load(fp)
            
            # flatten data for write direction
            flat_data = {}
            self._flatten_data(flat_data, self.scheme)
            self.scheme_flat = flat_data
        
        
    def read(self) -> dict:
        """reads from plc using scheme got by self.load() method
        
        FIXME: WONT READ Array AT THE MOMENT

        Raises:
            Exception: raises if self.load() not called

        Returns:
            dict: dictionary - key = var name, value = actual value; might be multilevel depending on loaded json
        """
        
        if not self.scheme:
            raise Exception('You must first load json data structure with self.load() method!')
        else:
            return self._read_by_scheme(self.scheme)
        
    def write(self, data: dict):
        """writes flatten data to DB using scheme got by self.load() method
        
        FIXME: WONT WRITE Array AT THE MOMENT

        Args:
            data (dict): you data dictionary where key is var name and value is value to be written

        Raises:
            Exception: raises if self.load() not called
        """
        
        if not self.scheme:
            raise Exception('You must first load json data structure with self.load() method!')
        else:
            self._write_by_scheme(data)
        
    def _read_by_scheme(self, var_dict: dict):
        message = {}
        
        for k, v in var_dict.items():
            datatype = v['datatype']
            
            data = None
            if datatype == 'Struct':
                data = self._read_by_scheme(v['children'])
            elif self._array_check_pattern.match(datatype):
                pass
                # TODO: Array parsing
                # length = int(self._array_size_pattern.search(datatype).group(1) + 1)
                # el_datatype = str(self._array_datatype_pattern.search(datatype).group(1))
            else:
                data = self._datatype_read_map[datatype](v['offset'])

            message[k] = data
        
        return message

    def _write_by_scheme(self, data: dict):
        for k, v in data.items():
            try:
                self.scheme_flat[k]
            except:
                continue
            
            datatype = self.scheme_flat[k]['datatype']
            offset = self.scheme_flat[k]['offset']
            
            if datatype == 'Struct':
                self._write_by_scheme(v)
            elif self._array_check_pattern.match(datatype):
                pass
                # TODO: Array writing
            else:
                if v == None:
                    raise Exception(f"Value of '{k}' are None, it wont be written.")
                else:
                    try:
                        self._datatype_write_map[datatype](offset, v)
                    except Exception as e:
                        raise Exception(f'Could not write data: {e}')

    
    def _db_read(self, offset: float, byte_size: int):
        return self.plc.db_read(self.db_number, int(offset), byte_size)
    def _db_write(self, offset: float, data: bytearray):
        self.plc.db_write(self.db_number, int(offset), data)
        
    def _offset_decimal(self, offset: float):
        integer_part = int(offset)
        decimal_part = int(round((offset - integer_part)*10))
        return decimal_part
    
    def _flatten_data(self, flat_data: dict, data: dict): # flatten multilevel dictionary into one level one
        for k, v in data.items():
            if v['datatype'] == 'Struct':
                self._flatten_data(flat_data, v['children'])
            else:
                flat_data[k] = v
    
    ############################################## PLC DB readers writers ################################################
    # note: functions defined in order of documentation: https://python-snap7.readthedocs.io/en/latest/API/util.html
    
    def read_bool(self, offset: float) -> bool:
        reading    = self._db_read(offset, 1)
        bit_offset = self._offset_decimal(offset)
        val        = snap7.util.get_bool(reading, 0, bit_offset)
        return val
    def write_bool(self, offset: float, val: bool):
        reading    = self._db_read(offset, 1)
        bit_offset = self._offset_decimal(offset)
        snap7.util.set_bool(reading, 0, bit_offset, val)
        self._db_write(offset, reading)
        
    
    def read_byte(self, offset: float) -> int:
        reading = self._db_read(offset, 1)  
        val     = snap7.util.get_byte(reading, 0)
        return val
    def write_byte(self, offset: float, val: int):
        reading = self._db_read(offset, 1)
        snap7.util.set_byte(reading, 0, val)
        self._db_write(offset, reading)
        
        
    def read_char(self, offset: float) -> str:
        reading = self._db_read(offset, 1)
        val     = snap7.util.get_char(reading, 0)
        return val
    def write_char(self, offset: float, val: str):
        reading = self._db_read(offset, 1)
        snap7.util.set_char(reading, 0, val)
        self._db_write(offset, reading)
        
    
    # TODO: date_time_object = date_and_time
    
        
        
    def read_dint(self, offset: float) -> int:
        reading = self._db_read(offset, 4)
        val     = snap7.util.get_dint(reading, 0)
        return val
    def write_dint(self, offset: float, val: int):
        reading = self._db_read(offset, 4)
        snap7.util.set_dint(reading, 0, val)
        self._db_write(offset, reading)
        
        
    # TODO: dt
        
    
    def read_dword(self, offset: float) -> int:
        reading = self._db_read(offset, 8)
        val     = snap7.util.get_dword(reading, 0)
        return val
    def write_dword(self, offset: float, val: int):
        reading = self._db_read(offset, 8)
        snap7.util.set_dword(reading, 0, val)
        self._db_write(offset, reading)
        
        
    # TODO: fstring
        
        
    def read_int(self, offset: float) -> int:
        reading = self._db_read(offset, 2)
        val     = snap7.util.get_int(reading, 0)
        return val
    def write_int(self, offset: float, val: int):
        reading = self._db_read(offset, 2)
        snap7.util.set_int(reading, 0, val)
        self._db_write(offset, reading)
        
        
    def read_lint(self, offset: float) -> int:
        reading = self._db_read(offset, 8)
        val     = snap7.util.get_int(reading, 0)
        return val
    def write_lint(self, offset: float, val: int):
        reading = self._db_read(offset, 8)
        snap7.util.set_int(reading, 0, val)
        self._db_write(offset, reading)
        
        
    def read_lreal(self, offset: float) -> float:
        reading = self._db_read(offset, 8)
        val     = snap7.util.get_lreal(reading, 0)
        return val
    def write_lreal(self, offset: float, val: float):
        reading = self._db_read(offset, 8)
        snap7.util.set_lreal(reading, 0, val)
        self._db_write(offset, reading)
        
        
    def read_lword(self, offset: float) -> int:
        reading = self._db_read(offset, 8)
        val     = snap7.util.get_lword(reading, 0)
        return val
    def write_lword(self, offset: float, val: int):
        reading = self._db_read(offset, 8)
        snap7.util.set_lword(reading, 0, val)
        self._db_write(offset, reading)
            

    def read_real(self, offset: float) -> float:
        reading = self._db_read(offset, 4)
        val     = snap7.util.get_real(reading, 0)
        return val
    def write_real(self, offset: float, val: float):
        reading = self._db_read(offset, 4)
        snap7.util.set_real(reading, 0, val)
        self._db_write(offset, reading)
        
        
    def read_sint(self, offset: float) -> int:
        reading = self._db_read(offset, 1)
        val     = snap7.util.get_sint(reading, 0)
        return val
    def write_sint(self, offset: float, val: int):
        reading = self._db_read(offset, 1)
        snap7.util.set_sint(reading, 0, val)
        self._db_write(offset, reading)
        
        
    def read_string(self, offset: float, byte_size: int = 255) -> str:
        reading = self._db_read(offset, byte_size)  
        val     = snap7.util.get_string(reading, 0)
        return val
    def write_string(self, offset: float, val: str, byte_size: int = 255):
        reading = self._db_read(offset, byte_size)
        snap7.util.set_string(reading, 0, val, byte_size)
        self._db_write(offset, reading)


    # TODO: time
    
    
    def read_udint(self, offset: float) -> int:
        reading = self._db_read(offset, 4)
        val     = snap7.util.get_udint(reading, 0)
        return val
    def write_udint(self, offset: float, val: int):
        reading = self._db_read(offset, 4)
        snap7.util.set_udint(reading, 0, val)
        self._db_write(offset, reading)
        
        
    def read_uint(self, offset: float) -> int:
        reading = self._db_read(offset, 2)
        val     = snap7.util.get_uint(reading, 0)
        return val
    def write_uint(self, offset: float, val: int):
        reading = self._db_read(offset, 2)
        snap7.util.set_uint(reading, 0, val)
        self._db_write(offset, reading)
    
    
    def read_ulint(self, offset: float) -> int:
        reading = self._db_read(offset, 8)
        val     = snap7.util.get_ulint(reading, 0)
        return val
    # def write_ulint(self, offset: float, val: int):
    #     reading = self._db_read(offset, 8)
    #     snap7.util.set_ulint(reading, 0, val)  # FIXME: set_ulint doenst exist
    #     self._db_write(offset, reading)
        
        
    def read_usint(self, offset: float) -> int:
        reading = self._db_read(offset, 1)
        val     = snap7.util.get_usint(reading, 0)
        return val
    def write_usint(self, offset: float, val: int):
        reading = self._db_read(offset, 1)
        snap7.util.set_usint(reading, 0, val)
        self._db_write(offset, reading)
        
        
    def read_wchar(self, offset: float) -> str:
        reading = self._db_read(offset, 2)
        val     = snap7.util.get_wchar(reading, 0)
        return val
    # def write_wchar(self, offset: float, val: str): 
    #     reading = self._db_read(offset, 2)
    #     snap7.util.set_wchar(reading, 0, val)  # FIXME: set_wchar doenst exist
    #     self._db_write(offset, reading)
        
        
    def read_word(self, offset: float) -> int:
        reading = self._db_read(offset, 2)
        val     = snap7.util.get_word(reading, 0)
        return val
    def write_word(self, offset: float, val: int):
        reading = self._db_read(offset, 2)
        snap7.util.set_word(reading, 0, val)
        self._db_write(offset, reading)
        
        
    # TODO: wstring
    
    
    ########################################## memory bits reading ######################################
    # TODO: not tested, not tried
    
    # def read_memory(self, addr, len):
    #     reading = self.plc.read_area(snap7.types.Areas.MK, 0, addr, len)
    #     val = struct.unpack('>f', reading)  # big-endian
    #     return val
    # def write_memory(self, addr, len, value):
    #     self.plc.mb_write(addr, len, bytearray(struct.pack('>f', value)))  # big-endian
    
        
if __name__ == '__main__':
    manager = Snap7Manager('192.168.20.101', 0, 1, 2)
    
    manager.load('plc_driver\Snap7ManagementSystem\src\\resources\DB.json')
    
    print('scheme:\n', manager.scheme, '\n')
    
    ########## read #############
    
    read_data = manager.read()
    
    print('read_data:\n', read_data)
    
    # ########## write #############      
    
    # change some value and write all of it back
    read_data['var_bool'] = not read_data['var_bool']
    
    manager.write(read_data)
    
    
            
        
    
    