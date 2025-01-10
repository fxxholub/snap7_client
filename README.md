# Snap7 client

__A python based snap7 client for effortless Siemens PLC DataBlock reading and writing.__

How? Provide JSON representing the Data Block structure and the tool will handle the rest.


## Example run

- Check the example JSON and TIA portal screenshot in the `resources` directory
- Check the example run in the `snap7_manager.py` main

__note:__ your DB must use non optimized data access

    right click DB, then: Properties > Attributes > uncheck Optimized block access

__note:__ your PLC must permit the PUT/GET requests from extern clients

    open PLC properties > Protection & Securrity > Connection Mechanism > check Permit access with PUT/GET...

loaded json:

```json
{
    "var_string": {"datatype": "String", "offset": 0.0},
    "bl5": {"datatype": "Bool", "offset": 256.0},
    "bl4": {"datatype": "Bool", "offset": 256.1},
    "bl3": {"datatype": "Bool", "offset": 256.2},
    "bl2": {"datatype": "Bool", "offset": 256.3},
    "bl1": {"datatype": "Bool", "offset": 256.4},
    "var_bool": {"datatype": "Bool", "offset": 256.5},
    "byte_arr": {"datatype": "Array[0..1] of Byte", "offset": 258.0},
    "var_struct": {
        "datatype": "Struct",
        "offset": 260.0,
        "children": {
            "var_struct_string": {"datatype": "String", "offset": 260.0},
            "var_struct_bool": {"datatype": "Bool", "offset": 516.0},
        },
    },
}
```

read data:

```python
 {
    "var_string": "",
    "bl5": False,
    "bl4": False,
    "bl3": False,
    "bl2": False,
    "bl1": False,
    "var_bool": True,
    "byte_arr": None,
    "var_struct": {"var_struct_string": "", "var_struct_bool": False},
}
```

## Automatic JSON generator

If you dont wanna write the whole json by yourself, use XMLDataBlockReader:

### Generate XML

1) in TIA portal go: Version Control Interface > Add new workspace > Workspace_1
2) Configure the workspace and drag and drop items (or whole configuration to the workspace)
3) Export changes to workspace (icon) > Synchronize (icon)
4) TADAAA! you have an XML

### Generate JSON

1) run the `utils/xml_datablock_reader.py` with provided XML file path:
   
   `python xml_datablock_reader.py <input_file_path.xml> <output_file_path.json>`
2) TADAAA! you have the JSON!
3) fill the offset values (including the decimal part) so they are not `None` anymore

