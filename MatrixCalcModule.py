from map_storage import CELL_PX_SIZE, CHUNK_SIZE


class MatrixCalcModule:

    def __init__(self):
        self.IDs = []
        self.targetIDs = []

        self.botsPosition = {}

        self.targetsPosition = {}

        self.countOfDrones = 0
        self.countOfTarget = 0
        self.selfCharge = 0
        self.droneIDCharge = {}

        self.dronePathTime = {}
        self.selfMatrixString = []
        self.botIDMatrixString = {}
        self.matrixCoefficient = []
        self.targetForDrone = {}

        self.droneTargetPathTimes = {}
        self.selfTarget = None

    def getSelfMatrixString(self):
        return self.selfMatrixString

    def setDroneIds(self, IDs):
        for ID in IDs:
            if ID not in self.IDs:
                self.IDs.append(ID)
        self.IDs.sort()

    def setTargetIDs(self, IDs):
        for ID in IDs:
            if ID not in self.targetIDs:
                self.targetIDs.append(ID)
        self.targetIDs.sort()

    def setTargetPos(self, ID, pos):
        #self.targetsPosition[ID] = (pos[0] / CELL_PX_SIZE, pos[1] / CELL_PX_SIZE)
        self.targetsPosition[ID] = (pos[0], pos[1])

    def setCountOdDrone(self):
        self.countOfDrones = len(self.IDs)

    def setCountOfTarget(self):
        self.countOfTarget = len(self.targetIDs)

    def setDroneCharge(self, charge):
        self.selfCharge = charge

    def setBotCurrentCharge(self, botID, currentCharge):
        self.droneIDCharge[botID] = currentCharge

    def appendMatrixString(self, matrixString, botID):
        self.botIDMatrixString[botID] = matrixString

    def appendBotPosition(self, botID, botPos):
        self.botsPosition[botID] = botPos

    def appendMatrixStrings(self):
        for ID in self.IDs:
            koeffString = self.botIDMatrixString[ID]
            self.matrixCoefficient.append([])
            for koef in koeffString:
                self.matrixCoefficient[-1].append(koef)

    def initSelfMatrixValues(self, droneIDs, selfID, targetPos, droneCharge):
        self.dronePathTime = {}
        self.selfMatrixString = []
        self.botIDMatrixString = {}
        self.matrixCoefficient = []
        self.targetForDrone = {}

        self.setDroneIds(droneIDs)

        """ 
        self.setTargetIDs(targetPos.keys())
        for ID in self.targetIDs:
            self.setTargetPos(ID, targetPos[ID])
        """
        self.setTargetIDs(targetPos)
        for ID in self.targetIDs:
            self.setTargetPos(ID, ID)

        self.setCountOdDrone()
        self.setCountOfTarget()

        if self.countOfTarget == 0:
            return None
        self.setDroneCharge(droneCharge)
        self.setBotCurrentCharge(selfID, droneCharge)
        return True

    def getWaitingTime(self):
        droneTargetPathTime = {}
        resultWaitingTime = {}
        for droneTarget in self.targetForDrone.items():
            drone, target = droneTarget
            droneTargetPathTime[drone] = self.droneTargetPathTimes[(drone, target)]

        drones = droneTargetPathTime.keys()
        times = droneTargetPathTime.values()

        minTime = min(times)
        minTimeIndex = times.index(minTime)
        previousPathTime = 0
        previousSetTime = 0
        for i in range(len(drones)):
            resultWaitingTime[drones[minTimeIndex]] = previousPathTime + previousSetTime

            previousSetTime = previousPathTime + previousSetTime
            previousPathTime = times[minTimeIndex]

            times[minTimeIndex] = 1000000000
            minTime = min(times)
            minTimeIndex = times.index(minTime)

        return resultWaitingTime

    def setDroneTargetsPathTimes(self, droneTargetsPaths, botSpeed, botVelSpeed):
        for targetID in self.targetIDs:
            self.dronePathTime[targetID] = self.calculatePathTime(droneTargetsPaths[targetID], botSpeed, botVelSpeed)

    def calculatePathTime(self, droneTargetsPath, botSpeed, botVelSpeed):
        if not droneTargetsPath:
            return None

        pathTime = 0
        anglesCount = len(droneTargetsPath)
        pathTime += (self.getPathTimeMovementSegment(droneTargetsPath) * CHUNK_SIZE) / botSpeed
        pathTime += (anglesCount * 90) / abs(botVelSpeed)

        return pathTime

    def getPathTimeMovementSegment(self, droneTargetsPath):
        distance = 0
        previousSegment = droneTargetsPath[0]

        for segment in droneTargetsPath:
            distance += ((segment[0] - previousSegment[0]) ** 2 + (segment[1] - previousSegment[1]) ** 2) ** 0.5
            previousSegment = segment
        return distance

    def selfStringMatrixCalculation(self, ID):
        if self.selfMatrixString:
            return
        for targetNumber in self.targetIDs:

            if self.dronePathTime[targetNumber] == 0:
                self.dronePathTime[targetNumber] = 0.01
            if not self.dronePathTime[targetNumber]:
                self.selfMatrixString.append(None)
            else:
                coefficient = self.selfCharge / self.dronePathTime[targetNumber]
                self.selfMatrixString.append(float("{0:.3f}".format(coefficient)))
        self.appendMatrixString(self.selfMatrixString, ID)

    def convertMatrix(self):
        for stringNumber in range(len(self.matrixCoefficient)):
            for coefNubmer in range(len(self.matrixCoefficient[stringNumber])):
                if self.matrixCoefficient[stringNumber][coefNubmer] is None:
                    self.matrixCoefficient[stringNumber][coefNubmer] = 0

        for stringNumber in range(len(self.matrixCoefficient)):
            if len(self.matrixCoefficient[stringNumber]) < self.countOfTarget:
                for i in range(self.countOfTarget - len(self.matrixCoefficient[stringNumber])):
                    self.matrixCoefficient[stringNumber].append(0)

    def checkCountOfDroneTarget(self):
        self.setCountOdDrone()
        self.setCountOfTarget()
        if len(self.botIDMatrixString.values()[0]) == self.countOfTarget and \
                len(self.botIDMatrixString) == self.countOfDrones:
            self.appendMatrixStrings()
            self.convertMatrix()
            return True
        return False

    def matrixCalc(self):
        while self.matrixCoefficient != [[0] * self.countOfTarget] * self.countOfDrones:
            for i in range(self.countOfDrones):
                if self.matrixCoefficient[i] == [0] * self.countOfTarget:
                    continue
                selectDrone = i
                selectDroneTargetCoeff = max(self.matrixCoefficient[i])
                selectTarget = self.matrixCoefficient[i].index(selectDroneTargetCoeff)
                self.checkTarget(selectDroneTargetCoeff, selectTarget, selectDrone)

    def checkTarget(self, droneTargetCoeff, target, drone):
        for j in range(self.countOfDrones):
            if droneTargetCoeff < self.matrixCoefficient[j][target]:
                break
            if j == self.countOfDrones - 1:
                droneID = self.IDs[drone]
                if droneTargetCoeff != 0 or droneTargetCoeff is not None:
                    self.droneTargetPathTimes[(droneID, self.targetIDs[target])] = \
                        float("{0:.3f}".format(self.droneIDCharge[droneID] / self.matrixCoefficient[drone][target]))
                    self.appendTargetForDrone(drone, target)

                else:
                    self.targetForDrone[self.IDs[drone]] = None

    def appendTargetForDrone(self, selectDrone, selectTargetIndex):
        self.targetForDrone[self.IDs[selectDrone]] = self.targetIDs[selectTargetIndex]
        self.matrixCoefficient[selectDrone] = [0] * self.countOfTarget
        for i in range(self.countOfDrones):
            self.matrixCoefficient[i][selectTargetIndex] = 0

    def printTargetForDrone(self):
        printStrings = ''
        for drone in self.targetForDrone:
            printStrings += 'For drone %s target %s \n' % (drone, self.targetForDrone[drone])
        print printStrings

    def printMatrixCoeff(self):
        for col in self.matrixCoefficient:
            print (col)

    def getSelfTarget(self, ID):
        return self.targetForDrone[ID]

