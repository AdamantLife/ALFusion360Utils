# ALFusion360Utils
 ### Additional Utility Classes and Functions for Fusion 360 Add-in Development

 This module contains a variety of utility functions- such as `print()`-like logging and shorthand functions for entity access- as well as an Object-oriented Command Class.


 ## Example Code
 ``` python
 ## MyCommand/entry.py

 import ALUtils
 import adsk.core

 class MyCommand(ALUtils.Command):
    active = False

    ## By defining command_created, the Command's Icon will be added to the UI,
    ## the Command Definition will be created, and ALUtils.Command will check
    ## to see if other Command Event Handlers were defined
    def command_created(self, args: adsk.core.CommandCreatedEventArgs):
        """ Sets up the Command Dialog """
        command = args.command
        inputs = command.commandInputs

        activebutton = inputs.addBoolValueInput("active", "Active Button", False, "", self.active)
        activebutton.tooltip = "Toggle Add-in Activity"
        activebutton.text =  "Active" if self.active else "Inactive"
    
    ## Defining command_input_changed will create and register a new
    ## InputChangedEventHandler and register it during onCommandCreated
    def command_input_changed(self, args: adsk.core.InputChangedEventArgs):
        """ Updates the Command Dialog when the Input changes"""
        changed_input = args.input
        if changed_input.id == "active":
            changed_input.text = "Active" if changed_input.value else "Inactive"

    ## Defining command_execute will create and register a new CommandEventHandler
    ## and register it during onCommandCreated
    def command_execute(self, args: adsk.core.CommandEventArgs):
        """ Fires when the OK Button is pressed on the Command Dialog """
        inputs = args.command.commandInputs
        active: adsk.core.BooleanValueCommandInput = inputs.itemById('active')
        self.active = active.value

    ## command_destroy will cleanup all Handlers generated during 
    ## onCommandCreated. Subclasses can define additional actions, but
    ## should always call super() in order to ensure handlers are cleaned up
    def command_destroy(self, args: adsk.core.CommandEventArgs):
        super().command_destroy()

        ## Print-like logging
        ALUtils.log("This app is", "Active" if self.active else "Inactive")


## MyCommand/__init__.py

from .entry import Command
from ...ALUtils import CommandPlacement
from ...ALUtils import io
from ... import config

## These are initialization arguments for the Command Object
## They could be defined in the class definition, but this is
## more convenient to update
COMMANDINFO = {
    "id" : f'{config.COMPANY_NAME}_{config.ADDIN_NAME}_MyCommandDialog',
    "name" : 'My Command',
    "description" : 'Toggle Command Example',
    "icon_folder" : str((io.getLocalDir(__file__) / 'resources').resolve()),
}

## Description of where to Place an icon (in the Solid Environment/Tab)
## Initialized into a CommandPlacement Instance below
SOLIDICON = {
    "workspace" : 'FusionSolidEnvironment',
    "panel" : 'SolidModifyPanel',
    "command_beside" : 'ChangeParameterCommand',
    "is_promoted" : False
}

## Intialize the Command and import this reference into
## the Add-in's start() commands list
IntuitiveRenameDialog = Command(**COMMANDINFO,

commandicons = [
    ## You can add additional icons be creating more CommandPlacement instances
    CommandPlacement(**SOLIDICON)
    ])
 ```
