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

handlers = []
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
        dropDown.listItems.add('Random Noise Generation', True, '')
        dropDown.listItems.add('Adaptive Noise Generation', False, '')
        #dropDown.isFullWidth(False)

        # Create the value inputs to get the number of Donuts to be created as well as their width
        seedField = inputs.addValueInput('seedField', 'Seed', '', adsk.core.ValueInput.createByReal(0))
        degree = inputs.addValueInput('degree', 'Noise Degree', '', adsk.core.ValueInput.createByReal(0.25)) 
        #numberField.isEnabled = False
        #Create a check box to get if a random number of donuts should be generated
        inverseBox = inputs.addBoolValueInput('inverseBox', 'Inverse', True, '', False)
        inverseBox.isEnabled = False
        inverseBox.isVisible = False

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
            inverseBox = inputs.itemById('inverseBox')
			
            # Change the visibility of the scale value input.
            if changedInput.selectedItem.name == 'Adaptive Noise Generation':
                inverseBox.isEnabled = True
                inverseBox.isVisible = True
            else:
                inverseBox.isEnabled = False
                inverseBox.isVisible = False


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
            if algorithm == 'Adaptive Noise Generation':   
                inverse = inputs.itemById('inverseBox').value
                adaptiveVertexDistortion(body, degree, inverse, seed)
            elif algorithm == 'Random Noise Generation': 
                randomDistortion(body, degree, seed)
            meshBodies.addByTriangleMeshData([x for y in body.vertices for x in y],mesh.triangleNodeIndices,[],[])
            

        # This is the test block for meshes that come out of fusion 

        #bodies = rootComp.bRepBodies
        #meshBodies = rootComp.meshBodies
        #body = meshBodies.item(0)
        #mesh = body.mesh
        #coords = meshHelper.fusionPolygonMeshToBody(mesh)
        #adaptiveVertexDistortion(coords,0.25,inverse=False)
        #randomDistortion(coords,0.01,1887)
        #print(len(coords.vertices), len(coords.normals))
        #coords = randomDistortionForVertices(coords,2)
        #coords = adaptiveVertexDistortion(coords, 0.02)
        #print(type(mesh.normalVectors[0].asArray()))
        #print([list(x.asArray()) for x in mesh.normalVectors])
        #To keep the old normal vectors, set the third parameter to mesh.normalVectorsAsDouble
        #meshBodies.addByTriangleMeshData([x for y in coords.vertices for x in y],mesh.triangleNodeIndices,[],[])
        
        
        # This is the test block for meshes that have been imported from obj files

        #body = meshHelper.readObjMesh('/Users/lmueller/Desktop/plane.obj')
        #scaleMeshByAxis(body,2,1,0.5)
        #randomGeneralDistortion(body,1)
        #randomDistortion(body,1)
        #valueNoise(body, 1997)
        #meshHelper.writeObjMesh('/Users/lmueller/Desktop/test.obj', coords)








# TODO: Dass die funktionen den body returnen ist natürlich aktuell nutzlos. Der originale body wird verändert 

#def scaleMesh(body:Body, scalar:int) -> Body:
#    body.vertices = (scalar*Matrix(body.vertices)).tolist()
#    return body

#def scaleMeshByAxis(body:Body, x=1., y=1., z=1.) -> Body:
#    mat = Matrix(body.vertices)
#    mat[:,0] = (x*(Matrix(body.vertices)[:,0]))
#    mat[:,1] = (y*(Matrix(body.vertices)[:,1]))
#    mat[:,2] = (z*(Matrix(body.vertices)[:,2]))
#    body.vertices = mat.tolist()
#    return body

#randomly distorts each x,y,z coordinate of each vertex
def randomDistortion(body:Body, degree:float, seed:int=None) -> Body:
    if seed:
        random.seed(seed)
    res = []
    for v in body.vertices:
        res.append([random.uniform(-degree,degree)+float(el) for el in v])
    body.vertices = res
    return body

def randomDistortionForVertices(vertices, degree:float, seed:int=None):
    if seed:
        random.seed(seed)
    res = []
    for v in vertices:
        res.append([random.uniform(-degree,degree)+float(el) for el in v])
    return res

#randomly distorts each vertex. This seems to preserve some faces TODO: Warum?
def randomGeneralDistortion(body:Body, degree:float, seed:int=None) -> Body:
    if seed:
        random.seed(seed)
    res = []
    for v in body.vertices:
        i = random.uniform(-degree,degree)
        res.append([i+float(el) for el in v])
    body.vertices = res
    return body

# Distorts each vertex by the given degree. The degree is scaled according to the face size
# If inverse=False then bigger faces are distorted more extremely
# if inverse=True then smaller faces are distorted more extremely
def adaptiveVertexDistortion(body, degree:float, inverse=False, seed:int=None):
    if seed:
        random.seed(seed)
    res = []
    areas = []
    for f in body.facets:
        a = adsk.core.Vector3D.create(body.vertices[f[0]-1][0], body.vertices[f[0]-1][1], body.vertices[f[0]-1][2])
        b = adsk.core.Vector3D.create(body.vertices[f[1]-1][0], body.vertices[f[1]-1][1], body.vertices[f[1]-1][2])
        c = adsk.core.Vector3D.create(body.vertices[f[2]-1][0], body.vertices[f[2]-1][1], body.vertices[f[2]-1][2])
        areas.append(0.5* (a.crossProduct(b).crossProduct(a.crossProduct(c))).length)
    if inverse:
        maxArea = min(areas)
        minArea = max(areas)
    else:
        minArea = min(areas)
        maxArea = max(areas)
    areas = list(map(lambda x: (x- minArea)/(maxArea-minArea)*(1-0)+0, areas))
    for f,a in zip(body.facets,areas):
        body.vertices[f[0]-1] = [random.uniform(-degree,degree)*a + float(el) for el in body.vertices[f[0]-1]]
        body.vertices[f[1]-1] = [random.uniform(-degree,degree)*a + float(el) for el in body.vertices[f[1]-1]]
        body.vertices[f[2]-1] = [random.uniform(-degree,degree)*a + float(el) for el in body.vertices[f[2]-1]]
    return res

#similar to the one above but only scales in one direction. Looks super weird
def weirdScalyDistortion(body, degree:float, seed:int=None):
    if seed:
        random.seed(seed)
    res = []
    areas = []
    for f in body.facets:
        a = adsk.core.Vector3D.create(body.vertices[f[0]-1][0], body.vertices[f[0]-1][1], body.vertices[f[0]-1][2])
        b = adsk.core.Vector3D.create(body.vertices[f[1]-1][0], body.vertices[f[1]-1][1], body.vertices[f[1]-1][2])
        c = adsk.core.Vector3D.create(body.vertices[f[2]-1][0], body.vertices[f[2]-1][1], body.vertices[f[2]-1][2])
        areas.append(0.5* (a.crossProduct(b).crossProduct(a.crossProduct(c))).length)
    minArea = min(areas)
    maxArea = max(areas)
    areas = list(map(lambda x: (x- minArea)/(maxArea-minArea), areas))
    print(min(areas), max(areas))
    for f,a in zip(body.facets,areas):
        i = random.uniform(-degree,degree)
        
        body.vertices[f[0]-1] = [i*a + float(el) for el in body.vertices[f[0]-1]]
        body.vertices[f[1]-1] = [i*a + float(el) for el in body.vertices[f[1]-1]]
        body.vertices[f[2]-1] = [i*a + float(el) for el in body.vertices[f[2]-1]]
    return res

def valueNoise(body:Body, seed:int) -> Body:
    if seed:
        random.seed(seed)
    xValues = [v[0] for v in body.vertices]
    yValues = [v[1] for v in body.vertices]
    zValues = [v[2] for v in body.vertices]
    print(max(xValues), max(yValues), max(zValues))
    print(min(xValues), min(yValues), min(zValues))
    # define the 3d grid to distribute the random points onto
    p1 = min(xValues), min(yValues), min(zValues)
    return body


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
