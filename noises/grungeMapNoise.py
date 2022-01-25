import random, math, time
from ..helpers.meshHelper import Body
from ..helpers.mathHelper import *
from ..helpers.pngHelper import GrungeMap
from adsk.core import ProgressDialog, Vector2D, Vector3D
import adsk.core

def grungeMapNoise(body:Body, map:GrungeMap, amplitude, inverse, smooth, plane,progressDialog=None):
    if plane == 'xY' or plane == None:
        xValues = [v[0] for v in body.vertices]
        yValues = [v[1] for v in body.vertices]
    elif plane == 'xZ':
        xValues = [v[0] for v in body.vertices]
        yValues = [v[2] for v in body.vertices]
    elif plane == 'yZ':
        xValues = [v[1] for v in body.vertices]
        yValues = [v[2] for v in body.vertices]

    #make a lattice grid
    lattice = map.values
    
    def getNoiseValue(x,y):
        xMin = min(int(x),map.x-1)
        yMin = min(int(y),map.y-1)
        tx = x - xMin
        ty = y - yMin
        if smooth:
            tx = smoothstep(tx)
            ty = smoothstep(ty)

        rx0 = xMin
        rx1 = min(xMin+1,map.x-1)
        ry0 = yMin
        ry1 = min(yMin+1,map.y-1)

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

    xValuesScaled = [(x- minX)/(maxX-minX) * (map.x) for x in xValues]
    yValuesScaled = [(y- minY)/(maxY-minY) * (map.y) for y in yValues]
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
        noise = getNoiseValue(xyValuesScaled[i][0],xyValuesScaled[i][1])
        if inverse:
            normal.scaleBy(noise*amplitude)
        else:
            normal.scaleBy(-noise*amplitude)
        vec.add(normal)
        ###
        body.vertices[i] = vec.asArray()