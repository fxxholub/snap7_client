import re
import json
import sys

from bs4 import BeautifulSoup

class XMLDataBlockReader:
    """Reader class that parses DataBlock represented as XML derived from Siemens TIA Portal Version Constrol Interface.
    The parsed data can be accesed by self.scheme or dumped by python json library using self.json_dump or dumps.
    """
    def __init__(self, file_path):
        self.scheme = None
        
        self._array_check_pattern = re.compile(r'^Array')
        self._string_check_pattern = re.compile(r'^String')
        self._array_size_pattern = re.compile(r'\[0\.\.(\d+)\]')
        
        
        with open(file_path, 'rb') as fp:
            self.soup = BeautifulSoup(fp, 'xml')
            # print(self.soup)
            # print(len(self.soup.Section.contents)
            try:
                self.scheme = self._parse(self.soup.Section.contents)
            except Exception as e:
                print(f'Could not parse TIA Portal DataBlock XML: {e}')

        
        
    def _parse(self, members):
        scheme = {}
        for member in members:
            if member == "\n": continue
            
            datatype = member["Datatype"]
            
            var_obj = {
                "datatype": datatype,
                "offset": None,
            }
            
            
            if datatype == "Struct":
                submembers = member.find_all("Member")
                kids = self._parse(submembers)
                var_obj["children"] = kids
            elif self._array_check_pattern.match(datatype):
                match = self._array_size_pattern.search(datatype)
                submembers = member.find_all("Member")
                kids = self._parse(submembers)
                if kids:
                    var_obj["children"] = kids
                # size = int(match.group(1)) + 1
                # print(size)
            # elif self._string_check_pattern.match(datatype):
                
            scheme[member["Name"]] = var_obj
            
        return scheme
            
    def json_dumps(self):
        return json.dumps(self.scheme)
    
    def json_dump(self, file_path):
        with open(file_path, 'w', encoding ='utf8') as json_file: 
            json.dump(self.scheme, json_file, ensure_ascii = False, indent=4)

def main():
    if len(sys.argv) != 3:
        print("Usage: python xml_datablock_reader.py <input_file_path.xml> <output_file_path.json>")
        return    

    input_path = sys.argv[1]
    output_path = sys.argv[2]
    
    reader = XMLDataBlockReader(input_path)
    print(reader.scheme)
    reader.json_dump(output_path)

if __name__ == "__main__":
    main()
