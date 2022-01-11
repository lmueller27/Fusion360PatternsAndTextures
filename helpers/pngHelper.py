from ..ext import png

class GrungeMap:
    def __init__(self, sizeX:int, sizeY:int, values:"list[int]"):
        self.x = sizeX
        self.y = sizeY
        self.values = values

def readPng(filename):
    file = png.Reader(filename=filename)
    info = file.read_flat()
    print(info[3])
    sizeX = info[1]
    sizeY = info[0]
    isGrey = info[3]['greyscale']
    hasAlpha = info[3]['alpha']
    if 'palette' in info[3]:
        palette = info[3]['palette']
    else:
        palette = None
    pixelValues = list(info[2])
    #print(len(pixelValues))
    #print(sizeX, sizeY)
    minValue = min(pixelValues)
    maxValue = max(pixelValues)

    if isGrey:
        if hasAlpha:
            pixelsWithoutAlpha = pixelValues[0::2]
            flatValuesScaled = [(x-minValue)/(maxValue-minValue) for x in pixelsWithoutAlpha]
        else:
            flatValuesScaled = [(x-minValue)/(maxValue-minValue) for x in pixelValues]
    else: 
        if palette:
            #print(len(palette[0]))
            def applyPalette(x):
                return round(0.299*palette[x][0]+0.587*palette[x][1]+0.114*palette[x][2],1)
            appliedPalette = [applyPalette(x) for x in pixelValues]
            print(len(appliedPalette))
            minValue = min(appliedPalette)
            maxValue = max(appliedPalette)
            flatValuesScaled = [(x-minValue)/(maxValue-minValue) for x in appliedPalette]
            #print(flatValuesScaled)
        else:
            if hasAlpha:
                r = pixelValues[0::4]
                g = pixelValues[1::4]
                b = pixelValues[2::4]
            else:
                r = pixelValues[0::3]
                g = pixelValues[1::3]
                b = pixelValues[2::3]
            flatValuesScaled = [(x-minValue)/(maxValue-minValue) for x in list(map(lambda x: 0.299*x[0]+0.587*x[1]+0.114*x[2], zip(r,g,b)))]

    values = []
    for i in range(sizeX):
        values.append([])
        for j in range(sizeY):
            values[i].append(flatValuesScaled[i*sizeX + j])
    return GrungeMap(sizeX,sizeY,values)