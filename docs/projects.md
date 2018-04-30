# Pyree Projects
A pyree project is a collection of scenes, resources and signals.
A JSON config file is used to define a project.

## Project Elements

### Nodes
A node is a single python file containing a single class that inherits from the BaseNode class.
It can do anything from the simplest data processing to rendering a full scene.

An instance of the class is generated on startup.
Whenever the file is changed, it is reloaded and a new instance of the class is generated.
To prevent unnecessary regeneration of data, a mechanism of transferring information from the old to the new
instance is provided.

### Signals
Each node can define inputs and outputs directly in code. These signals can be linked in the project file.
Only the inputs can be directly called within a node.


## Project Structure