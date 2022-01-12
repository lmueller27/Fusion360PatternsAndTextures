#Author-
#Description-

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
defaultCommandInputs = ['advancedGroup','seedField','degree','dropList','body_input', 'previewBox']
groupCommandChildren = ['stepHeightField', 'stepPaddingField']
groupCommands = ['advancedGroup', 'stepGroup']
panelString = 'ParaMeshModifyPanel'
lastChangedInput = ''

lastStepGroupValue = False
lastAdvancedGroupValue = False

previewIsActive = False
currentPreview: Body = None
currentPreviewMesh = None

def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui  = app.userInterface

        #pngHelper.readPng()
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
        app = adsk.core.Application.get()
        ui  = app.userInterface
        eventArgs = adsk.core.CommandCreatedEventArgs.cast(args)
        cmd = eventArgs.command

        # Get the CommandInputs collection to create new command inputs.            
        inputs = cmd.commandInputs
        
        global previewIsActive, currentPreview, currentPreviewMesh, lastStepGroupValue, lastAdvancedGroupValue
        previewIsActive = False
        currentPreview = None
        currentPreviewMesh = None
        lastAdvancedGroupValue = False
        lastStepGroupValue = False

        cmd.okButtonText = "Generate"
        #cmd.setDialogInitialSize(100,100)
        cmd.isExecutedWhenPreEmpted = False
        # Create selection input
        body_input = inputs.addSelectionInput('body_input', 'Select MeshBody', 'Select MeshBody')
        # select only meshbodies
        body_input.addSelectionFilter('MeshBodies')
        body_input.tooltip = "Select the target MeshBodies"
        # I can select more than one body
        body_input.setSelectionLimits(0)
        dropDown = inputs.addDropDownCommandInput('dropList', 'Algorithm', adsk.core.DropDownStyles.TextListDropDownStyle)
        dropDown.tooltip = "Choose a Noise algorithm."
        dropDown.listItems.add('Random Noise', True, '')
        dropDown.listItems.add('Adaptive Noise', False, '')
        dropDown.listItems.add('Value Noise', False, '')
        dropDown.listItems.add('Perlin Noise', False, '')
        dropDown.listItems.add('Worley Noise', False, '')
        dropDown.listItems.add('Grunge Map', False, '')
        #dropDown.isFullWidth(False)

        degree = inputs.addValueInput('degree', 'Noise Level', '', adsk.core.ValueInput.createByReal(0.25)) 
        degree.tooltip = "Sets the level of noise to be applied."
        #numberField.isEnabled = False
        #Create a check box
        inverseBox = inputs.addBoolValueInput('inverseBox', 'Inverse', True, '', False)
        inverseBox.isVisible = False
        inverseBox.tooltip = "Inverts the noise values."
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

        smoothBox = inputs.addBoolValueInput('smoothBox', 'Smooth', True, '', True)
        smoothBox.isVisible = False
        smoothBox.tooltip = "Smoothes the result."

        resolutionField = inputs.addIntegerSpinnerCommandInput('resolutionField', 'Resolution', 2, 1000, 1, 10)
        resolutionField.isVisible = False

        # Plane input for 2D noise
        planeInput = inputs.addSelectionInput('planeInput', 'Plane', 'Select Plane to apply noise to.')
        planeInput.addSelectionFilter('ConstructionPlanes')
        planeInput.setSelectionLimits(0,1)
        planeInput.isVisible = False
        planeInput.tooltip = "Choose an origin plane to apply the noise to. If no plane is selected, the xY plane is used."
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
        seedField.tooltip = "Optinal: Sets a seed for the RNG."
        #frequencyField = groupAdvancedChildInputs.addFloatSliderCommandInput('frequencyField', 'Frequency', '', 0, 1, False)
        #frequencyField.spinStep = 0.1
        #frequencyField.setText("0","1")
        #frequencyField.valueOne = 1
        frequencyField = groupAdvancedChildInputs.addValueInput('frequencyField', 'Frequency', '', adsk.core.ValueInput.createByReal(1)) 
        frequencyField.isVisible = False
        #Create signed checkbox
        signedBox = groupAdvancedChildInputs.addBoolValueInput('signedBox', 'Signed', True, '', True)
        signedBox.isVisible = False

        #Create Preview Checkbox
        previewBox = inputs.addBoolValueInput('previewBox', 'Preview', True, '', False)
        previewBox.tooltip = "Displays a preview of the result with the current settings."

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
            global lastChangedInput
            lastChangedInput = changedInput.id
            if changedInput.id == 'previewBox':
                global previewIsActive, currentPreview, currentPreviewMesh
                previewIsActive = not previewIsActive
                currentPreview = None
                currentPreviewMesh = None
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
                frequencyField = inputs.itemById('frequencyField')
                imageField = inputs.itemById('imageField')
                fileDialogButton = inputs.itemById('fileDialogButton')
                planeInput = inputs.itemById('planeInput')
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
                elif changedInput.selectedItem.name == 'Worley Noise':
                    dim2Buttons.isVisible = True
                    resolutionField.isVisible = True
                    stepGroup.isVisible = True
                elif changedInput.selectedItem.name == 'Grunge Map':
                    #rootComp.isOriginFolderLightBulbOn = True
                    planeInput.isVisible = True
                    inverseBox.isVisible = True
                    advancedGroup.isVisible = False
                    smoothBox.isVisible = True
                    imageField.isVisible = True
                    fileDialogButton.isVisible = True
            elif changedInput.id == 'fileDialogButton':
                fileDialog = ui.createFileDialog()
                fileDialog.isMultiSelectEnabled = False
                print(os.path.dirname(os.path.abspath(__file__))+'/resources/exampleGrungeMaps')
                fileDialog.initialDirectory =  os.path.dirname(os.path.abspath(__file__))+'/resources/exampleGrungeMaps'
                fileDialog.title = 'Choose Grunge Map Image'
                fileDialog.filter = '*.png'
                result = fileDialog.showOpen()
                #Set the new image if one was selected
                if result == 0:
                    filename = fileDialog.filename
                    imageField = inputs.itemById('imageField')
                    imageField.imageFile = filename
            elif changedInput.id == 'body_input':
                bodyInput = inputs.itemById('body_input')
                degreeField = inputs.itemById('degree')
                if bodyInput.selectionCount > 0:
                    selection = bodyInput.selection(0).entity
                    mesh = selection.mesh
                    body = meshHelper.fusionPolygonMeshToBody(mesh)
                    degreeField.value = calculateAppropriateNoiseLevel(body)
                else:
                    currentPreview = None
                    currentPreviewMesh = None


            app.activeViewport.refresh()  
        except:
            if ui:
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

                
# Event handler for the executePreview event.
class SampleCommandExecutePreviewHandler(adsk.core.CommandEventHandler):
    #progressDialog:ProgressDialog
    def __init__(self):
        super().__init__()

    def notify(self, args):
        app = adsk.core.Application.get()
        ui  = app.userInterface
        try:
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
                #showMeshPreview(currentPreview,mesh)
                if not currentPreview == None:
                    showMeshPreview(currentPreview,currentPreviewMesh)
            elif previewIsActive and (not lastChangedInput == 'advancedGroup'):
                if not stepActive == lastStepGroupValue:
                    lastStepGroupValue = stepActive
                if not advancedActive == lastAdvancedGroupValue:
                    lastAdvancedGroupValue = advancedActive


                #progressDialog = ui.createProgressDialog()
                #progressDialog.hide()
                progressDialog = None
                
                product = app.activeProduct #the fusion tab that is active
                rootComp = product.rootComponent # the root component of the active product
                meshBodies = rootComp.meshBodies
                #eventArgs = adsk.core.CommandEventArgs.cast(args)

                # Get the values from the command inputs. 
                #inputs = eventArgs.command.commandInputs

                algorithm = inputs.itemById('dropList').selectedItem.name
                seed = (inputs.itemById('seedField').value).strip()
                if seed == '':
                    seed = None
                degree = inputs.itemById('degree').value
                dimension3 = inputs.itemById('dim3Buttons').selectedItem.name
                dimension2 = inputs.itemById('dim2Buttons').selectedItem.name
                signed = inputs.itemById('signedBox').value
                smooth = inputs.itemById('smoothBox').value
                stepActive = inputs.itemById('stepGroup').isEnabledCheckBoxChecked
                stepPadding = inputs.itemById('stepPaddingField').value
                resolution = inputs.itemById('resolutionField').value
                frequency = inputs.itemById('frequencyField').value
                grungeMap = inputs.itemById('imageField').imageFile
                inverse = inputs.itemById('inverseBox').value

                #Get the construction plane and turn it into a string
                plane = inputs.itemById('planeInput')
                planeString = None
                if plane.selectionCount > 0:
                    planeInput = plane.selection(0).entity
                    if planeInput== rootComp.xYConstructionPlane:
                        planeString = 'xY'
                    elif planeInput== rootComp.xZConstructionPlane:
                        planeString = 'xZ'
                    elif planeInput== rootComp.yZConstructionPlane:
                        planeString = 'yZ'

                selectionList = []
                for i in range(inputs.itemById('body_input').selectionCount):
                    selectionList.append(inputs.itemById('body_input').selection(i).entity)
                for selection in selectionList:
                    selection.isLightBulbOn = False
                    mesh = selection.mesh
                    body = meshHelper.fusionPolygonMeshToBody(mesh)

                    #progressDialog.reset()
                    #progressDialog.show('Computing Noise...', 'Percentage: %p% - %v/%m steps completed',0,len(body.vertices))

                    if algorithm == 'Adaptive Noise':   
                        adaptiveVertexDistortion(body, degree, inverse, seed)
                    elif algorithm == 'Random Noise': 
                        randomDistortion(body, degree, seed)
                    elif algorithm == 'Value Noise': 
                        if dimension3 == '1':
                            valueNoise1D(body,resolution,degree,frequency,signed,smooth,seed,progressDialog)
                        elif dimension3 == '2':
                            valueNoise2D(body,resolution,degree,frequency,signed,smooth,seed,progressDialog)
                        elif dimension3 == '3':
                            valueNoise3D(body,resolution,degree,frequency,signed,smooth,seed,progressDialog)
                    elif algorithm == 'Perlin Noise': 
                        if dimension2 == '2':
                            perlinNoise2D(body,resolution,degree,frequency,signed,smooth,seed,progressDialog)
                        elif dimension2 == '3':
                            perlinNoise3D(body,resolution,degree,frequency,signed,smooth,seed,progressDialog)
                    elif algorithm == 'Worley Noise': 
                        progressDialog = ui.createProgressDialog()
                        progressDialog.show('Computing Noise...', 'Percentage: %p% - %v/%m steps completed',0,len(body.vertices))
                        if dimension2 == '2':
                            worleyNoise2D(body, resolution, degree, stepActive, stepPadding, seed=seed, progressDialog=progressDialog)
                        elif dimension2 == '3':
                            worleyNoise3D(body, resolution, degree, stepActive, stepPadding, seed=seed, progressDialog=progressDialog)
                    elif algorithm == 'Grunge Map': 
                        progressDialog = ui.createProgressDialog()
                        progressDialog.show('Computing Noise...', 'Percentage: %p% - %v/%m steps completed',0,len(body.vertices))
                        grungeMapNoise(body,pngHelper.readPng(grungeMap), degree, inverse,smooth,progressDialog,planeString)

                    currentPreview = body
                    currentPreviewMesh = mesh
                    
                    showMeshPreview(body,mesh)

                    app.activeViewport.refresh()  
        except:
            if ui:
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
                


# Event handler for the execute event.
class SampleCommandExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            app = adsk.core.Application.get()
            ui  = app.userInterface

            progressDialog = ui.createProgressDialog()
            progressDialog.hide()
            
            product = app.activeProduct #the fusion tab that is active
            rootComp = product.rootComponent # the root component of the active product
            meshBodies = rootComp.meshBodies
            eventArgs = adsk.core.CommandEventArgs.cast(args)

            # Get the values from the command inputs. 
            inputs = eventArgs.command.commandInputs

            algorithm = inputs.itemById('dropList').selectedItem.name
            seed = (inputs.itemById('seedField').value).strip()
            if seed == '':
                seed = None
            degree = inputs.itemById('degree').value
            dimension3 = inputs.itemById('dim3Buttons').selectedItem.name
            dimension2 = inputs.itemById('dim2Buttons').selectedItem.name
            signed = inputs.itemById('signedBox').value
            smooth = inputs.itemById('smoothBox').value
            resolution = inputs.itemById('resolutionField').value
            frequency = inputs.itemById('frequencyField').value
            grungeMap = inputs.itemById('imageField').imageFile
            inverse = inputs.itemById('inverseBox').value
            stepActive = inputs.itemById('stepGroup').isEnabledCheckBoxChecked
            stepPadding = inputs.itemById('stepPaddingField').value

            #Get the construction plane and turn it into a string
            plane = inputs.itemById('planeInput')
            planeString = None
            if plane.selectionCount > 0:
                planeInput = plane.selection(0).entity
                if planeInput== rootComp.xYConstructionPlane:
                    planeString = 'xY'
                elif planeInput== rootComp.xZConstructionPlane:
                    planeString = 'xZ'
                elif planeInput== rootComp.yZConstructionPlane:
                    planeString = 'yZ'

            selectionList = []
            for i in range(inputs.itemById('body_input').selectionCount):
                selectionList.append(inputs.itemById('body_input').selection(i).entity)
            for selection in selectionList:
                selection.isLightBulbOn = False
                mesh = selection.mesh
                if currentPreview==None:
                    body = meshHelper.fusionPolygonMeshToBody(mesh)
                    progressDialog.show('Computing Noise...', 'Percentage: %p% - %v/%m steps completed',0,len(body.vertices))
                    if algorithm == 'Adaptive Noise':   
                        adaptiveVertexDistortion(body, degree, inverse, seed,progressDialog)
                    elif algorithm == 'Random Noise': 
                        randomDistortion(body, degree, seed)
                    elif algorithm == 'Value Noise': 
                        if dimension3 == '1':
                            valueNoise1D(body,resolution,degree,frequency,signed,smooth,seed,progressDialog)
                        elif dimension3 == '2':
                            valueNoise2D(body,resolution,degree,frequency,signed,smooth,seed,progressDialog)
                        elif dimension3 == '3':
                            valueNoise3D(body,resolution,degree,frequency,signed,smooth,seed, progressDialog)
                    elif algorithm == 'Perlin Noise': 
                        if dimension2 == '2':
                            perlinNoise2D(body,resolution,degree,frequency,signed,smooth,seed,progressDialog)
                        elif dimension2 == '3':
                            perlinNoise3D(body,resolution,degree,frequency,signed,smooth,seed,progressDialog)
                    elif algorithm == 'Worley Noise': 
                        if dimension2 == '2':
                            worleyNoise2D(body, resolution, degree, stepActive, stepPadding, seed=seed, progressDialog=progressDialog)
                        elif dimension2 == '3':
                            worleyNoise3D(body, resolution, degree, stepActive, stepPadding, seed=seed, progressDialog=progressDialog)
                    elif algorithm == 'Grunge Map': 
                        grungeMapNoise(body,pngHelper.readPng(grungeMap),degree,inverse,smooth,progressDialog, planeString)
                else:
                    body = currentPreview
                    
                meshBodies.addByTriangleMeshData([x for y in body.vertices for x in y],mesh.triangleNodeIndices,[],[])
                # Add the operation to the timeline
                #addToTimeline()
        except:
            if ui:
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


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
