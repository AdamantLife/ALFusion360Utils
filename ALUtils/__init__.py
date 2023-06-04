import adsk.core
from dataclasses import dataclass
from typing import List

try:
    from ..config import DEBUG
except:
    DEBUG = False

## All Root Components are generated with the following Entity Token
ROOTET = '/v4BAAEAAwAAAAAAAAAAAAAA'

def log(*args, sep = " ", app: adsk.core.Application = None, level: adsk.core.LogLevels = adsk.core.LogLevels.InfoLogLevel, force_console: bool = False)->None:
    """ Adaptation of futils implementation to make it function as a more intuitive console log """
    if not isinstance(sep, str):
        raise TypeError(f"Invalid sep; sep must be of type str: {sep}")
    if app is None: app = getApp()

    ## Typical console log schema
    message = sep.join(map(str,args))

    ## Copied from futils
    print(message)
    
    # Log all errors to Fusion log file.
    if level == adsk.core.LogLevels.ErrorLogLevel:
        log_type = adsk.core.LogTypes.FileLogType
        app.log(message, level, log_type)

    # If config.DEBUG is True write all log messages to the console.
    if DEBUG or force_console:
        log_type = adsk.core.LogTypes.ConsoleLogType
        app.log(message, level, log_type)

    app.log(message)

def getApp():
    """ Returns the current Application """
    return adsk.core.Application.get()

def getUI(app = None):
    """ Returns the Application's User Interface"""
    if app is None: app = getApp()
    return app.userInterface

def getActiveDoc(app = None):
    """ Returns the Application's Active Document """
    if app is None: app = getApp()
    return app.activeDocument

def getDocID(app = None, document = None):
    """ Returns the Document ID """
    if document: return document.creationId
    if app is None: app = getApp()
    return app.activeDocument.creationId

def create_handler(event:adsk.core.Event, handlers: list, classes: dict)->adsk.core.EventHandler:
    """ Allows for shorthand creation of multiple Event Handler classes/instances.
    
        This method is similar to futil.create_handler except that it's much more
        strict in order to improve transparency: all components necessary to build
        the Handler Class are required arguments.

        Arguments:
            event- The Event to add a Handler to

            handlers- The handlers collection which persists the lifetime
                        of the created Event Handler

            classes- A dictionary where the keys are Event.name strings and
                    the values are a length two tuple: (callback, handler_class)

            callback - The callback to evoke in EventHandler.notify

            handler_class- The specific EventHandler subclass to use
    """
    callback, handler_class = classes.get(event.name, [None, None])
    if not handler_class:
        raise TypeError(f"Invalid command {event.name}")
    if not callback:
        raise TypeError(f"Callback not defined for {event.name}")
    
    class EventHandler(handler_class):
            def notify(self,args):
                try:
                    callback(args)
                except:
                    import traceback
                    log(f"""ERROR: {self.name}
{traceback.format_exc()}""", level=adsk.core.LogLevels.ErrorLogLevel)

    handler = EventHandler()
    event.add(handler)
    handlers.append(handler)
    return handler

@dataclass
class CommandPlacement:
    """ Object Describing the icon placement of a Command """
    workspace: str
    panel: str
    command_beside: str = None
    is_promoted: bool = False

class Command():
    ## Subclasses should assign an AppData class to initialize
    appdata = None

    def __init__(self, id: str, name: str, description: str, icon_folder: str = None, commandicons: List[CommandPlacement] = None):
        self.id = id
        self.name = name
        self.description = description
        self.icon_folder = icon_folder

        if commandicons is None: commandicons = list()
        self.commandicons = commandicons

        self.app = None
        ## Reference store for commandCreated handlers
        self._command_handlers = []
        ## Reference store for command's sub-handlers
        ## which are cleaned up when the command ends
        self.local_handlers = []

    def start(self, app:adsk.core.Application = None)-> tuple[adsk.core.Application, adsk.core.UserInterface]:
        """ Default startup method for Commands.
        
            COMMANDINFO- A dictionary containing information necessary to set up the Command

            app- The application to set the Command up for (defaults to the adsk.core.Application.get)
            callbacks- A List of callback functions that will be run after initial start
        """
        if app is None:
            if self.app is None: app = getApp()
            else: app = self.app
        self.app = app
        ui = getUI(app)
        ## Check if command def is already created
        cmd_def = ui.commandDefinitions.itemById(self.id)
        if not cmd_def:
            # Create a command Definition.
            cmd_def = ui.commandDefinitions.addButtonDefinition(self.id, self.name, self.description, self.icon_folder)

        ## command_created is a property which returns False on this base class
        ## Subclasses should override command_created with a function, which will
        ## make the following truthy
        if self.command_created:
            # Define an event handler for the command created event. It will be called when the button is clicked.
            self._createHandler(cmd_def.commandCreated, handlers = self._command_handlers)

            for placement in self.commandicons:
                # ******** Add a button into the UI so the user can run the command. ********
                # Get the target workspace the button will be created in.
                workspace = ui.workspaces.itemById(placement.workspace)

                # Get the panel the button will be created in.
                panel = workspace.toolbarPanels.itemById(placement.panel)

                # Create the button command control in the UI after the specified existing command.
                control = panel.controls.addCommand(cmd_def, placement.command_beside, False)

                # Specify if the command is promoted to the main toolbar. 
                control.isPromoted = placement.is_promoted

        if self.appdata:
            self.appdata = self.appdata.loadfromfile()
        ## Returning the UserInterface reference for subclasses to use
        return app, ui

    # Executed when add-in is stopped.
    def stop(self, app: adsk.core.Application = None)-> tuple[adsk.core.Application, adsk.core.UserInterface]:
        ## self.app should not be None at this point
        if app is None: app = self.app
        ui = getUI(app)
        for placement in self.commandicons:
            workspace = ui.workspaces.itemById(placement.workspace)
            panel = workspace.toolbarPanels.itemById(placement.panel)
            ## The button
            command_control = panel.controls.itemById(self.id)
            if command_control:
                command_control.deleteMe()

        command_definition = ui.commandDefinitions.itemById(self.id)
        # Delete the command definition
        if command_definition:
            command_definition.deleteMe()

        ## Clear reference to App for good measure
        self.app = None

        ## Save App Data
        if self.appdata:
            self.appdata.save()

        ## Clear handlers
        self.local_handlers = []
        self._command_handlers = []

        ## Return Application and UserInterface references for subclasses
        return app, ui

    @property
    def command_created(self)->False:
        """ In order to implement Command Dialog, override in Subclass """
        return False
    
    def _command_created(self, args: adsk.core.CommandEventArgs)->None:
        """ Wraps the Subclasses' command_created functions in order to ensure that the rest of the event handlers are setup  """
        self.command_created(args)
        command = args.command

        self._createHandler(command.destroy)
        if self.command_execute:
            self._createHandler(command.execute)
        if self.command_input_changed:
            self._createHandler(command.inputChanged)
        if self.command_preview:
            self._createHandler(command.executePreview)
        if self.command_validate_input:
            self._createHandler(command.validateInputs)
    
    def command_destroy(self, args: adsk.core.CommandEventArgs)-> None:
        """ Cleans up after the Command Dialog is destroyed by clearing self.local_handlers.
        
            Always implemented When setup_commandchain is called. Subclasses should
            put in a super() call prior to taking other actions.
        """
        self.local_handlers = []

    @property
    def command_execute(self)->False:
        """ Fires when the User selects the Ok button in the Command Dialog.
        
            Should be implemented by Subclass if it implements command_created.
        """
        return False
    @property
    def command_input_changed(self)->False:
        """ Fires when the input of the Command Dialog changes.
        
            Optionally implementable by Subclass.
        """
        return False
    @property
    def command_preview(self)->False:
        """ Fires when the input of the Command Dialog changes.

            Optionally implementable by Subclass.
        """
        return False
    @property
    def command_validate_input(self)->False:
        """ Fires when the input of the Command Dialog changes.
            If implemented, should set args.areInputsValid to True if  inputs are valid, or 
            False if they are invalid. Inputs can be accessed from args.inputs.
        
            Optionally implmentable by Subclass.
        """
        return False
    
    def _create_handler(self, event, handlers = None, classes = None):
        if classes is None:
            classes = {
                ## Note that _command_created is called instead of command_created because
                ## _command_created ensure the rest of the command stack is initialized
                "CommandCreated": (self._command_created, adsk.core.CommandCreatedEventHandler),
                "OnDestroy": (self.command_destroy, adsk.core.CommandEventHandler),
                "OnExecute": (self.command_execute, adsk.core.CommandEventHandler),
                "InputValueChanged": (self.command_input_changed,adsk.core.InputChangedEventHandler),
                "OnExecutePreview": (self.command_preview,adsk.core.CommandEventHandler),
                "AreInputsValid": (self.command_validate_input,adsk.core.ValidateInputsEventHandler),
            }

        if handlers is None: handlers = self.local_handlers

        return create_handler(event, handlers=handlers, classes=classes)