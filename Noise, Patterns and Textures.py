#Author- Leon Müller
#Description- A Fusion360 Add-In that lets you add noise, patterns, and textures to your MeshBodies.

from tokenize import Double
import adsk.core, adsk.fusion, adsk.cam, traceback, os, sys, random, time

from .helpers import mathHelper
from .helpers import meshHelper
from .helpers import pngHelper
from .helpers.meshHelper import Body, calculateAppropriateNoiseLevel, calculateAverageFaceSize #our own body class

from .noises.valueNoise import *
from .noises.perlinNoise import *
from .noises.randomNoise import *
from .noises.worleyNoise import *
from .noises.grungeMapNoise import *

handlers = []
defaultCommandInputs = ['advancedGroup','seedField','degree','dropList','body_input', 'previewBox','algDesc']
groupCommandChildren = ['stepHeightField', 'stepPaddingField']
groupCommands = ['advancedGroup', 'stepGroup']
panelString = 'ParaMeshModifyPanel'
lastChangedInput = ''

lastStepGroupValue = False
lastAdvancedGroupValue = False

previewIsActive = False
currentGrungeMap: GrungeMap = None
currentPreview = []
currentPreviewMesh = []



def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui  = app.userInterface

        #global progressDialog
        #progressDialog = ui.createProgressDialog()
        #pngHelper.readPng()

        # Get the CommandDefinitions collection.
        cmdDefs = ui.commandDefinitions
        # Create a button command definition.
        buttonSample = cmdDefs.addButtonDefinition('NoiseButton', 
                                                   'Noise, Patterns and Textures', 
                                                   'Lets you add noise, patterns, and textures to your MeshBodies.\n Provides a selection of algorithms and paramaterized settings.',
                                                   './resources/newButton')
        buttonSample.toolClipFilename = 'resources/button/toolClip.png'
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

# Event handler for the commandCreated event. (The Add-In view is opened)
class SampleCommandCreatedEventHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        app = adsk.core.Application.get()
        ui  = app.userInterface
        eventArgs = adsk.core.CommandCreatedEventArgs.cast(args)
        cmd = eventArgs.command

        # Get the CommandInputs collection to create new command inputs.            
        inputs = cmd.commandInputs
        
        global previewIsActive, currentPreview, currentPreviewMesh, lastStepGroupValue, lastAdvancedGroupValue
        previewIsActive = False
        currentPreview = []
        currentPreviewMesh = []
        lastAdvancedGroupValue = False
        lastStepGroupValue = False

        cmd.okButtonText = "Generate"
        #cmd.setDialogInitialSize(100,100)
        cmd.isExecutedWhenPreEmpted = False
        #cmd.helpFile = '/Users/lmueller/Library/Application Support/Autodesk/Autodesk Fusion 360/API/AddIns/Noisy Surfaces/resources/helpPages/buttonHelp.html'
        # Create selection input
        body_input = inputs.addSelectionInput('body_input', 'Select MeshBody', 'Select MeshBody to apply noise to')
        # select only meshbodies
        body_input.addSelectionFilter('MeshBodies')
        body_input.tooltip = "Select the target MeshBodies"
        # I can select more than one body
        body_input.setSelectionLimits(0)
        dropDown = inputs.addDropDownCommandInput('dropList', 'Algorithm', adsk.core.DropDownStyles.TextListDropDownStyle)
        dropDown.tooltip = "Choose a noise algorithm"
        dropDown.listItems.add('Value Noise', True, '')
        dropDown.listItems.add('Perlin Noise', False, '')
        dropDown.listItems.add('Worley Noise', False, '')
        dropDown.listItems.add('Random Noise', False, '')
        dropDown.listItems.add('Adaptive Noise', False, '')
        dropDown.listItems.add('Grunge Map', False, '')
        #dropDown.isFullWidth(False)

        algDescriptionBox = inputs.addTextBoxCommandInput('algDesc', 'Description', "This is only a test of the functionality of the box",3,True)
        algDescriptionBox.text = "Generates noise based on a continous function. The dimension of the function can be specified as well as the resolution."
        #test = inputs.addIntegerSliderListCommandInput('test', 'test', list(range(2,20))+list(range(20,100,5)))


        #degree = inputs.addValueInput('degree', 'Noise Level', '', adsk.core.ValueInput.createByReal(0.25)) 
        degree = inputs.addFloatSliderCommandInput('degree', 'Level', "", 0, 3)
        degree.spinStep = 0.25
        degree.valueOne = 1
        degree.tooltip = "Sets the level of noise"
        #numberField.isEnabled = False
        #Create a check box
        inverseBox = inputs.addBoolValueInput('inverseBox', 'Inverse', True, '', False)
        inverseBox.isVisible = False
        inverseBox.tooltip = "Inverts the result"
        #Create 3 Dimension button row
        dim3Buttons = inputs.addRadioButtonGroupCommandInput('dim3Buttons', 'Dimension')
        #dim3Buttons.isVisible = False
        dim3Buttons.listItems.add('1D', False)
        dim3Buttons.listItems.add('2D', False)
        dim3Buttons.listItems.add('3D', True)
        #Create 2 Dimension button row
        dim2Buttons = inputs.addRadioButtonGroupCommandInput('dim2Buttons', 'Dimension')
        dim2Buttons.isVisible = False
        dim2Buttons.listItems.add('2D', False)
        dim2Buttons.listItems.add('3D', True)

        smoothBox = inputs.addBoolValueInput('smoothBox', 'Smooth', True, '', True)
        #smoothBox.isVisible = False
        smoothBox.tooltip = "Smoothes the result"

        resolutionField = inputs.addIntegerSpinnerCommandInput('resolutionField', 'Resolution', 2, 1000, 1, 10)
        resolutionField.tooltip = "Sets the resolution of the applied noise function. \nThe higher the resolution, the more features are visible."
        #resolutionField.isVisible = False

        resolutionYField = inputs.addIntegerSpinnerCommandInput('resolutionYField', 'ResolutionY', 2, 1000, 1, 10)
        resolutionYField.tooltip = "Sets the y-resolution of the applied noise function. \nThe higher the resolution, the more features are visible."

        # Plane input for 2D noise
        #planeInput = inputs.addSelectionInput('planeInput', 'Plane', 'Select Plane to apply noise to.')
        #planeInput.addSelectionFilter('ConstructionPlanes')
        #planeInput.setSelectionLimits(0,1)
        planeInput = inputs.addButtonRowCommandInput('planeInput', 'Plane', False)
        planeInput.listItems.add("xY", True, 'resources/planeButtons/xY')
        planeInput.listItems.add("xZ", False, 'resources/planeButtons/xZ')
        planeInput.listItems.add("yZ", False, 'resources/planeButtons/yZ')
        planeInput.isVisible = False
        planeInput.tooltip = "Choose an origin plane that the map is projected onto"
        ## Experimental Image Input
        fileDialogButton = inputs.addBoolValueInput('fileDialogButton', 'Choose Grunge Map', False, 'resources/fileDialogButton')
        fileDialogButton.isVisible = False
        fileDialogButton.tooltip = "Choose a PNG Grunge Map."
        imageField = inputs.addImageCommandInput('imageField', '', './resources/exampleGrungeMaps/GrungeMap_008.png')
        #imageField.isFullWidth = True
        imageField.isVisible = False

        # All Command inputs for the step function settings
        # Create group input.
        groupStepInput = inputs.addGroupCommandInput('stepGroup', 'Activate Step Function')
        groupStepInput.isExpanded = False
        groupStepInput.isEnabledCheckBoxDisplayed = True
        groupStepInput.isEnabledCheckBoxChecked = False
        groupStepInput.isVisible = False
        groupStepChildInputs = groupStepInput.children
        #stepHeightField = groupStepChildInputs.addValueInput('stepHeightField', 'Step Height','mm',adsk.core.ValueInput.createByReal(0.5))
        stepPaddingField = groupStepChildInputs.addValueInput('stepPaddingField', 'Padding', 'mm',adsk.core.ValueInput.createByReal(0.1))

        groupAdvancedInput = inputs.addGroupCommandInput('advancedGroup', 'Advanced Settings')
        groupAdvancedInput.isExpanded = False
        groupAdvancedChildInputs = groupAdvancedInput.children
        seedField = groupAdvancedChildInputs.addStringValueInput('seedField', 'Seed', '')
        seedField.tooltip = "Optinal: Sets a seed for the RNG.\n The same seed will always produce the same result."
        #frequencyField = groupAdvancedChildInputs.addFloatSliderCommandInput('frequencyField', 'Frequency', '', 0, 1, False)
        #frequencyField.spinStep = 0.1
        #frequencyField.setText("0","1")
        #frequencyField.valueOne = 1
        frequencyField = groupAdvancedChildInputs.addValueInput('frequencyField', 'Frequency', '', adsk.core.ValueInput.createByReal(1)) 
        frequencyField.isVisible = False
        #Create signed checkbox
        signedBox = groupAdvancedChildInputs.addBoolValueInput('signedBox', 'Signed', True, '', True)
        signedBox.tooltip = "Sets wether the noise can be negative"
        #signedBox.isVisible = False

        #Create Preview Checkbox
        previewBox = inputs.addBoolValueInput('previewBox', 'Preview', True, '', False)
        previewBox.tooltip = "Displays a preview of the result with the current settings"

        # Connect to the execute event.
        onExecute = SampleCommandExecuteHandler()
        cmd.execute.add(onExecute)
        handlers.append(onExecute)
        #ui.messageBox('Creating the command???')

        # Connect to the inputChanged event.
        onInputChanged = SampleCommandInputChangedHandler()
        cmd.inputChanged.add(onInputChanged)
        handlers.append(onInputChanged)
        
        #Connect to the execute preview event
        onExecutePreview = SampleCommandExecutePreviewHandler()
        cmd.executePreview.add(onExecutePreview)
        handlers.append(onExecutePreview)

# Event handler for the inputChanged event.
class SampleCommandInputChangedHandler(adsk.core.InputChangedEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try: 
            app = adsk.core.Application.get()
            ui  = app.userInterface
            product = app.activeProduct #the fusion tab that is active
            rootComp = product.rootComponent # the root component of the active product
            eventArgs = adsk.core.InputChangedEventArgs.cast(args)
            inputs = eventArgs.firingEvent.sender.commandInputs
            # Check the value of the check box.
            changedInput = eventArgs.input
            global lastChangedInput, currentGrungeMap
            global previewIsActive, currentPreview, currentPreviewMesh
            lastChangedInput = changedInput.id
            if changedInput.id == 'previewBox':
                previewIsActive = not previewIsActive
                currentPreview = []
                currentPreviewMesh = []
            elif changedInput.id == 'dropList':
                for i in inputs:
                    if not i.id in defaultCommandInputs and not i.id in groupCommandChildren:
                        i.isVisible = False
                    elif i.id in defaultCommandInputs or i.id in groupCommandChildren:
                        i.isVisible = True
                inverseBox = inputs.itemById('inverseBox')
                dim3Buttons = inputs.itemById('dim3Buttons')
                dim2Buttons = inputs.itemById('dim2Buttons')
                signedBox = inputs.itemById('signedBox')
                smoothBox = inputs.itemById('smoothBox')
                stepGroup = inputs.itemById('stepGroup')
                advancedGroup = inputs.itemById('advancedGroup')
                resolutionField = inputs.itemById('resolutionField')
                resolutionYField = inputs.itemById('resolutionYField')
                frequencyField = inputs.itemById('frequencyField')
                imageField = inputs.itemById('imageField')
                fileDialogButton = inputs.itemById('fileDialogButton')
                planeInput = inputs.itemById('planeInput')
                algDescriptionBox = inputs.itemById('algDesc')

                previewBox = inputs.itemById('previewBox')
                previewBox.value =False
                previewIsActive = False
                currentPreview = []
                currentPreviewMesh = []

                # Change the visibility of the scale value input.
                if changedInput.selectedItem.name == 'Adaptive Noise':
                    inverseBox.isVisible = True
                    algDescriptionBox.text = "A randomly generated noise that preserves the more granular/detailed areas of the mesh. If the 'inverse' box is checked, the less detailed areas of the mesh will be preserved."
                elif changedInput.selectedItem.name == 'Value Noise':
                    dim3Buttons.isVisible = True
                    signedBox.isVisible = True
                    smoothBox.isVisible = True
                    resolutionField.isVisible = True
                    resolutionYField.isVisible = True
                    #frequencyField.isVisible = True
                    algDescriptionBox.text = "Generates noise based on a continous function. The dimension of the function can be specified as well as the resolution."
                elif changedInput.selectedItem.name == 'Perlin Noise':
                    dim2Buttons.isVisible = True
                    signedBox.isVisible = True
                    smoothBox.isVisible = True
                    resolutionField.isVisible = True
                    #frequencyField.isVisible = True
                    algDescriptionBox.text = "Generates noise based on a continous function. The dimension of the function can be specified as well as the resolution."
                elif changedInput.selectedItem.name == 'Worley Noise':
                    dim2Buttons.isVisible = True
                    resolutionField.isVisible = True
                    stepGroup.isVisible = True
                    algDescriptionBox.text = "Generates noise based on distances to randomly distributed points across the mesh. The number of feature points can be set with 'resolution'."
                elif changedInput.selectedItem.name == 'Grunge Map':
                    #rootComp.isOriginFolderLightBulbOn = True
                    planeInput.isVisible = True
                    inverseBox.isVisible = True
                    advancedGroup.isVisible = False
                    smoothBox.isVisible = True
                    imageField.isVisible = True
                    fileDialogButton.isVisible = True
                    currentGrungeMap = pngHelper.readPng(imageField.imageFile)
                    algDescriptionBox.text = "Generates noise based on a PNG image Grunge Map."
                elif changedInput.selectedItem.name == 'Random Noise':
                    algDescriptionBox.text = "A randomly generated noise."
            elif changedInput.id == 'fileDialogButton':
                fileDialog = ui.createFileDialog()
                fileDialog.isMultiSelectEnabled = False
                #print(os.path.dirname(os.path.abspath(__file__))+'/resources/exampleGrungeMaps')
                fileDialog.initialDirectory =  os.path.dirname(os.path.abspath(__file__))+'/resources/exampleGrungeMaps'
                fileDialog.title = 'Choose Grunge Map Image'
                fileDialog.filter = '*.png'
                result = fileDialog.showOpen()
                #Set the new image if one was selected
                if result == 0:
                    filename = fileDialog.filename
                    imageField = inputs.itemById('imageField')
                    imageField.imageFile = filename
                    currentGrungeMap = pngHelper.readPng(filename)
            elif changedInput.id == 'body_input':
                bodyInput = inputs.itemById('body_input')
                degreeField = inputs.itemById('degree')
                if bodyInput.selectionCount > 0:
                    selection = bodyInput.selection(0).entity
                    mesh = selection.mesh
                    body = meshHelper.fusionPolygonMeshToBody(mesh)
                    degreeField.valueOne = calculateAppropriateNoiseLevel(body)
                else:
                    currentPreview = []
                    currentPreviewMesh = []


            app.activeViewport.refresh()  
        except:
            if ui:
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

                
# Event handler for the executePreview event.
class SampleCommandExecutePreviewHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        app = adsk.core.Application.get()
        ui  = app.userInterface
        
        try:
            progressDialog = ui.createProgressDialog()
            progressDialog.hide()
            
            eventArgs = adsk.core.CommandEventArgs.cast(args)
            inputs = eventArgs.command.commandInputs
            stepActive = inputs.itemById('stepGroup').isEnabledCheckBoxChecked
            advancedActive = inputs.itemById('advancedGroup').isExpanded

            global currentPreview, currentPreviewMesh, lastStepGroupValue, lastAdvancedGroupValue
            # The if - block is accessed if a group command input was expanded or collapsed without value changes
            # The elif is accessed else
            if lastChangedInput in groupCommands and previewIsActive and stepActive == lastStepGroupValue:
                selectionList = []
                for i in range(inputs.itemById('body_input').selectionCount):
                    selectionList.append(inputs.itemById('body_input').selection(i).entity)
                for selection in selectionList:
                    selection.isLightBulbOn = False
                    mesh = selection.mesh
                if len(currentPreview) > 0:
                    for body, mesh in zip(currentPreview, currentPreviewMesh):
                        showMeshPreview(body,mesh)
            elif previewIsActive and (not lastChangedInput == 'advancedGroup') and (not lastChangedInput == 'dropList'):
                if not stepActive == lastStepGroupValue:
                    lastStepGroupValue = stepActive
                if not advancedActive == lastAdvancedGroupValue:
                    lastAdvancedGroupValue = advancedActive

                product = app.activeProduct #the fusion tab that is active
                rootComp = product.rootComponent # the root component of the active product
                meshBodies = rootComp.meshBodies
                algorithm, seed, degree, dimension3, dimension2, signed, smooth, resolution, resolutionY, frequency, inverse, stepActive, stepPadding, planeString = getInputs(inputs)

                currentPreview = []
                currentPreviewMesh = []

                selectionList = []
                for i in range(inputs.itemById('body_input').selectionCount):
                    selectionList.append(inputs.itemById('body_input').selection(i).entity)
                for selection in selectionList:
                    mesh = selection.mesh
                    body = meshHelper.fusionPolygonMeshToBody(mesh)

                    computeNoise(progressDialog, algorithm, seed, degree, dimension3, dimension2, signed, smooth, resolution, resolutionY, frequency, inverse, stepActive, stepPadding, planeString, body)

                    selection.isLightBulbOn = False
                    currentPreview.append(body)
                    currentPreviewMesh.append(mesh)
                    showMeshPreview(body,mesh)
                    #app.activeViewport.refresh()  
        except ValueError as err:
            if 'CanceledProgress'in err.args:
                currentPreview = []
                currentPreviewMesh = []
                progressDialog.hide()
            else:
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
        except:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

                


# Event handler for the execute event.
class SampleCommandExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        app = adsk.core.Application.get()
        ui  = app.userInterface
        
        try:
            progressDialog = ui.createProgressDialog()
            progressDialog.hide()
            
            product = app.activeProduct #the fusion tab that is active
            rootComp = product.rootComponent # the root component of the active product
            meshBodies = rootComp.meshBodies
            eventArgs = adsk.core.CommandEventArgs.cast(args)
            # Get the values from the command inputs. 
            inputs = eventArgs.command.commandInputs
            algorithm, seed, degree, dimension3, dimension2, signed, smooth, resolution, resolutionY, frequency, inverse, stepActive, stepPadding, planeString = getInputs(inputs)

            selectionList = []
            for i in range(inputs.itemById('body_input').selectionCount):
                selectionList.append(inputs.itemById('body_input').selection(i).entity)
            for i, selection in enumerate(selectionList):
                mesh = selection.mesh
                body = meshHelper.fusionPolygonMeshToBody(mesh)

                if len(currentPreview) > 0:
                    body = currentPreview[i]
                else:
                    computeNoise(progressDialog, algorithm, seed, degree, dimension3, dimension2, signed, smooth, resolution, resolutionY, frequency, inverse, stepActive, stepPadding, planeString, body)

                # Hide the original meshBody, add and name the new one
                selection.isLightBulbOn = False    
                meshBody = meshBodies.addByTriangleMeshData([x for y in body.vertices for x in y],mesh.triangleNodeIndices,[],[])
                meshBody.name = selection.name + "-" + algorithm 
        except ValueError as err:
            if 'CanceledProgress'in err.args:
                pass
            else:
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
        except:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

def getInputs(inputs):
    algorithm = inputs.itemById('dropList').selectedItem.name
    seed = (inputs.itemById('seedField').value).strip()
    if seed == '':
        seed = None
    degree = inputs.itemById('degree').valueOne
    dimension3 = inputs.itemById('dim3Buttons').selectedItem.name
    dimension2 = inputs.itemById('dim2Buttons').selectedItem.name
    signed = inputs.itemById('signedBox').value
    smooth = inputs.itemById('smoothBox').value
    resolution = inputs.itemById('resolutionField').value
    resolutionY = inputs.itemById('resolutionYField').value
    frequency = inputs.itemById('frequencyField').value
    inverse = inputs.itemById('inverseBox').value
    stepActive = inputs.itemById('stepGroup').isEnabledCheckBoxChecked
    stepPadding = inputs.itemById('stepPaddingField').value

        #Get the construction plane and turn it into a string
    planeInput = inputs.itemById('planeInput')
    planeString = None
    if planeInput.selectedItem.name == "xY":
        planeString = 'xY'
    elif planeInput.selectedItem.name == "xZ":
        planeString = 'xZ'
    elif planeInput.selectedItem.name == "yZ":
        planeString = 'yZ'
    return algorithm,seed,degree,dimension3,dimension2,signed,smooth,resolution,resolutionY,frequency,inverse,stepActive,stepPadding,planeString

def computeNoise(progressDialog, algorithm, seed, degree, dimension3, dimension2, signed, smooth, resolution, resolutionY, frequency, inverse, stepActive, stepPadding, planeString, body):
    progressDialog.show('Computing Noise...', 'Percentage: %p% - %v/%m steps completed',0,len(body.vertices),2)
    if algorithm == 'Adaptive Noise':   
        progressDialog.show('Computing Noise...', 'Percentage: %p% - %v/%m steps completed',0,len(body.facets),2)
        adaptiveVertexDistortion(body, degree, inverse, seed, progressDialog)
    elif algorithm == 'Random Noise': 
        randomDistortion(body, degree, seed)
    elif algorithm == 'Value Noise': 
        if dimension3 == '1D':
            valueNoise1D(body,resolution,degree,frequency,signed,smooth,seed,progressDialog)
        elif dimension3 == '2D':
            valueNoise2D(body,resolution,resolutionY,degree,frequency,signed,smooth,seed, progressDialog)
        elif dimension3 == '3D':
            valueNoise3D(body,resolution,degree,frequency,signed,smooth,seed, progressDialog)
    elif algorithm == 'Perlin Noise': 
        if dimension2 == '2D':
            perlinNoise2D(body,resolution,degree,frequency,signed,smooth,seed,progressDialog)
        elif dimension2 == '3D':
            perlinNoise3D(body,resolution,degree,frequency,signed,smooth,seed,progressDialog)
    elif algorithm == 'Worley Noise': 
        if dimension2 == '2D':
            worleyNoise2D(body, resolution, degree, stepActive, stepPadding, seed=seed, progressDialog=progressDialog)
        elif dimension2 == '3D':
            worleyNoise3D(body, resolution, degree, stepActive, stepPadding, seed=seed, progressDialog=progressDialog)
    elif algorithm == 'Grunge Map': 
        grungeMapNoise(body,currentGrungeMap,degree,inverse,smooth, planeString, progressDialog)

def showMeshPreview(body:Body, mesh:adsk.fusion.MeshBody):
    try: 
        app = adsk.core.Application.get()
        ui  = app.userInterface
        product = app.activeProduct 
        rootComp = product.rootComponent 
        graphics = rootComp.customGraphicsGroups.add()
        graphics.id = 'MeshPreview'
        coords = adsk.fusion.CustomGraphicsCoordinates.create([x for y in body.vertices for x in y])
        lines = graphics.addLines(coords, mesh.triangleNodeIndices, False, [])
        lines.weight = 1
        meshGraphics = graphics.addMesh(coords, mesh.triangleNodeIndices, [], [])
        #color = adsk.core.Color.create(219, 213, 26,100)
        #colorEffect = adsk.fusion.CustomGraphicsShowThroughColorEffect.create(color, 0.25)
        #colorEffect = adsk.fusion.CustomGraphicsSolidColorEffect.create(color)
        #mesh.color = colorEffect
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

def addToTimeline():
    app = adsk.core.Application.get()
    ui  = app.userInterface
    product = app.activeProduct 
    timeline = product.timeline
    groups = timeline.timelineGroups
    group = groups.add(1,2)


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
