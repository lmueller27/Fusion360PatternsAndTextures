#Author-
#Description-

from tokenize import Double
import adsk.core, adsk.fusion, adsk.cam, traceback, os, sys, random, time
#sys.path.append("./packages")
#import sympy
#from sympy import *

from .helpers import mathHelper
from .helpers import meshHelper
from .helpers.meshHelper import Body #our own body class

from .noises.valueNoise import *
from .noises.perlinNoise import *
from .noises.randomNoise import *

handlers = []
defaultCommandInputs = ['seedField','degree','dropList','body_input']
panelString = 'ParaMeshModifyPanel'

def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui  = app.userInterface

        # Get the CommandDefinitions collection.
        cmdDefs = ui.commandDefinitions
        # Create a button command definition.
        buttonSample = cmdDefs.addButtonDefinition('NoiseButton', 
                                                   'Noisy Surfaces', 
                                                   'lorem ipsum',
                                                   './resources/button')
        # Connect to the command created event.
        sampleCommandCreated = SampleCommandCreatedEventHandler()
        buttonSample.commandCreated.add(sampleCommandCreated)
        handlers.append(sampleCommandCreated)
        # Get the ADD-INS panel in the model workspace. 
        
        addInsPanel = ui.allToolbarPanels.itemById(panelString)
        # Add the button to the bottom of the panel.
        buttonControl = addInsPanel.controls.addCommand(buttonSample)
        # Make the button available in the panel.
        buttonControl.isPromotedByDefault = True
        buttonControl.isPromoted = True

    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

# Event handler for the commandCreated event.
class SampleCommandCreatedEventHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        eventArgs = adsk.core.CommandCreatedEventArgs.cast(args)
        cmd = eventArgs.command

        # Get the CommandInputs collection to create new command inputs.            
        inputs = cmd.commandInputs

        # Create selection input
        body_input = inputs.addSelectionInput('body_input', 'Select MeshBody', 'Select MeshBody')
        # select only meshbodies
        body_input.addSelectionFilter('MeshBodies')
        # I can select more than one body
        body_input.setSelectionLimits(0)
        dropDown = inputs.addDropDownCommandInput('dropList', 'Algorithm', adsk.core.DropDownStyles.TextListDropDownStyle)
        dropDown.listItems.add('Random Noise', True, '')
        dropDown.listItems.add('Adaptive Noise', False, '')
        dropDown.listItems.add('Value Noise', False, '')
        dropDown.listItems.add('Perlin Noise', False, '')
        #dropDown.isFullWidth(False)

        # Create the value inputs to get the number of Donuts to be created as well as their width
        seedField = inputs.addValueInput('seedField', 'Seed', '', adsk.core.ValueInput.createByReal(0))
        degree = inputs.addValueInput('degree', 'Noise Level', '', adsk.core.ValueInput.createByReal(0.25)) 
        #numberField.isEnabled = False
        #Create a check box
        inverseBox = inputs.addBoolValueInput('inverseBox', 'Inverse', True, '', False)
        inverseBox.isVisible = False
        #Create 3 Dimension button row
        dim3Buttons = inputs.addRadioButtonGroupCommandInput('dim3Buttons', 'Dimension')
        dim3Buttons.isVisible = False
        dim3Buttons.listItems.add('1', False)
        dim3Buttons.listItems.add('2', False)
        dim3Buttons.listItems.add('3', True)
        #Create 2 Dimension button row
        dim2Buttons = inputs.addRadioButtonGroupCommandInput('dim2Buttons', 'Dimension')
        dim2Buttons.isVisible = False
        dim2Buttons.listItems.add('2', False)
        dim2Buttons.listItems.add('3', True)
        #Create signed checkbox
        signedBox = inputs.addBoolValueInput('signedBox', 'Signed', True, '', True)
        signedBox.isVisible = False

        smoothBox = inputs.addBoolValueInput('smoothBox', 'Smooth', True, '', True)
        smoothBox.isVisible = False

        resolutionField = inputs.addIntegerSpinnerCommandInput('resolutionField', 'Resolution', 2, 100, 1, 10)
        resolutionField.isVisible = False
        frequencyField = inputs.addValueInput('frequencyField', 'Frequency', '', adsk.core.ValueInput.createByReal(1)) 
        frequencyField.isVisible = False

        # Connect to the execute event.
        onExecute = SampleCommandExecuteHandler()
        cmd.execute.add(onExecute)
        handlers.append(onExecute)
        #ui.messageBox('Creating the command???')

        # Connect to the inputChanged event.
        onInputChanged = SampleCommandInputChangedHandler()
        cmd.inputChanged.add(onInputChanged)
        handlers.append(onInputChanged)

# Event handler for the inputChanged event.
class SampleCommandInputChangedHandler(adsk.core.InputChangedEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        eventArgs = adsk.core.InputChangedEventArgs.cast(args)
        # Check the value of the check box.
        changedInput = eventArgs.input
        if changedInput.id == 'dropList':
            inputs = eventArgs.firingEvent.sender.commandInputs

            for i in inputs:
                if not i.id in defaultCommandInputs:
                    i.isVisible = False
            inverseBox = inputs.itemById('inverseBox')
            dim3Buttons = inputs.itemById('dim3Buttons')
            dim2Buttons = inputs.itemById('dim2Buttons')
            signedBox = inputs.itemById('signedBox')
            smoothBox = inputs.itemById('smoothBox')
            resolutionField = inputs.itemById('resolutionField')
            frequencyField = inputs.itemById('frequencyField')
            # Change the visibility of the scale value input.
            if changedInput.selectedItem.name == 'Adaptive Noise':
                inverseBox.isVisible = True
            elif changedInput.selectedItem.name == 'Value Noise':
                dim3Buttons.isVisible = True
                signedBox.isVisible = True
                smoothBox.isVisible = True
                resolutionField.isVisible = True
                frequencyField.isVisible = True
            elif changedInput.selectedItem.name == 'Perlin Noise':
                dim2Buttons.isVisible = True
                signedBox.isVisible = True
                smoothBox.isVisible = True
                resolutionField.isVisible = True
                frequencyField.isVisible = True

                

                


# Event handler for the execute event.
class SampleCommandExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        app = adsk.core.Application.get()
        product = app.activeProduct #the fusion tab that is active
        rootComp = product.rootComponent # the root component of the active product
        meshBodies = rootComp.meshBodies
        eventArgs = adsk.core.CommandEventArgs.cast(args)

        # Get the values from the command inputs. 
        inputs = eventArgs.command.commandInputs

        algorithm = inputs.itemById('dropList').selectedItem.name
        seed = int(inputs.itemById('seedField').value)
        if seed == 0:
            seed = None
        degree = inputs.itemById('degree').value

        selectionList = []
        for i in range(inputs.itemById('body_input').selectionCount):
            selectionList.append(inputs.itemById('body_input').selection(i).entity)
        for selection in selectionList:
            selection.isLightBulbOn = False
            mesh = selection.mesh
            body = meshHelper.fusionPolygonMeshToBody(mesh)
            if algorithm == 'Adaptive Noise':   
                inverse = inputs.itemById('inverseBox').value
                adaptiveVertexDistortion(body, degree, inverse, seed)
            elif algorithm == 'Random Noise': 
                randomDistortion(body, degree, seed)
            elif algorithm == 'Value Noise': 
                dimension = inputs.itemById('dim3Buttons').selectedItem.name
                signed = inputs.itemById('signedBox').value
                smooth = inputs.itemById('smoothBox').value
                resolution = inputs.itemById('resolutionField').value
                frequency = inputs.itemById('frequencyField').value
                if dimension == '1':
                    valueNoise1D(body,resolution,degree,frequency,signed,smooth,seed)
                elif dimension == '2':
                    valueNoise2D(body,resolution,degree,frequency,signed,smooth,seed)
                elif dimension == '3':
                    valueNoise3D(body,resolution,degree,frequency,signed,smooth,seed)
            elif algorithm == 'Perlin Noise': 
                dimension = inputs.itemById('dim2Buttons').selectedItem.name
                signed = inputs.itemById('signedBox').value
                smooth = inputs.itemById('smoothBox').value
                resolution = inputs.itemById('resolutionField').value
                frequency = inputs.itemById('frequencyField').value
                if dimension == '2':
                    perlinNoise2D(body,resolution,degree,frequency,signed,smooth,seed)
                elif dimension == '3':
                    perlinNoise3D(body,resolution,degree,frequency,signed,smooth,seed)
                
            meshBodies.addByTriangleMeshData([x for y in body.vertices for x in y],mesh.triangleNodeIndices,[],[])


def stop(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui  = app.userInterface
        # Delete the button definition.
        buttonExample = ui.commandDefinitions.itemById('NoiseButton')
        if buttonExample:
            buttonExample.deleteMe()
            
        # Get panel the control is in.
        addInsPanel = ui.allToolbarPanels.itemById(panelString)

        # Get and delete the button control.
        buttonControl = addInsPanel.controls.itemById('NoiseButton')
        if buttonControl:
            buttonControl.deleteMe()

    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
