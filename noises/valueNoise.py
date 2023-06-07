import random
from ..helpers.meshHelper import Body
from ..helpers.mathHelper import *
from adsk.core import ProgressDialog, Vector2D, Vector3D

def valueNoise3D(body:Body, resolution:int, amplitude:float=1, frequency:float=1, signed:bool=True, smooth:bool=True, seed:int=None, progressDialog:ProgressDialog=None) -> Body:
    if seed:
        random.seed(seed)
    xValues = [v[0] for v in body.vertices]
    yValues = [v[1] for v in body.vertices]
    zValues = [v[2] for v in body.vertices]
    #make a lattice grid
    lattice = []
    for i in range(resolution): # This is the ugliest matrix init of all time
        lattice.append([])
        for j in range(resolution):
            lattice[i].append([])
            for k in range(resolution):
                if signed:
                    lattice[i][j].append(random.uniform(-1,1))
                else:
                    lattice[i][j].append(random.uniform(0,1))
    
    def getNoiseValue(x,y,z):
        xMin = min(int(x),len(lattice)-1)
        yMin = min(int(y),len(lattice)-1)
        zMin = min(int(z),len(lattice)-1)
        tx = x - xMin
        ty = y - yMin
        tz = z - zMin
        if smooth:
            tx = smoothstep(tx)
            ty = smoothstep(ty)
            tz = smoothstep(tz)

        rx0 = xMin
        rx1 = min(xMin+1,len(lattice)-1)
        ry0 = yMin
        ry1 = min(yMin+1,len(lattice)-1)
        rz0 = zMin
        rz1 = min(zMin+1,len(lattice)-1)

        c000 = lattice[rx0][ry0][rz0]
        c100 = lattice[rx1][ry0][rz0]
        c010 = lattice[rx0][ry1][rz0]
        c001 = lattice[rx0][ry0][rz1]
        c110 = lattice[rx1][ry1][rz0]
        c101 = lattice[rx1][ry0][rz1]
        c011 = lattice[rx0][ry1][rz1]
        c111 = lattice[rx1][ry1][rz1]

        nx00 = lerp(c000, c100, tx) 
        nx01 = lerp(c001, c101, tx)
        nx10 = lerp(c010, c110, tx)
        nx11 = lerp(c011, c111, tx)

        nxy0 = lerp(nx00, nx10, ty)
        nxy1 = lerp(nx01, nx11, ty)

        return lerp(nxy0, nxy1, tz)
    
    minX = min(xValues)
    maxX = max(xValues)
    minY = min(yValues)
    maxY = max(yValues)
    minZ = min(zValues)
    maxZ = max(zValues)

    xValuesScaled = [(x- minX)/(maxX-minX) * (resolution-1) for x in xValues]
    yValuesScaled = [(y- minY)/(maxY-minY) * (resolution-1) for y in yValues]
    if not maxZ == minZ:
        zValuesScaled = [(z- minZ)/(maxZ-minZ) * (resolution-1) for z in zValues]
    else:
        zValuesScaled = zValues
    xyzValuesScaled = list(zip(xValuesScaled,yValuesScaled,zValuesScaled))

    allSteps = len(body.vertices)
    maxSteps = allSteps - allSteps/20
    for i in range(len(xyzValuesScaled)):
        # Update progress value of progress dialog
        if progressDialog:
            if progressDialog.wasCancelled:
                raise ValueError('CanceledProgress')
            if i%int(allSteps/20)==0:
                progressDialog.progressValue = i+1
            elif i > maxSteps:
                progressDialog.progressValue = progressDialog.maximumValue
        
        b = body.vertices[i]
        n = body.normals[i]

        vec = Vector3D.create(b[0],b[1],b[2])
        normal = Vector3D.create(n[0],n[1],n[2])
        normal.normalize()
        noise = getNoiseValue(xyzValuesScaled[i][0]*frequency,xyzValuesScaled[i][1]*frequency,xyzValuesScaled[i][2]*frequency)
        normal.scaleBy(noise*amplitude)
        vec.add(normal)
        body.vertices[i] = vec.asArray()
    return body


#frequency>1 -> compress the curve, frequency<1 -> stretch the curve
# We don't allow frequencies > 1, as our curve is not periodic. 
def valueNoise2D(body:Body, resolutionX:int, resolutionY:int, amplitude:float=1, frequency:float=1, signed:bool=True, smooth:bool=True, seed:int=None, progressDialog:ProgressDialog=None) -> Body:
    if seed:
        random.seed(seed)
    xValues = [v[0] for v in body.vertices]
    yValues = [v[1] for v in body.vertices]
    zValues = [v[2] for v in body.vertices]

    #make a lattice grid
    lattice = []
    for i in range(resolutionX):
        lattice.append([])
        for j in range(resolutionY):
            if signed:
                lattice[i].append(random.uniform(-1,1))
            else:
                lattice[i].append(random.uniform(0,1))
    
    def getNoiseValue(x,y):
        xMin = min(int(x),len(lattice)-1)
        yMin = min(int(y),len(lattice[0])-1)
        tx = x - xMin
        ty = y - yMin
        if smooth:
            tx = smoothstep(tx)
            ty = smoothstep(ty)

        rx0 = xMin
        rx1 = min(xMin+1,len(lattice)-1)
        ry0 = yMin
        ry1 = min(yMin+1,len(lattice[0])-1)

        c00 = lattice[rx0][ry0]
        c10 = lattice[rx1][ry0]
        c01 = lattice[rx0][ry1]
        c11 = lattice[rx1][ry1]

        nx0 = lerp(c00, c10, tx) 
        nx1 = lerp(c01, c11, tx) 
        return lerp(nx0, nx1, ty)
    
    minX = min(xValues)
    maxX = max(xValues)
    minY = min(yValues)
    maxY = max(yValues)

    xValuesScaled = [(x- minX)/(maxX-minX) * (resolutionX-1) for x in xValues]
    yValuesScaled = [(y- minY)/(maxY-minY) * (resolutionY-1) for y in yValues]
    xyValuesScaled = list(zip(xValuesScaled,yValuesScaled))

    allSteps = len(body.vertices)
    maxSteps = allSteps - allSteps/20
    for i in range(len(xyValuesScaled)):
        # Update progress value of progress dialog
        if progressDialog:
            if progressDialog.wasCancelled:
                raise ValueError('CanceledProgress')
            if i%int(allSteps/20)==0:
                progressDialog.progressValue = i+1
            elif i > maxSteps:
                progressDialog.progressValue = progressDialog.maximumValue

        b = body.vertices[i]
        n = body.normals[i]
        vec = Vector3D.create(b[0],b[1],b[2])
        normal = Vector3D.create(n[0],n[1],n[2])
        normal.normalize()
        ###
        noise = getNoiseValue(xyValuesScaled[i][0]*frequency,xyValuesScaled[i][1]*frequency)
        normal.scaleBy(noise*amplitude)
        vec.add(normal)
        ###
        body.vertices[i] = vec.asArray()

        #Here a proper linAlg library could be useful for performance and for noise in normal vector direction...
        #though the noise in one diretion can look much cooler sometimes. should be an option
        #body.vertices[i][2] += getNoiseValue(xyValuesScaled[i][0],xyValuesScaled[i][1]) 
    



def valueNoise1D(body:Body, resolution:int, amplitude:float=1, frequency:float=1, signed:bool=True, smooth:bool=True, seed:int=None, progressDialog:ProgressDialog=None) -> Body: 
    if seed:
        random.seed(seed)
    xValues = [v[0] for v in body.vertices]
    #yValues = [v[1] for v in body.vertices]
    #zValues = [v[2] for v in body.vertices]

    #make a lattice grid
    lattice = []
    for i in range(resolution):
        if signed:
            lattice.append(random.uniform(-1,1))
        else:
            lattice.append(random.uniform(0,1))
    
    def getNoiseValue(x):
        xMin = min(int(x),len(lattice)-2)
        t = x-xMin
        if smooth:
            t = smoothstep(t)
        return lerp(lattice[xMin],lattice[xMin+1],t)

    minX = min(xValues)
    maxX = max(xValues)
    xValuesScaled = [(x- minX)/(maxX-minX) * (resolution-1) for x in xValues]

    allSteps = len(body.vertices)
    maxSteps = allSteps - allSteps/20
    for i in range(len(xValuesScaled)):
        # Update progress value of progress dialog
        if progressDialog:
            if progressDialog.wasCancelled:
                raise ValueError('CanceledProgress')
            if i%int(allSteps/20)==0:
                progressDialog.progressValue = i+1
            elif i > maxSteps:
                progressDialog.progressValue = progressDialog.maximumValue

        #n = (xValuesScaled[i]/len(body.vertices)) * resolution
        body.vertices[i][2] += getNoiseValue(xValuesScaled[i]*frequency)*amplitude
        


    return body