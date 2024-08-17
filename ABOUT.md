# Design notes about the SensorVisualizer (SV)

## Widgets

A widget is a window where data being inputted to the system can be visualized.

The following widgets will be implemented:

- **Monitor panel**. A simple window where data is shown. You may format the data as you wish. 
- **Linear Graph**. A plot of numerical data. You may select the scale to be used, fix its axis limits, set the line and point sizes, color...
- **Scatter Plot**. Similar to the last one but without interconnecting lines.
- **Candlestick Chart**. Useful to measure noise in a signal.
- **Inertial 3D View**. Select from an assortment of 3D models and attach the inputs of their XYZ linear acceleration and angular velocity.
- **GPS View**. Opens a plane or a map and draws the trajectory of the device.

All widgets will have a bunch of ***hook*** methods:

- `hookVariable(Variable) -> None`

    A hook will receive a variable as argument and will update the properties of the widget related to that variable. E.g. the Inertial 3D view will have a variable representing the X angular velocity, then, there'll be a function that will receive a new value and move the model accordingly.

To add a widget:

1. Add a widget either by right clicking into empty space in the window or by selecting `Widget` > `Add Widget` > (Select the type of widget).
2. Position the widget wherever it suits you best.
3. Right click over the widget > `Widget configuration`.
4. User is presented with two sections:

    - **Variables**. The linked variable(s) for the visualization.
        - You may select an already used variable by searching for it or you may create a new one.
        - If “New variable” is selected, a new window will open.
        - Once the variable is selected, the program will search for the variable inside `Variable._vbes` and attach the correspondent hook to the variable.

    - **Visualization settings**.
        - In the case of graphs, you may select what type of graph to use. For each variable there may be some special fields, such as color, line width…
        - In the case of 3D models, you’ll have to attach rotXYZ, omegaXYZ to an input variable.
        - In the case of trajectory planes, you’ll have to attach the position XYZ to the input variable. 

## Variables

A variable has the following fields:

- `name : str`. The variable name.
- `type : type`. This type should have a constructor to convert from `string` to that `type`.
- `value`. The last received value.
- `lastValues : List[]`. The last received values. It's a FIFO structure. Must contain `value` at position 0.
- `time : List[int]`. An array with the time of reception of all values inside `lastValues`.
- `hooks : List[Callable[Variable, None]]`. Contains the functions of the widgets related to the variable. These functions will 
- Source (maybe it won't be needed?).

All created variables will be stored in a class variable `_vbes : List[Variables]`.

To add them on the “New variable” window:

1.	First, select a source from the available sources. If the source you’re looking for doesn’t appear, you’ll have to create it by clicking “New Source”.

2.	A list of available names will appear if the source is already giving out data. You may select one from the list or add your own.

## Sources

A source is a class from where the different protocols will inherit. Basically, the class will have the following fields:

- **Preprocessor**. By default, `None`. 
  
  This preprocessor must be a simple program that receives as arguments an input string and shall return over console or stdout the processed field. A field is processed when it follows the following format:

    ```
    {(...),”name”:”value”,(...)}
    ```
	
    By this format rule, the name and value fields must be in valid `string` format; that is, special characters are to be stored as `"\x"`, and \ must be stored as `\\`, as usual string syntax. The structure is the same as dictionaries in Python.

A source has the following functions:

- `(abstract) _getInputData() -> str | None`
  
  Returns a string of raw data. This data may or may not be already processed.

- `getDataFields() -> Dict[str,str] | None`
  
  Returns a dictionary with the fields and its values. As it is a dictionary, no repeated values can appear so the represented item will always be the last one received. If a preprocessor is selected, this function will call it to generate the formatted string that will be then parsed as a dictionary.

From the “New source” window:
1.	When selecting a source, first you’ll specify the type of source:

    a. **Serial port**. You’ll be presented with a list of available ports on your computer.

    b. **Ethernet**. You’ll have to specify the port number. If you click on the down arrow, a list of available ports will appear.
    
    c. **ZMQ**.  Same as before (?).

2.	Then, you may opt to add a preprocessor. 

## Extra notes

- All these windows will also be available individually from the toolbar, so you may first add sources and variables and finally the widgets.
