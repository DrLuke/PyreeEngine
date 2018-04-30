# Node Signals
Node signals are the only method of passing data between nodes.
They are also used to determine the execution order.

## Signal definition
Signals are defined with the help of four different decorators:
* `@signalInput(name: str, type: Union[Type, List[Type]], meta: dict= None)`
* `@signalOutput(name: str, type: Union[Type, List[Type]], meta: dict= None)`
* `@execIn(name: str, meta: dict= None)`
* `@execOut(name: str, meta: dict= None)`

You define a signal by decorating a class method with the appropriate decorator.
Only output methods need an actual implementation, the inputs will get patched with the linked output method during runtime.
