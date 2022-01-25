import random
from ..helpers.meshHelper import Body
from ..helpers.mathHelper import *
from adsk.core import ProgressDialog, Vector2D, Vector3D

def perlinNoise3D(body:Body, resolution:int, amplitude:float=1, frequency:float=1, signed:bool=True, smooth:bool=True, seed:int=None, progressDialog:ProgressDialog=None) -> Body:
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
                #Todo: Think about wether a signed perlin noise is meaningful
                if signed:
                    bottomRange = -1
                else:
                    bottomRange = 0
                x = random.uniform(bottomRange,1)
                y = random.uniform(bottomRange,1)
                z = random.uniform(bottomRange,1)
                gradient = Vector3D.create(x,y,z)
                gradient.normalize()
                lattice[i][j].append(gradient)
    
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

        # Get the surrounding gradients
        c000 = lattice[rx0][ry0][rz0]
        c100 = lattice[rx1][ry0][rz0]
        c010 = lattice[rx0][ry1][rz0]
        c001 = lattice[rx0][ry0][rz1]
        c110 = lattice[rx1][ry1][rz0]
        c101 = lattice[rx1][ry0][rz1]
        c011 = lattice[rx0][ry1][rz1]
        c111 = lattice[rx1][ry1][rz1]

        #Generate Vectors from the point to the gradients
        p000 = Vector3D.create(tx, ty, tz); 
        p100 = Vector3D.create(tx-1, ty, tz); 
        p010 = Vector3D.create(tx, ty-1, tz); 
        p110 = Vector3D.create(tx-1, ty-1, tz); 
 
        p001 = Vector3D.create(tx, ty, tz-1); 
        p101 = Vector3D.create(tx-1, ty, tz-1); 
        p011 = Vector3D.create(tx, ty-1, tz-1); 
        p111 = Vector3D.create(tx-1, ty-1, tz-1); 

        nx00 = lerp(c000.dotProduct(p000), c100.dotProduct(p100), tx) 
        nx01 = lerp(c001.dotProduct(p001), c101.dotProduct(p101), tx)
        nx10 = lerp(c010.dotProduct(p010), c110.dotProduct(p110), tx)
        nx11 = lerp(c011.dotProduct(p011), c111.dotProduct(p111), tx)

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
def perlinNoise2D(body:Body, resolution:int, amplitude:float=1, frequency:float=1, signed:bool=True, smooth:bool=True, seed:int=None, progressDialog:ProgressDialog=None) -> Body:
    if seed:
        random.seed(seed)
    xValues = [v[0] for v in body.vertices]
    yValues = [v[1] for v in body.vertices]

    #make a lattice grid
    lattice = []
    for i in range(resolution):
        lattice.append([])
        for j in range(resolution):
            if signed:
                    bottomRange = -1
            else:
                bottomRange = 0
            x = random.uniform(bottomRange,1)
            y = random.uniform(bottomRange,1)
            gradient = Vector2D.create(x,y)
            gradient.normalize()
            lattice[i].append(gradient)
    
    def getNoiseValue(x,y):
        xMin = min(int(x),len(lattice)-1)
        yMin = min(int(y),len(lattice)-1)
        tx = x - xMin
        ty = y - yMin
        if smooth:
            tx = smoothstep(tx)
            ty = smoothstep(ty)

        rx0 = xMin
        rx1 = min(xMin+1,len(lattice)-1)
        ry0 = yMin
        ry1 = min(yMin+1,len(lattice)-1)

        c00 = lattice[rx0][ry0]
        c10 = lattice[rx1][ry0]
        c01 = lattice[rx0][ry1]
        c11 = lattice[rx1][ry1]

        #Generate Vectors from point to grid gradients
        p00 = Vector2D.create(tx, ty); 
        p10 = Vector2D.create(tx-1, ty); 
        p01 = Vector2D.create(tx, ty-1); 
        p11 = Vector2D.create(tx-1, ty-1); 

        nx0 = lerp(c00.dotProduct(p00), c10.dotProduct(p10), tx) 
        nx1 = lerp(c01.dotProduct(p01), c11.dotProduct(p11), tx) 
        return lerp(nx0, nx1, ty)
    
    minX = min(xValues)
    maxX = max(xValues)
    minY = min(yValues)
    maxY = max(yValues)

    xValuesScaled = [(x- minX)/(maxX-minX) * (resolution-1) for x in xValues]
    yValuesScaled = [(y- minY)/(maxY-minY) * (resolution-1) for y in yValues]
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