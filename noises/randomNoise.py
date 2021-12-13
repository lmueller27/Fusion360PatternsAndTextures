import random
from ..helpers.meshHelper import Body
from adsk.core import Vector2D, Vector3D

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
        a = Vector3D.create(body.vertices[f[0]-1][0], body.vertices[f[0]-1][1], body.vertices[f[0]-1][2])
        b = Vector3D.create(body.vertices[f[1]-1][0], body.vertices[f[1]-1][1], body.vertices[f[1]-1][2])
        c = Vector3D.create(body.vertices[f[2]-1][0], body.vertices[f[2]-1][1], body.vertices[f[2]-1][2])
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
        a = Vector3D.create(body.vertices[f[0]-1][0], body.vertices[f[0]-1][1], body.vertices[f[0]-1][2])
        b = Vector3D.create(body.vertices[f[1]-1][0], body.vertices[f[1]-1][1], body.vertices[f[1]-1][2])
        c = Vector3D.create(body.vertices[f[2]-1][0], body.vertices[f[2]-1][1], body.vertices[f[2]-1][2])
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