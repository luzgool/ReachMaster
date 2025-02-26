"""Module that provides a set of functions for interfacing
with the robot microcontroller. It provides functions to 
recognize and establish serial connections to the 
controller, read/write settings, calibration and command
files. 

Todo:
    * Object orient
    * Automate unit tests
    * Python 3 compatibility
    * PEP 8

"""

import numpy as np
import serial
from serial.tools import list_ports

#private functions----------------------------------------------

def _load_calibration_variable(rob_controller, varname, value):
    robot.write("c")
    if robot.read() == "c":
        robot.write(varname + "\n")
        if robot.read() == "c":
            robot.write(value)
    if robot.read() == "c":
        print(varname + ' loaded')
    else:
        raise Exception(varname)

def _load_command_variable(rob_controller, varname, value):  
    robot.write("p")
    if robot.read() == "p":
        robot.write(varname + "\n")
        if robot.read() == "p":
            robot.write(value)
    if robot.read() == "p":
        print(varname + ' loaded')
    else:
        raise Exception(varname)

def _variable_read(rob_controller, varname):
    rob_controller.write("g")
    if rob_controller.read() == "g":
        rob_controller.write(varname+"\n")
        return rob_controller.readline()[:-2]

def _variable_write(rob_controller, varname, value):
    rob_controller.write("v")
    if rob_controller.read() == "v":
        rob_controller.write(varname+"\n")
        if rob_controller.read() == "v":
            rob_controller.write(value+"\n")

#public functions---------------------------------------------------

def start_interface(config):
    """Establish a serial connection with the robot
    controller.

    Parameters
    ----------
    config : dict
        The currently loaded configuration file.

    Returns
    -------
    rob_controller : serial.serialposix.Serial  
        The serial interface to the robot controller.      

    """ 
    rob_controller = serial.Serial(config['ReachMaster']['rob_control_port'],
        config['ReachMaster']['serial_baud'],
        timeout=config['ReachMaster']['control_timeout'])
    rob_controller.flushInput()
    rob_controller.write("h")
    response = rob_controller.read()
    if response == "h":
        rob_connected = True
        return rob_controller
    else:
        raise Exception("Robot controller failed to connect.")

def stop_interface(rob_controller): 
    """Perform a soft reboot of the robot controller
    and close the serial connection.

    Parameters
    ----------
    rob_controller : serial.serialposix.Serial
        The serial interface to the robot controller.

    """   
    rob_controller.write("e")
    rob_controller.close()

def get_ports():
    """List all serial port with connected devices.

    Returns
    -------
    port_list : list(str)  
        Names of all the serial ports with connected devices. 

    """
    port_list = list(list_ports.comports())
    for i in range(len(port_list)):
        port_list[i] = port_list[i].device
    return port_list

def load_config_calibration(rob_controller, config):
    """Load the calibration parameters to the robot controller.

    Uses the calibration file selected in the configuration
    file.

    Parameters
    ----------
    rob_controller : serial.serialposix.Serial
        The serial interface to the robot controller.
    config : dict
        The currently loaded configuration file.     

    """
    try:
        _load_calibration_variable(rob_controller, 'dis', config['RobotSettings']['dis'])
        _load_calibration_variable(rob_controller, 'pos', config['RobotSettings']['pos'])
        _load_calibration_variable(rob_controller, 'x_push_dur', config['RobotSettings']['x_push_dur'])
        _load_calibration_variable(rob_controller, 'x_pull_dur', config['RobotSettings']['x_pull_dur'])
        _load_calibration_variable(rob_controller, 'y_push_dur', config['RobotSettings']['y_push_dur'])
        _load_calibration_variable(rob_controller, 'y_pull_dur', config['RobotSettings']['y_pull_dur'])
        _load_calibration_variable(rob_controller, 'z_push_dur', config['RobotSettings']['z_push_dur'])
        _load_calibration_variable(rob_controller, 'z_pull_dur', config['RobotSettings']['z_pull_dur'])
    except Exception as varname:
        raise Exception(varname)      

def load_config_commands(rob_controller, config):
    """Load the position commands to the robot controller.
    
    Uses the method determined by the command type 
    selected in the configuration file. Currently, the
    options are `read_from_file`, `sample_from_file`, or 
    `parametric_sample`. `read_from_file` takes the 
    commands directly from the command file. 
    `sample_from_file` generates a sequence of commands by
    sampling rows from the command file with replacement.
    For both of these options, the command file is assumed
    to have three columns ordered as `reach distance`, 
    `azimuth', `elevation`. `parametric_sample` does not 
    use the command file. Rather, it samples commands 
    uniformly from the `reach volume` determined by the 
    user-selected inverse kinematics parameters. 

    Todo:
        * Further functionalize for better clarity.

    Parameters
    ----------
    rob_controller : serial.serialposix.Serial
        The serial interface to the robot controller.
    config : dict
        The currently loaded configuration file. 

    Returns
    -------
    config : dict
        The configuration file possibly updated to include
        the command values that were loaded.    

    """
    #extract robot kinematic settings
    ygimbal_to_joint = config['RobotSettings']['ygimbal_to_joint']
    zgimbal_to_joint = config['RobotSettings']['zgimbal_to_joint']
    xgimbal_xoffset = config['RobotSettings']['xgimbal_xoffset']
    ygimbal_yoffset = config['RobotSettings']['ygimbal_yoffset']
    zgimbal_zoffset = config['RobotSettings']['zgimbal_zoffset']
    x_origin = config['RobotSettings']['x_origin']
    y_origin = config['RobotSettings']['y_origin']
    z_origin = config['RobotSettings']['z_origin'] 
    reach_dist_min = config['RobotSettings']['reach_dist_min']
    reach_dist_max = config['RobotSettings']['reach_dist_max']
    reach_angle_max = config['RobotSettings']['reach_angle_max']
    #generate commands according to selected command type     
    n = 100
    if config['RobotSettings']['command_type'] == "parametric_sample":        
        r = (
            reach_dist_min + 
            (reach_dist_max - reach_dist_min)*
            np.random.uniform(
                low = 0.0, 
                high = 1.0, 
                size = 500*n
                )**(1.0/3.0)
            )
        theta_y = reach_angle_max * np.random.uniform(low = -1, high = 1, size = 500*n)
        theta_z = reach_angle_max * np.random.uniform(low = -1, high = 1, size = 500*n)
        theta = np.sqrt(theta_y**2 + theta_z**2)
        r = r[theta <= reach_angle_max][0:n]
        theta_y = theta_y[theta <= reach_angle_max][0:n]
        theta_z = theta_z[theta <= reach_angle_max][0:n]
    elif config['RobotSettings']['command_type'] == "sample_from_file":
        r_set, theta_y_set, theta_z_set = np.loadtxt(
            config['RobotSettings']['command_file'],
            skiprows = 1, 
            delimiter = ',', 
            unpack = True, 
            usecols = (1, 2, 3)
            )
        rand_sample = np.random.choice(range(len(r_set)), replace = True, size = n)
        r = r_set[rand_sample]
        theta_y = theta_y_set[rand_sample]
        theta_z = theta_z_set[rand_sample]
    elif config['RobotSettings']['command_type'] == "read_from_file":
        r, theta_y, theta_z = np.loadtxt(
            config['RobotSettings']['command_file'],
            skiprows = 1,
            delimiter = ',',
            unpack = True,
            usecols = (1, 2, 3)
            )
    else:
        raise Exception("Invalid command type.") 
    #pass generated commands though inverse kinematic transformation       
    Ax = np.sqrt(
        xgimbal_xoffset**2 + r**2 - 2*xgimbal_xoffset*r*np.cos(theta_y)*np.cos(theta_z)
        )
    gammay = -np.arcsin(
        np.sin(theta_y)*
        np.sqrt(
            (r*np.cos(theta_y)*np.cos(theta_z))**2 + 
            (r*np.sin(theta_y)*np.cos(theta_z))**2
            )/
        np.sqrt(
            (xgimbal_xoffset - r*np.cos(theta_y)*np.cos(theta_z))**2 +
            (r*np.sin(theta_y)*np.cos(theta_z))**2
            )
        )
    gammaz = -np.arcsin(r*np.sin(theta_z)/Ax)
    Ay = np.sqrt(
        (ygimbal_to_joint - ygimbal_to_joint*np.cos(gammay)*np.cos(gammaz))**2 + 
        (ygimbal_yoffset - ygimbal_to_joint*np.sin(gammay)*np.cos(gammaz))**2 + 
        (ygimbal_to_joint*np.sin(gammaz))**2
        )
    Az = np.sqrt(
        (zgimbal_to_joint - zgimbal_to_joint*np.cos(gammay)*np.cos(gammaz))**2 + 
        (zgimbal_to_joint*np.sin(gammay)*np.cos(gammaz))**2 + 
        (zgimbal_zoffset - zgimbal_to_joint*np.sin(gammaz))**2
        )
    Ax = np.round((Ax - xgimbal_xoffset)/50*1024 + x_origin, decimals = 1)
    Ay = np.round((Ay - ygimbal_yoffset)/50*1024 + y_origin, decimals = 1)
    Az = np.round((Az - zgimbal_zoffset)/50*1024 + z_origin, decimals = 1)
    #convert tranformed commands to appropriate data types/format
    x = np.array2string(Ax, formatter = {'float_kind': lambda Ax: "%.1f" % Ax})
    y = np.array2string(Ay, formatter = {'float_kind': lambda Ay: "%.1f" % Ay})
    z = np.array2string(Az, formatter = {'float_kind': lambda Az: "%.1f" % Az})
    r = np.array2string(r, formatter = {'float_kind': lambda r: "%.1f" % r})
    theta_y = np.array2string(theta_y, formatter = {'float_kind': lambda theta_y: "%.1f" % theta_y})
    theta_z = np.array2string(theta_z, formatter = {'float_kind': lambda theta_z: "%.1f" % theta_z})
    x = x[1:-1] + ' '
    y = y[1:-1] + ' '
    z = z[1:-1] + ' '
    r = r[1:-1] + ' '
    theta_y = theta_y[1:-1] + ' '
    theta_z = theta_z[1:-1] + ' '    
    #load commands to robot
    try:
        _load_command_variable(rob_controller, 'x_command_pos', x)
        _load_command_variable(rob_controller, 'y_command_pos', y)
        _load_command_variable(rob_controller, 'z_command_pos', z)
    except Exception as varname:
        raise Exception("Failed to load: " + varname)
    #record the loaded commands to the config
    config['RobotSettings']['x'] = x
    config['RobotSettings']['y'] = y
    config['RobotSettings']['z'] = z
    config['RobotSettings']['r'] = r
    config['RobotSettings']['theta_y'] = theta_y
    config['RobotSettings']['theta_z'] = theta_z
    return config

def set_rob_controller(rob_controller, config):
    """Load all the robot settings to the robot controller.

    Parameters
    ----------
    rob_controller : serial.serialposix.Serial
        The serial interface to the robot controller.
    config : dict
        The currently loaded configuration file.

    Returns
    -------
    config : dict
        The configuration file possibly updated to include
        the command values that were loaded.

    """
    _variable_write(rob_controller, 'alpha', str(config['RobotSettings']['alpha']))
    _variable_write(rob_controller, 'tol', str(config['RobotSettings']['tol']))
    _variable_write(rob_controller, 'period', str(config['RobotSettings']['period']))
    _variable_write(rob_controller, 'off_dur', str(config['RobotSettings']['off_dur']))
    _variable_write(rob_controller, 'num_tol', str(config['RobotSettings']['num_tol']))
    _variable_write(rob_controller, 'x_push_wt', str(config['RobotSettings']['x_push_wt']))
    _variable_write(rob_controller, 'x_pull_wt', str(config['RobotSettings']['x_pull_wt']))
    _variable_write(rob_controller, 'y_push_wt', str(config['RobotSettings']['y_push_wt']))
    _variable_write(rob_controller, 'y_pull_wt', str(config['RobotSettings']['y_pull_wt']))
    _variable_write(rob_controller, 'z_push_wt', str(config['RobotSettings']['z_push_wt']))
    _variable_write(rob_controller, 'z_pull_wt', str(config['RobotSettings']['z_pull_wt']))
    _variable_write(rob_controller, 'rew_zone_x', str(config['RobotSettings']['rew_zone_x']))
    _variable_write(rob_controller, 'rew_zone_y_min', str(config['RobotSettings']['rew_zone_y_min']))
    _variable_write(rob_controller, 'rew_zone_y_max', str(config['RobotSettings']['rew_zone_y_max']))
    _variable_write(rob_controller, 'rew_zone_z_min', str(config['RobotSettings']['rew_zone_z_min']))
    _variable_write(rob_controller, 'rew_zone_z_max', str(config['RobotSettings']['rew_zone_z_max']))
    load_config_calibration(rob_controller, config)
    config = load_config_commands(rob_controller, config)    
    return config