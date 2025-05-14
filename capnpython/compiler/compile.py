import sys
from jinja2 import Environment, PackageLoader
from pathlib import Path
import json
import capnp
from capnp import schema_capnp

def find_type(code, node_id):
    for node in code.get("nodes", []):
        if node.get("id") == node_id:
            return node.get("displayName").split(":")[-1].replace(".", "_").replace("/", ".")
    return None

def to_pytype(node_type):
    if node_type == "void":
        return "None"
    elif node_type == "bool":
        return "bool"
    elif "int" in node_type:
        return "int"
    elif "float" in node_type:
        return "float"
    elif node_type == "text":
        return "str"
    elif node_type == "data":
        return "bytes"
    elif node_type == "list":
        return "list"
    elif node_type == "struct":
        return "struct"
    elif node_type == "enum":
        return "enum"
    elif node_type == "interface":
        return "interface"
    else:
        # print(node_type)
        # print(node_type.get("displayName"))
        return node_type

def main():
    env = Environment(loader=PackageLoader('capnpython', 'templates'))
    env.filters["format_name"] = lambda name: name[name.find(":")+1:]
    module = env.get_template("module.py.j2")
    
    code = schema_capnp.CodeGeneratorRequest.read(sys.stdin).to_dict()
    filtered_code = {
        "enums": [],
        "structs": [],
        "consts": [],
        "capnp_file": None,
        "capnpVersion": code.get("capnpVersion"),
    }
    for node in code.get("nodes", []):
        node_type = list(node.keys())[0]
        if node_type == "file":
            filtered_code["capnp_file"] = node.get("displayName").replace(".", "_").replace("/", ".")
            continue
        node_id = node.get("id")
        display_name = node.get("displayName")
        capnp_module, local_name = display_name.split(":")
        capnp_module = capnp_module.replace(".", "_").replace("/", ".")
        local_name = local_name.replace(".", "_").replace("/", ".")
        if node_type == "enum":
            enumerants = node.get("enum", {}).get("enumerants", {})
            for enumerant in enumerants:
                enumerant["pyname"] = enumerant["name"].upper()
            filtered_code["enums"].append({
                "id": node_id,
                "module": capnp_module,
                "name": local_name,
                "enumerants": enumerants,
            })
        elif node_type == "const":
            const_type = list(node.get('const').get('type').keys())[0]
            const_value = list(node.get('const').get('value').items())[0][1]
            node_const = {
                "id": node_id,
                "module": capnp_module,
                "name": local_name.upper(),
                "type": const_type,
                "value": const_value,
                "pytype": to_pytype(const_type),
            }
            filtered_code["consts"].append(node_const)
        elif node_type == "struct":
            fields = node.get("struct", {}).get("fields", [])
            is_union = False
            node_fields = []
            for field in fields:
                node_field = {}
                if field.get("discriminantValue") != 65535:
                    is_union = True
                name = field.get("name")
                node_field["name"] = name
                node_field["c_name"] = name[0].upper() + name[1:]
                if "slot" in field:
                    node_slot_type = field.get("slot").get("type")
                    node_field["type"] = list(node_slot_type.keys())[0]
                    if isinstance(node_slot_type.get(node_field["type"]), dict):
                        sub_type = node_slot_type.get(node_field["type"], {}).get("typeId", None)
                        if sub_type is not None:
                            sub_type = find_type(code, sub_type)
                        if sub_type is not None:
                            node_field["sub_type"] = sub_type
                            node_field["type"] = sub_type
                else:
                    node_field["type"] = find_type(code, field.get("group", {}).get("typeId", None))        
                node_field["pytype"] = to_pytype(node_field["type"])
                node_field["codeOrder"] = field.get("codeOrder")
                node_fields.append(node_field)
            filtered_code["structs"].append({
                "id": node_id,
                "is_union": is_union,
                "fields": node_fields,
                "module": capnp_module,
                "name": local_name,
            })
    for f in code.get("requestedFiles", []):
        outfile = Path(f.get("filename").replace(".capnp", ".py"))
        outfile.write_text(module.render(code=filtered_code))
            

            