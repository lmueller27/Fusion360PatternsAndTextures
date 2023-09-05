import random, math, time
from ..helpers.meshHelper import Body
from ..helpers.mathHelper import *
from adsk.core import ProgressDialog, Vector2D, Vector3D
import adsk.core


def worleyNoise3D(body:Body, resolution:int, amplitude:float, step:bool, stepPadding:float, seed:int=None, progressDialog:ProgressDialog=None) -> Body: 
    start = time.time()
        
    if seed:
        random.seed(seed)
    xValues = [v[0] for v in body.vertices]
    yValues = [v[1] for v in body.vertices]
    zValues = [v[2] for v in body.vertices]

    minX = min(xValues)
    maxX = max(xValues)
    minY = min(yValues)
    maxY = max(yValues)
    minZ = min(zValues)
    maxZ = max(zValues)

    #Generate random points in space
    #features = []
    features = random.choices(body.vertices,k=resolution)
    for i in range(len(features)):
        # This Block chooses random points on the bodies surface. Cool.
        features[i] = Vector3D.create(features[i][0],features[i][1],features[i][2])

    def distance3D(a,b):
        return math.sqrt((a.x-b.x)**2 + (a.y-b.y)**2 + (a.z-b.z)**2)
    
    #print(time.time()-start)
    allSteps = len(body.vertices)
    maxSteps = allSteps - allSteps/20
    for i in range(len(body.vertices)):

        # Update progress value of progress dialog
        if progressDialog:
            if progressDialog.wasCancelled:
                raise ValueError('CanceledProgress')
            if i%(int(allSteps/20)+1)==0:
                progressDialog.progressValue = i+1
            elif i > maxSteps:
                progressDialog.progressValue = progressDialog.maximumValue

        v = body.vertices[i]
        n = body.normals[i]
        vec = Vector3D.create(v[0],v[1],v[2])
        normal = Vector3D.create(n[0],n[1],n[2])
        normal.normalize()

        # Another option is to specify the nth closest not the closest
        # This is obviously extremly slow
        #Experimental:
        if step:
            closest = [distance3D(vec,x) for x in sorted(features,key=lambda x:distance3D(x,vec))[:2]]
            if abs(closest[0]-closest[1]) < stepPadding:
                dist = 0
            #elif abs(closest[0]-closest[1]) < 0.2:
            #    dist = 0.5
            else:
                dist = 1
        else:
            dist = min([distance3D(vec,f) for f in features])
        
        noise = dist*amplitude
        normal.scaleBy(noise)
        vec.add(normal)
        body.vertices[i] = vec.asArray()
    #print(time.time()-start)
    return body


def worleyNoise2D(body:Body, resolution:int, amplitude:float, step:bool, stepPadding:float, seed:int=None, progressDialog:ProgressDialog=None) -> Body: 
    if seed:
        random.seed(seed)
    xValues = [v[0] for v in body.vertices]
    yValues = [v[1] for v in body.vertices]
    #zValues = [v[2] for v in body.vertices]

    minX = min(xValues)
    maxX = max(xValues)
    minY = min(yValues)
    maxY = max(yValues)

    #Generate random points in space
    features = random.choices(body.vertices,k=resolution)
    for i in range(len(features)):
        # This Block chooses random points on the bodies surface. Cool.
        features[i] = Vector2D.create(features[i][0],features[i][1])
    
    def distance2D(a,b):
        return math.sqrt((a.x-b.x)**2 + (a.y-b.y)**2)

    allSteps = len(body.vertices)
    maxSteps = allSteps - allSteps/20
    for i in range(len(body.vertices)):
        b = body.vertices[i]
        n = body.normals[i]
        vec = Vector3D.create(b[0],b[1],b[2])
        normal = Vector3D.create(n[0],n[1],n[2])
        normal.normalize()
        
        # Update progress value of progress dialog
        if progressDialog:
            if progressDialog.wasCancelled:
                raise ValueError('CanceledProgress')
            if i%(int(allSteps/20)+1)==0:
                progressDialog.progressValue = i+1
            elif i > maxSteps:
                progressDialog.progressValue = progressDialog.maximumValue
        
        ###
        if step:
            closest = [distance2D(vec,x) for x in sorted(features,key=lambda x:distance2D(x,vec))[:2]]
            if abs(closest[0]-closest[1]) < stepPadding:
                dist = 0
            else:
                dist = 1
        else:
            dist = min([distance2D(vec,f) for f in features])
        
        normal.scaleBy(dist*amplitude)
        vec.add(normal)
        ###
        body.vertices[i] = vec.asArray()

    return body

