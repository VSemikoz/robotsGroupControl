import struct
import Queue
BOT_R = 28

if __name__ == "__main__":
    import sys

    print "This module should not be run as an executable"
    sys.exit()

CELL_PX_SIZE = 28
BOT_ECHO_RANGE = 300
CHUNK_SIZE = 16 * (2 * BOT_R / CELL_PX_SIZE)

SYMBOL_TO_BIT_DICT = {'/': 0b0000,
                      ' ': 0b0001,
                      '#': 0b0010,
                      'X': 0b0101,
                      '?': 0b0100,
                      '$': 0b1000,
                      'O': 0b1001}


# 0bxx00 - unknown cell                       '/'
# 0bxx01 - passable cell                      ' '
# 0bxx10 - wall cell                          '#'
# 0bxx11 - cell near wall (non-wall cage)     'X'
# 0bx1xx - cell near wall
# 0bx0xx - cell not near wall

# Tests done
class Chunk:
    def __init__(self, size):
        self._cellCount = size * size
        self._grid = [0 for x in range(self._cellCount)]
        self._size = size
        self.searchState = False

    def update(self, update, forceSet=False):
        if len(update) < 5:
            # ToDo warning
            return

        size = struct.unpack('i', update[:4])[0]
        grid = update[4:]
        if self._size != size:
            # ToDo warning
            return

        if forceSet:
            for i in range(self._cellCount):
                self._grid[i] = grid[i]
        else:
            for i in range(self._cellCount):
                if grid[i]:
                    self._grid[i] = grid[i]

    def pack(self):
        packData = [self._size]
        packData.extend(self._grid)
        return struct.pack("i", self._size) + bytearray(self._grid)

    def getCell(self, coord):
        i = coord[1] * self._size + coord[0]
        if i < 0 or i >= self._cellCount:
            return None
        return self._grid[i]

    def setCell(self, coord, val):
        i = coord[1] * self._size + coord[0]
        if 0 <= i < self._cellCount:
            try:
                self._grid[i] = val
            except:
                pass

class Map:
    def __init__(self):

        self.saveFront = Queue.Queue()
        self._transmData = []
        self.ChangeWallToPass = {}
        self.maxChangeWallToPassKayValue = 20
        self.cellMarkRadius = (BOT_R / CELL_PX_SIZE)

        self.convertCellsTable = \
            [  # 0'/' 1'_'    2'#' 3'' 4'?' 5'X' 6'#'
                ['n', 'y', 'ys', '', 'y', 'n', 'ys'],  # 0 '/'
                ['y', 'n', 'yas', '', 'y', 'y', 'yas'],  # 1 '_'
                ['n', 'ya', 'ys', '', 'n', 'n', 'ys'],  # 2 '#'
                ['', '', '', '', '', '', ''],  # 3 ''
                ['n', 'n', 'yas', '', 'n', 'y', 'ys'],  # 4 '?'
                ['y', 'n', 'yas', '', 'n', 'n', 'ys'],  # 5 'X'
                ['n', 'ya', 'ys', '', 'n', 'n', 'ys'],  # 6 '#'
            ]
        self._chunks = {}

    def getChunkCoords(self, pos):
        return pos[0] / CHUNK_SIZE, pos[1] / CHUNK_SIZE

    def getMapCoords(self, inChunkPos, chunkKey):
        x_pos = chunkKey[0] * CHUNK_SIZE + (inChunkPos % CHUNK_SIZE)
        y_pos = chunkKey[1] * CHUNK_SIZE + (inChunkPos // CHUNK_SIZE)
        return x_pos, y_pos

    def unsearchChunk(self, pos, cellRadius):
        chunkCoords = self.getChunkCoords(pos)
        chunkQueue = Queue.Queue()
        chunkQueue.put(chunkCoords)
        size = self.getChunkSize(chunkQueue)

        self._chunks[(chunkCoords[0], chunkCoords[1])].searchState = False
        if pos[0] - cellRadius <= size[0][0] and self._chunks.get((chunkCoords[0] - 1, chunkCoords[1])):
            self._chunks[(chunkCoords[0] - 1, chunkCoords[1])].searchState = False
        if pos[0] + cellRadius >= size[0][1] and self._chunks.get((chunkCoords[0] + 1, chunkCoords[1])):
            self._chunks[(chunkCoords[0] + 1, chunkCoords[1])].searchState = False
        if pos[1] - cellRadius <= size[1][0] and self._chunks.get((chunkCoords[0], chunkCoords[1] - 1)):
            self._chunks[(chunkCoords[0], chunkCoords[1] - 1)].searchState = False
        if pos[1] + cellRadius >= size[1][1] and self._chunks.get((chunkCoords[0], chunkCoords[1] + 1)):
            self._chunks[(chunkCoords[0], chunkCoords[1] + 1)].searchState = False

    # mark in square area with side as drone diameter around cell as unknown 0b0000 '/'
    def quadMarkUnknownArea(self, pos, cellRadius, botPos):
        matrixRange = [0]
        for i in range(1, cellRadius + 1):
            matrixRange.append(i)
            matrixRange.append(-i)
        for i in range(len(matrixRange)):
            for j in range(len(matrixRange)):
                if i == 0 and j == 0:
                    continue
                self.setCell((pos[0] + matrixRange[i], pos[1] + matrixRange[j]), 0b0000, botPos)
        self.unsearchChunk(botPos, cellRadius)

    def quadSetBitNearestWall(self, pos, cellRadius):
        matrixRange = [0]
        for i in range(1, cellRadius + 1):
            matrixRange.append(i)
            matrixRange.append(-i)
        for i in range(len(matrixRange)):
            for j in range(len(matrixRange)):
                if i == 0 and j == 0:
                    continue
                setterBit = self.setBitNearestWall(self.getCell((pos[0] + matrixRange[i], pos[1] + matrixRange[j])))
                self.setBitCell((pos[0] + matrixRange[i], pos[1] + matrixRange[j]), setterBit)

    def quadUnsetBitNearestWall(self, pos, cellRadius):
        matrixRange = [0]
        for i in range(1, cellRadius + 1):
            matrixRange.append(i)
            matrixRange.append(-i)
        for i in range(len(matrixRange)):
            for j in range(len(matrixRange)):
                if i == 0 and j == 0:
                    continue
                setterBit = self.unsetBitNearestWall(self.getCell((pos[0] + matrixRange[i], pos[1] + matrixRange[j])))
                self.setBitCell((pos[0] + matrixRange[i], pos[1] + matrixRange[j]), setterBit)

    # special setter third bit of cell
    def setBitCell(self, coords, val):
        chunkPos = (coords[0] / CHUNK_SIZE, coords[1] / CHUNK_SIZE)
        chunk = self._chunks.get(chunkPos)
        if not chunk:
            chunk = Chunk(CHUNK_SIZE)
            self._chunks[chunkPos] = chunk
        inChunkPos = (coords[0] % CHUNK_SIZE, coords[1] % CHUNK_SIZE)
        chunk.setCell(inChunkPos, val)

    # bit setter
    def setCell(self, coords, val, botPos):
        chunkPos = (coords[0] / CHUNK_SIZE, coords[1] / CHUNK_SIZE)
        chunk = self._chunks.get(chunkPos)
        if not chunk:
            chunk = Chunk(CHUNK_SIZE)
            self._chunks[chunkPos] = chunk
        inChunkPos = (coords[0] % CHUNK_SIZE, coords[1] % CHUNK_SIZE)
        curCell = self.getCell(coords)

        commands = self.convertCellsTable[curCell][val]
        for command in commands:
            if command == 'n':
                return
            if command == 'y':
                if chunk.searchState:
                    chunk.searchState = False
                if 'a' in commands:
                    if self.distanceToCellLessEchoRange(coords, botPos):
                        chunk.setCell(inChunkPos, val)
                    else:
                        return
                else:
                    chunk.setCell(inChunkPos, val)
            if command == 's':
                self.quadSetBitNearestWall(coords, self.cellMarkRadius)
            if command == 'u':
                self.quadUnsetBitNearestWall(coords, self.cellMarkRadius)
            if command == 'a':
                self.quadMarkUnknownArea(coords, self.cellMarkRadius + 1, botPos)

    # bit getter
    def getCell(self, coords):
        chunkPos = (coords[0] / CHUNK_SIZE, coords[1] / CHUNK_SIZE)
        chunk = self._chunks.get(chunkPos)
        if chunk:
            inChunkPos = (coords[0] % CHUNK_SIZE, coords[1] % CHUNK_SIZE)
            return chunk.getCell(inChunkPos)
        else:
            return 0b0000

    def packChunk(self, transmData):
        dataType, chunkCoords = transmData
        chunksData = []

        chunk = self._chunks.get(chunkCoords)
        if not chunk:
            chunk = Chunk(CHUNK_SIZE)
            self._chunks[chunkCoords] = chunk

        chunksData.append(struct.pack('b', dataType) +
                          struct.pack("ii", chunkCoords[0], chunkCoords[1]) +
                          chunk.pack())
        return chunksData

    def packWaitingTime(self, data):
        dataType, waitingTimeID = data
        waitingTime, sendFromBotID, sendToBotID = waitingTimeID
        packFromBotId = ''
        for i in range(32):
            packFromBotId += struct.pack('s', str(sendFromBotID)[i])
        packToBotId = ''
        for i in range(32):
            packToBotId += struct.pack('s', str(sendToBotID)[i])

        packResult = [struct.pack('b', dataType) +
                      struct.pack("i", waitingTime) +
                      packFromBotId +
                      packToBotId]
        return packResult

    def packMatrixString(self, data):
        dataType, stringIDPos = data
        matrixString, botID, botPos, currentCharge = stringIDPos

        countOfTarget = len(matrixString)
        packMatrixString = ''
        packId = ''
        for koef in matrixString:
            if not koef:
                koef = 0.0
            packMatrixString += struct.pack('d', koef)

        for i in range(32):
            packId += struct.pack('s', str(botID)[i])

        packBotPos = struct.pack('ii', botPos[0], botPos[1])

        packCurrentCharge = struct.pack('i', currentCharge)

        packResult = [struct.pack('b', dataType) +
                      struct.pack('i', countOfTarget) +
                      packId +
                      packBotPos +
                      packCurrentCharge +
                      packMatrixString]

        return packResult

    def packTrajectory(self, data):
        dataType, trajectoryBotID = data
        trajectory = trajectoryBotID[:2]
        botID = trajectoryBotID[-1]

        packBotID = ''
        for i in range(32):
            packBotID += struct.pack('s', str(botID)[i])

        packResult = [struct.pack('b', dataType) +
                      struct.pack("ii", trajectory[0][0], trajectory[0][1]) +
                      struct.pack("ii", trajectory[1][0], trajectory[1][1]) +
                      packBotID]
        return packResult

    def updateChunks(self, update):
        pos = 1
        symbolLength = 4

        x = struct.unpack("i", update[pos: pos + symbolLength])[0]
        pos += symbolLength
        y = struct.unpack("i", update[pos: pos + symbolLength])[0]
        pos += symbolLength
        size = struct.unpack("i", update[pos: pos + symbolLength])[0]

        chunks = [((x, y), update[pos:pos + symbolLength + size * size])]
        for chunkPos, data in chunks:

            chunk = self._chunks.get(chunkPos)
            if not chunk:
                chunk = Chunk(CHUNK_SIZE)
                self._chunks[chunkPos] = chunk
                self._chunks[chunkPos].searchState = False
            chunk.update(data)

    def unpackWaitingTime(self, data):
        pos = 1
        symbolLength = 4

        waitingTime = struct.unpack("i", data[pos: pos + symbolLength])[0]
        pos += symbolLength

        sendFromBotID = ''
        for i in range(32):
            sendFromBotID += struct.unpack("s", data[pos + i: pos + 1 + i])[0]
        pos += 32

        sendToBotID = ''
        for i in range(32):
            sendToBotID += struct.unpack("s", data[pos + i: pos + 1 + i])[0]
        pos += 32
        return [waitingTime, sendFromBotID, sendToBotID]

    def unpackMatrixString(self, data):
        pos = 1
        intSymbolLength = 4
        doubleSymbolLength = 8
        botID = ''
        countOfTarget = struct.unpack("i", data[pos: pos + intSymbolLength])[0]
        pos += intSymbolLength

        for i in range(32):
            botID += struct.unpack("s", data[pos + i: pos + 1 + i])[0]
        pos += 32

        botPosX = struct.unpack("i", data[pos: pos + intSymbolLength])[0]
        pos += intSymbolLength
        botPosY = struct.unpack("i", data[pos: pos + intSymbolLength])[0]
        pos += intSymbolLength
        botPos = (botPosX, botPosY)

        currentCharge = struct.unpack("i", data[pos: pos + intSymbolLength])[0]
        pos += intSymbolLength

        matrixString = []
        for i in range(countOfTarget):
            coefficient = struct.unpack("d", data[pos: pos + doubleSymbolLength])[0]
            if coefficient == 0.0:
                coefficient = None
            matrixString.append(coefficient)
            pos += doubleSymbolLength

        return matrixString, botID, botPos, currentCharge

    def unpackTrajectory(self, data):
        pos = 1
        symbolLength = 4

        firstX = struct.unpack("i", data[pos: pos + symbolLength])[0]
        pos += symbolLength
        firstY = struct.unpack("i", data[pos: pos + symbolLength])[0]
        pos += symbolLength
        secondX = struct.unpack("i", data[pos: pos + symbolLength])[0]
        pos += symbolLength
        secondY = struct.unpack("i", data[pos: pos + symbolLength])[0]
        pos += symbolLength

        botID = ''
        for i in range(32):
            botID += struct.unpack("s", data[pos + i: pos + 1 + i])[0]
        pos += 32
        return (firstX, firstY), (secondX, secondY), botID

    def checkCollision(self, firstLine, data, botSpeed):
        secondLineID = self.unpackTrajectory(data)
        secondLine = secondLineID[:2]
        botId = secondLineID[-1]

        ax1, ay1 = firstLine[0]
        ax2, ay2 = firstLine[1]
        bx1, by1 = secondLine[0]
        bx2, by2 = secondLine[1]

        minAX = min(ax1, ax2)
        maxAX = max(ax1, ax2)
        minAY = min(ay1, ay2)
        maxAY = max(ay1, ay2)

        minBX = min(bx1, bx2)
        maxBX = max(bx1, bx2)
        minBY = min(by1, by2)
        maxBY = max(by1, by2)

        delArr = (BOT_R / CELL_PX_SIZE)
        firstRect = self.getRectCellsFromPoints((minAX - delArr, minAY - delArr), (maxAX + delArr, maxAY + delArr))
        secondRect = self.getRectCellsFromPoints((minBX - delArr, minBY - delArr), (maxBX + delArr, maxBY + delArr))

        banedCell = []
        for cell in firstRect:
            if cell in secondRect:
                banedCell.append(cell)

        firstLineLength = (abs(ax1 - ax2) ** 2 + abs(ay1 - ay2)) ** 0.5
        secondLineLength = (abs(bx1 - bx2) ** 2 + abs(by1 - by2)) ** 0.5

        if banedCell:
            if firstLineLength > secondLineLength:
                waitingTime = self.calculateWaitingTimeToAvoidCollision(firstLineLength, botSpeed)
                myWaitingTime = 'Me'
            elif firstLineLength < secondLineLength:
                if firstLineLength == 0:
                    waitingTime = self.calculateWaitingTimeToAvoidCollision(secondLineLength, botSpeed)
                    myWaitingTime = 'Me'
                else:
                    waitingTime = self.calculateWaitingTimeToAvoidCollision(secondLineLength, botSpeed)
                    myWaitingTime = 'NotMe'
            else:
                waitingTime = self.calculateWaitingTimeToAvoidCollision(secondLineLength, botSpeed)
                myWaitingTime = 'Equal'
            return banedCell, waitingTime, myWaitingTime, (ax2, ay2), botId
        return None

    def getChunksDict(self):
        return_dict = {}
        for key in self._chunks.keys():
            return_dict[key] = self._chunks[key]
        return return_dict

    def getDifferBetweenMap(self, firstMap, secondMap):
        unchangeable_symb = [0b1000, 0b1001]
        differList = {}
        for firstMapKey in firstMap.keys():
            for firstMapSymbNumb in range(len(firstMap[firstMapKey])):
                firstMapSymb =  firstMap[firstMapKey][firstMapSymbNumb]
                if firstMapKey in secondMap.keys():
                    secondMapSymb = secondMap[firstMapKey][firstMapSymbNumb]
                    if not firstMapSymb in unchangeable_symb and not secondMapSymb in unchangeable_symb:
                        if firstMapSymb != secondMapSymb:
                            differList[self.getMapCoords(firstMapSymbNumb, firstMapKey)] = firstMapSymb
        return differList

    def updateMapWithDifferUpdate(self, differ, otherBotPos, self_pos):
        updateIsCorrect, correctCellsList = self.getCorrectCellsFromUpdate(differ, otherBotPos, self_pos)
        for cell in correctCellsList.keys():
            self.setBitCell(cell, correctCellsList[cell])
        return updateIsCorrect

    def getCorrectCellsFromUpdate(self, differ, otherBotPos, self_pos):
        correctCellsList = {}
        updateIsCorrect = True
        for cell in differ.keys():
            neighborsCells = self.cellsAroundCell(cell)
            if otherBotPos in neighborsCells or (differ[cell] == 0b0000 and self_pos not in neighborsCells):
                correctCellsList[cell] = differ[cell]
            else:
                updateIsCorrect = False
                if self_pos not in neighborsCells:
                    # mark unreached point for all bots as unknown
                    correctCellsList[cell] = 0b0000
                else:
                    correctCellsList[cell] = self.getCell(cell)
        return updateIsCorrect, correctCellsList

    def updateChunksFromDict(self, chunks_dict):
        unchangeable_symb = [0b1000, 0b1001]

        for key in chunks_dict.keys():
            chunk_grid_string = []
            chunk = self._chunks.get(key)
            if not chunk:
                chunk = Chunk(CHUNK_SIZE)
                self._chunks[key] = chunk

            for symbNumb in range(len(chunks_dict[key])):
                symb = chunks_dict[key][symbNumb]

                if symb in unchangeable_symb:
                    symb = 0b0001
                if self._chunks[key]._grid[symbNumb] in unchangeable_symb:
                    symb = self._chunks[key]._grid[symbNumb]
                chunk_grid_string.append(symb)
            self._chunks[key]._grid = tuple(chunk_grid_string)


    # convert map from self._chunk to readable map
    def printToText(self):
        keys = self._chunks.keys()
        if not keys:
            return
        minX, minY = keys[0]
        maxX, maxY = keys[0]

        for key in keys:
            minX = min(key[0], minX)
            minY = min(key[1], minY)

            maxX = max(key[0], maxX)
            maxY = max(key[1], maxY)
        minX *= CHUNK_SIZE
        minY *= CHUNK_SIZE

        maxX = (maxX + 1) * CHUNK_SIZE
        maxY = (maxY + 1) * CHUNK_SIZE

        data = []

        for y in range(minY, maxY):
            data.append(['/' for x in range(minX, maxX)])
            for x in range(minX, maxX):
                val = self.getCell((x, y))
                if val == 0b0000:
                    data[-1][x - minX] = '/'
                elif val == 0b0100:
                    data[-1][x - minX] = '?'
                elif val == 0b0001:
                    data[-1][x - minX] = ' '
                elif val == 0b0101:
                    data[-1][x - minX] = 'X'
                elif val == 0b0010 or val == 0b0110:
                    data[-1][x - minX] = '#'
                elif val == 0b1000:
                    data[-1][x-minX] = '$'
                elif val == 0b1001:
                    data[-1][x-minX] = 'O'

        return data

    def getChunksFromFile(self, fileName):
        f = open(fileName, "r")
        fileContent = f.read().split('\n')
        if fileContent[-1] == '':
            fileContent.remove('')
        countOfLine = len(fileContent)
        countOfSymbolInLine = len(fileContent[0])
        for lineNumb in range(countOfLine):
            for symbolNumb in range(countOfSymbolInLine):
                symbol = fileContent[lineNumb][symbolNumb]
                self.setBitCell((symbolNumb, lineNumb), SYMBOL_TO_BIT_DICT[symbol])
        f.close()

        return self._chunks

    def getBotTargetCoords(self):
        target_list = []
        bot_coord = None
        chunkGrid = self.printToText()
        for lineNumb in range(len(chunkGrid)):
            for symbNumb in range(len(chunkGrid[lineNumb])):
                if chunkGrid[lineNumb][symbNumb] == '$':
                    target_list.append((symbNumb, lineNumb))
                if chunkGrid[lineNumb][symbNumb] == 'O':
                    bot_coord = (symbNumb, lineNumb)
        if bot_coord is None:
            bot_coord = (0, 0)
        return target_list, bot_coord

    def getChunkGridFormFile(self, fileName):
        mapChunks = self.getChunksFromFile(fileName)
        chunksGrid = {} #{chunk coords: chunk grid}

        for key in mapChunks.keys():
            chunksGrid[key] = str(mapChunks[key]._grid)
        return chunksGrid

    def getChunkSize(self, chunkFront):
        chunkFrontCopy = self.queueCopy(chunkFront)
        chunk = chunkFrontCopy.get()
        minX, minY = chunk
        maxX, maxY = chunk

        while not chunkFrontCopy.empty():
            chunk = chunkFrontCopy.get()
            minX = min(chunk[0], minX)
            minY = min(chunk[1], minY)
            maxX = max(chunk[0], maxX)
            maxY = max(chunk[1], maxY)

        minX *= CHUNK_SIZE
        minY *= CHUNK_SIZE
        maxX = (maxX + 1) * CHUNK_SIZE
        maxY = (maxY + 1) * CHUNK_SIZE
        return [(minX, maxX), (minY, maxY)]

    # append to chunk queue unsearch chunk
    def appendChunk(self, chunkFront):
        chunkMas = []
        chunkFrontCopy = self.queueCopy(chunkFront)
        returnChunks = []
        while not chunkFrontCopy.empty():

            newChunk = chunkFrontCopy.get()
            chunkMas.append(newChunk)
            newChunkX, newChunkY = newChunk

            leftChunk = (newChunkX - 1, newChunkY)
            rightChunk = (newChunkX + 1, newChunkY)
            topChunk = (newChunkX, newChunkY - 1)
            bottomChunk = (newChunkX, newChunkY + 1)
            neighborChunksList = [leftChunk, rightChunk, topChunk, bottomChunk]

            for chunk in neighborChunksList:
                if chunk in self._chunks.keys():
                    if not self._chunks[chunk].searchState:
                        returnChunks.append(chunk)
                        return chunk
                    elif chunk not in chunkMas:
                        chunkFrontCopy.put(chunk)

    def optimizePath(self, path):
        if len(path) <= 2:
            return path
        angleCells = [path[0]]
        previousCell = path[0]
        prevMotionDirection = self.getMotionDirection(path[0], path[1])

        for i in range(1, len(path)):
            motionDirection = self.getMotionDirection(previousCell, path[i])
            if self.directionIsChange(prevMotionDirection, motionDirection):
                angleCells.append(path[i - 1])
                prevMotionDirection = motionDirection
            previousCell = path[i]
        angleCells.append(path[len(path) - 1])
        return angleCells

    def getTransmitData(self):
        data = self._transmData.pop(0)
        if data[0] == 0:
            return self.packChunk(data)
        if data[0] == 1:
            return self.packTrajectory(data)
        if data[0] == 2:
            return self.packMatrixString(data)
        if data[0] == 3:
            return self.packWaitingTime(data)

    def addTransmissionData(self, dataType, data):
        self._transmData.append((dataType, data))

    def checkTransmissionData(self):
        if self._transmData:
            return True
        return False

    def AStarPathForAllTarget(self, botPosition, goals, banedCell):
        distanceToGoal = {}
        for goalID in goals.keys():
            distanceToGoal[goalID] = self.AStar(botPosition, goals[goalID], banedCell)

        pathToGoal = {}
        for goalID in goals.keys():
            if distanceToGoal[goalID]:
                pathToGoal[goalID] = self.getPathFromDistance(distanceToGoal[goalID], goals[goalID], banedCell)
            else:
                pathToGoal[goalID] = None

        optimizePathToGoal = {}
        for goalID in goals.keys():
            if pathToGoal[goalID]:
                optimizePathToGoal[goalID] = self.optimizePath(pathToGoal[goalID])
            else:
                optimizePathToGoal[goalID] = None
        return optimizePathToGoal

    def AStar(self, botPosition, goal, banedCells):
        if goal in banedCells:
            banedCells.remove(goal)
        if botPosition in banedCells:
            banedCells.remove(botPosition)
        frontier = [(botPosition, 0)]
        costSoFar = {botPosition: 0}
        distance = {botPosition: 0}
        while frontier:
            current = self.getMinPriority(frontier)
            frontier.remove(current)
            currentPos, currentPriority = current
            if currentPos == goal:
                return distance
            for next in self.getNeighbors(currentPos, (), True, banedCells):
                newCost = costSoFar[currentPos]
                if next not in costSoFar.keys() or newCost < costSoFar[next]:
                    costSoFar[next] = newCost + 1
                    priority = newCost + self.heuristic(goal, next)
                    if (next, priority) not in frontier:
                        frontier.append((next, priority))
                    distance[next] = costSoFar[next]

        return None

    def startChunkWave(self, botPosition, banedCells):
        if botPosition in banedCells:
            return None
        firstChunkPos = (botPosition[0] / CHUNK_SIZE, botPosition[1] / CHUNK_SIZE)
        chunkFrontier = Queue.Queue()
        chunkFrontier.put(firstChunkPos)
        chunkSize = self.getChunkSize(chunkFrontier)
        frontier = Queue.Queue()
        frontier.put(botPosition)
        distance = {botPosition: 0}

        while True:
            while not frontier.empty():
                current = frontier.get()
                for next in self.getNeighbors(current, chunkSize, False, banedCells):
                    next = tuple(next)
                    if next not in distance.keys():
                        nextCell = self.getCell(next)
                        if nextCell == 0b0000 or nextCell == 0b0100:
                            distance[next] = 1 + distance[current]
                            self.saveFront = Queue.Queue()
                            return [next, distance]
                        frontier.put(next)
                        distance[next] = 1 + distance[current]

            self._chunks[chunkFrontier.queue[-1]].searchState = True
            self.addTransmissionData(0, chunkFrontier.queue[-1])
            appendResult = self.appendChunk(chunkFrontier)

            if appendResult is None:
                self.saveFront = Queue.Queue()
                self.addTransmissionData(0, chunkFrontier.queue[-1])
                if self.getCell(botPosition) != 0b0001:
                    self._chunks[chunkFrontier.queue[-1]].searchState = False
                return None

            frontier = self.queueCopy(self.saveFront)
            chunkFrontier.put(appendResult)
            chunkSize = self.getChunkSize(chunkFrontier)

    # check that wall is near
    def wallIsNear(self, pos):
        wallCellsList = [0b0101, 0b0010, 0b0110]
        if self.getCell(pos) in wallCellsList:
            return True
        return False

    def cellIsPassable(self, pos):
        if self.getCell(pos) == 0b0001 or self.getCell(pos) == 0b1000:
            return True
        return False

    # find nearest to pos 0b0001 - ' ' cell
    def findNearestPassableCell(self, pos, banedCell, returnCell):
        currentRadius = 1
        queueChunk = Queue.Queue()
        queueChunk.put((pos[0] / CHUNK_SIZE, pos[1] / CHUNK_SIZE))
        while True:
            for j in range(1, currentRadius + 1):
                neighborCellsList = self.getDiagonalNeighborsList(pos, currentRadius, j)
                for cell in neighborCellsList:
                    if self.getCell(cell) == 0b0001 and \
                            cell not in banedCell:
                        distanceToPassableCell = self.AStar(pos, cell, banedCell)
                        if distanceToPassableCell:
                            pathToPassableCell = self.getPathFromDistance(distanceToPassableCell, cell, banedCell)
                            return pathToPassableCell
                        elif returnCell:
                            return [cell]
            currentRadius += 1
            if currentRadius > CHUNK_SIZE:
                return None

    def getPathFromDistance(self, distance, target, banedCells):
        path = [target]
        current = target

        while True:
            leftElem = (current[0] - 1, current[1])
            rightElem = (current[0] + 1, current[1])
            upElem = (current[0], current[1] - 1)
            downElem = (current[0], current[1] + 1)
            neighborElem = [leftElem, rightElem, upElem, downElem]
            if distance[current] == 0:
                path.pop(0)
                optimize_path = self.optimizePath(path)
                return optimize_path

            for elem in neighborElem:
                if elem in distance.keys():
                    if distance[elem] + 1 == distance[current] and elem not in banedCells:
                        path.insert(0, elem)
                        current = elem
                        break

    def cellIsPassableForChunkWave(self, cell, banedCells, chunkSize):
        if not self.wallIsNear(cell) and self.checkCellInsideChunk(chunkSize, cell) and (cell not in banedCells):
            return True
        return False

    def cellIsPassableForAStarWave(self, cell, banedCells):
        if self.cellIsPassable(cell) and (cell not in banedCells):
            return True
        return False

    def getNeighbors(self, curCell, chunkSize, AStarWave, banedCells):
        neighborsMas = []
        leftCell = (curCell[0] - 1, curCell[1])
        rightCell = (curCell[0] + 1, curCell[1])
        topCell = (curCell[0], curCell[1] - 1)
        bottomCell = (curCell[0], curCell[1] + 1)
        neighborCellsList = [leftCell, rightCell, topCell, bottomCell]

        for neighborCell in neighborCellsList:
            if AStarWave and self.cellIsPassableForAStarWave(neighborCell, banedCells) or \
                    not AStarWave and self.cellIsPassableForChunkWave(neighborCell, banedCells, chunkSize):
                #self.createNeighborChunks(neighborCell) remove to correct issue with
                neighborsMas.append(neighborCell)

            elif not AStarWave and curCell not in self.saveFront.queue:
                self.saveFront.put(curCell)

        return neighborsMas

    def createNeighborChunks(self, cell):
        chunkPos = (cell[0] / CHUNK_SIZE, cell[1] / CHUNK_SIZE)
        leftChunk = (chunkPos[0] - 1, chunkPos[1])
        rightChunk = (chunkPos[0] + 1, chunkPos[1])
        topChunk = (chunkPos[0], chunkPos[1] - 1)
        bottomChunk = (chunkPos[0], chunkPos[1] + 1)
        neighborChunkList = [leftChunk, rightChunk, topChunk, bottomChunk]

        for chunkPos in neighborChunkList:
            chunk = self._chunks.get(chunkPos)
            if not chunk:
                chunk = Chunk(CHUNK_SIZE)
                self._chunks[chunkPos] = chunk

    def getChunksGrid(self):
        chunks_grid_dict = {}
        for key in self._chunks.keys():
            chunks_grid_dict[key] = []
            for symb in self._chunks[key]._grid:
                chunks_grid_dict[key].append(symb)
        return chunks_grid_dict


    # set third bit as 1
    @staticmethod
    def setBitNearestWall(val):
        return val | 0b0100

    # set third bit as 0
    @staticmethod
    def unsetBitNearestWall(val):
        return val & 0b1011

    @staticmethod
    def getDiagonalNeighborsList(cellCoordinate, radius, value):
        leftCell = (cellCoordinate[0] + radius - value, cellCoordinate[1] - value)
        rightCell = (cellCoordinate[0] - value, cellCoordinate[1] - radius + value)
        topCell = (cellCoordinate[0] - radius + value, cellCoordinate[1] + value)
        bottomCell = (cellCoordinate[0] + value, cellCoordinate[1] + radius - value)
        neighborCellsList = [leftCell, rightCell, topCell, bottomCell]
        return neighborCellsList

    @staticmethod
    def queueCopy(q):
        qCopy = Queue.Queue()
        for i in q.queue:
            qCopy.put(i)
        return qCopy

    @staticmethod
    # check that cell place inside chunk
    def checkCellInsideChunk(chunkSize, pos):
        minX, maxX = chunkSize[0]
        minY, maxY = chunkSize[1]
        if maxX > pos[0] > minX and maxY > pos[1] > minY:
            return True
        return False

    @staticmethod
    # checking that the distance to the cell is less than the EchoRange
    def distanceToCellLessEchoRange(cellCoords, botPos):
        botX = botPos[0] * CELL_PX_SIZE
        botY = botPos[1] * CELL_PX_SIZE
        cellX = cellCoords[0] * CELL_PX_SIZE
        cellY = cellCoords[1] * CELL_PX_SIZE
        distance = (abs(botX - cellX) ** 2 + abs(botY - cellY) ** 2) ** 0.5

        return distance < BOT_ECHO_RANGE * 0.9

    @staticmethod
    def cellsAroundCell(cell):
        cellX, cellY = cell
        delArr = (BOT_R / CELL_PX_SIZE) + 1
        resultCells = []
        for i in range(cellX - delArr, cellX + delArr + 1):
            for j in range(cellY - delArr, cellY + delArr + 1):
                resultCells.append((i, j))
        return resultCells

    @staticmethod
    def calculateWaitingTimeToAvoidCollision(collisionBotPathLength, botSpeed):
        return (collisionBotPathLength * CHUNK_SIZE) / botSpeed

    @staticmethod
    def directionIsChange(firstMotionDir, secondMotionDir):
        if firstMotionDir != secondMotionDir:
            return True
        return False

    @staticmethod
    def getMotionDirection(firstCell, secondCell):
        firstCellX, firstCellY = firstCell
        secondCellX, secondCellY = secondCell

        if (firstCellX == secondCellX) and (firstCellY == secondCellY - 1):
            return 'Down'
        if (firstCellX == secondCellX) and (firstCellY == secondCellY + 1):
            return 'Up'
        if (firstCellX == secondCellX - 1) and (firstCellY == secondCellY):
            return 'Left'
        if (firstCellX == secondCellX + 1) and (firstCellY == secondCellY):
            return 'Right'

    @staticmethod
    def getRectCellsFromPoints(firstPoint, secondPoint):
        firstPointX, firstPointY = firstPoint
        secondPointX, secondPointY = secondPoint
        maxX = max(firstPointX, secondPointX)
        minX = min(firstPointX, secondPointX)
        maxY = max(firstPointY, secondPointY)
        minY = min(firstPointY, secondPointY)

        cellsList = []
        for i in range(minX, maxX + 1):
            for j in range(minY, maxY + 1):
                cellsList.append((i, j))
        return cellsList

    @staticmethod
    def heuristic(firstCell, secondCell):
        x1, y1 = firstCell
        x2, y2 = secondCell
        return int((abs(x2 - x1) ** 2 + abs(y2 - y1) ** 2) ** 0.5)

    @staticmethod
    def getMinPriority(frontier):
        minPrior = frontier[0][1]
        minElem = frontier[0][0]
        for el in frontier:
            if el[1] < minPrior:
                minPrior = el[1]
                minElem = el[0]
        return minElem, minPrior

