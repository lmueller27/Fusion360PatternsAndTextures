import adsk
from adsk.core import ProgressDialog, Vector2D, Vector3D
#from sympy.solvers.diophantine.diophantine import norm


class Body:
  def __init__(self, vertices:"list[list[float]]", textureCoordinates, normals, facets, name:str = "Body", mtllib = None):
    self.name = name 
    self.vertices = vertices
    self.textureCoordinates = textureCoordinates
    self.normals = normals
    self.facets = facets
    self.mtllib = mtllib

# Reads a Wavefront Obj file and returns it as a Body 
def readObjMesh(path: str) -> Body:
    vertices = []
    textureCoordinates = []
    vertexNormals = []
    facets = []
    with open(path) as file:
        for line in file:
            listOfValues = line.rstrip().split()
            if len(listOfValues) > 0:
                if listOfValues[0] == 'v':
                    vertices.append([float(element) for element in listOfValues[1:]])
                elif listOfValues[0] == 'vt':
                    textureCoordinates.append([float(element) for element in listOfValues[1:]])
                elif listOfValues[0] == 'vn':
                    vertexNormals.append([float(element) for element in listOfValues[1:]])
                elif listOfValues[0] == 'f':
                    facets.append([float(element) for element in listOfValues[1:]])
                elif listOfValues[0] == 'g':
                    name = listOfValues[1]
                elif listOfValues[0] == 'mtllib':
                    mtllib = listOfValues[1]
    return Body(vertices, textureCoordinates, vertexNormals, facets, name, mtllib)

# Writes a Body to a Wavefront Obj file at path
def writeObjMesh(path: str, body: Body): 
    with open(path, 'w') as file:
        if body.mtllib:
            file.write('mtllib ' + body.mtllib + '\n')
        file.write('g ' + body.name + '\n')
        for v in body.vertices:
            file.write('v ' + " ".join([str(element) for element in v]) + '\n')
        for vt in body.textureCoordinates:
            file.write('vt ' + " ".join([str(element) for element in vt]) + '\n')
        for vn in body.normals:
            file.write('vn ' + " ".join([str(element) for element in vn]) + '\n')
        for f in body.facets:
            file.write('f ' + " ".join([str(element) for element in f]) + '\n')

#Transforms the a Fusion360 PolygonMesh into a Body. Only uses triangles, not quads
def fusionPolygonMeshToBody(mesh) -> Body:
    vertices = [x.getData()[1:] for x in mesh.nodeCoordinates]
    normals = []
    normalVectors = list(mesh.normalVectorsAsDouble)
    for i in range(len(normalVectors)):
        if i%3==0:
            normals.append(normalVectors[i:i+3])
    facets = []
    if mesh.triangleCount > 0:
        indices = list(mesh.triangleNodeIndices)
        for i in range(len(indices)):
            if i%3==0:
                facets.append([x+1 for x in indices[i:i+3]]) # We have to increase each index by 1, because fusion and obj use different indeces
    return Body(vertices, [], normals, facets, "dummy", "plane.mtl") #ToDo: read mtllib

def calculateAppropriateNoiseLevel(body:Body) -> float:
    n = 10
    xValues = [v[0] for v in body.vertices[0::n]]
    yValues = [v[1] for v in body.vertices[0::n]]
    zValues = [v[2] for v in body.vertices[0::n]]

    rangeX = max(xValues)-min(xValues)
    rangeY = max(yValues)-min(yValues)
    rangeZ = max(zValues)-min(zValues)
    mean = (rangeX+rangeY+rangeZ)/3
    return mean/10

def calculateAverageFaceSize(body:Body, percentage:float) -> float:
    n = int(len(body.facets)*percentage)
    faces = body.facets[0::n]
    areas = []
    for f in faces:
        a = Vector3D.create(body.vertices[f[0]-1][0], body.vertices[f[0]-1][1], body.vertices[f[0]-1][2])
        b = Vector3D.create(body.vertices[f[1]-1][0], body.vertices[f[1]-1][1], body.vertices[f[1]-1][2])
        c = Vector3D.create(body.vertices[f[2]-1][0], body.vertices[f[2]-1][1], body.vertices[f[2]-1][2])
        areas.append(0.5* (a.crossProduct(b).crossProduct(a.crossProduct(c))).length)
    mean = sum(areas)/len(areas)
    print(mean)
    return mean
