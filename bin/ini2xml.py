import configparser
import xml.etree.ElementTree as ET
import sys

def preprocess_ini(ini_file):
    """Preprocess the .ini file to convert 'key value' into 'key=value'"""
    processed_lines = []
    with open(ini_file, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("["):  # Ignore section headers
                parts = line.split(None, 1)  # Split on first space
                if len(parts) == 2:
                    line = f"{parts[0]}={parts[1]}"
            processed_lines.append(line)
    
    temp_file = "temp_processed.ini"
    with open(temp_file, "w") as f:
        f.write("\n".join(processed_lines))
    
    return temp_file

def ini_to_xml(ini_file, extra_ini_file, output_xml):
    # Preprocess ini file
    print("ini: {0}, extra: {1}".format(ini_file, extra_ini_file))
    processed_extra = preprocess_ini(extra_ini_file)
    processed_ini = preprocess_ini(ini_file)
    
    # Parse the main ini file
    config = configparser.ConfigParser()
    config.read(processed_ini)
    
    # Parse the extra ini file
    extra_config = configparser.ConfigParser()
    extra_config.read(processed_extra)
    
    # Get extra parameters
    device_type = extra_config.get("GENERAL", "device", fallback="robotPathPlannerDev")
    nws_type = extra_config.get("GENERAL", "wrapper", fallback="navigation2D_nws_yarp")
    robot_name = extra_config.get("GENERAL", "robotname", fallback="robotPathPlanner")
    device_name = extra_config.get("GENERAL", "device_name", fallback="pathPlanner")
    nws_name = extra_config.get("GENERAL", "nws_name", fallback="nav2DNwsYarp")
    subdevice_name = device_name.lower()
    extern_name = nws_name.lower()
    
    # Create XML structure
    robot = ET.Element("robot", name=robot_name, build="1", portprefix="", xmlns_xi="http://www.w3.org/2001/XInclude")
    devices = ET.SubElement(robot, "devices")
    
    # Add main device
    device = ET.SubElement(devices, "device", name=device_name, type=device_type)
    for section in config.sections():
        group = ET.SubElement(device, "group", name=section)
        for key, value in config.items(section):
            print("{0}: {1}".format(key,value))
            ET.SubElement(group, "param", name=key).text = value
    
    # Add wrapper device
    nws_device = ET.SubElement(devices, "device", name=nws_name, type=nws_type)
    general_group = ET.SubElement(nws_device, "group", name="GENERAL")
    ET.SubElement(general_group, "param", name="name", extern_name=extern_name).text = f"/{nws_name}"
    
    # Add attach/detach actions
    attach_action = ET.SubElement(nws_device, "action", phase="startup", level="5", type="attach")
    param_list = ET.SubElement(attach_action, "paramlist", name="networks")
    ET.SubElement(param_list, "elem", name=f"subdevice{subdevice_name}").text = device_name
    ET.SubElement(nws_device, "action", phase="shutdown", level="5", type="detach")
    
    # Write XML to file
    tree = ET.ElementTree(robot)
    ET.indent(tree, space="    ", level=0)  # Format output for readability
    tree.write(output_xml, encoding="utf-8", xml_declaration=True)
    print(f"XML file '{output_xml}' generated successfully.")

# Example usage: ini_to_xml("robotPathPlanner_cer.ini", "extra_config.ini", "output.xml")
if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python script.py <input.ini> <extra.ini> <output.xml>")
    else:
        ini_to_xml(sys.argv[1], sys.argv[2], sys.argv[3])
