import simpy
import random
from enum import Enum
from datetime import date, datetime, timedelta

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

cred = credentials.Certificate("./factorysim-20ceb-firebase-adminsdk-mf3wo-4e4593dd24.json")

app = firebase_admin.initialize_app(cred)

db = firestore.client()

SEED = 123
random.seed(SEED)

class Debug(Enum):
    DEBUG = 0
    INFO = 1
    WARN = 2
    ERROR = 3
    FATAL = 4
    
class WrkStationStatus(Enum):
    START = 1
    IDLE = 2
    PRODUCING = 3
    RESTOCK = 4
    DOWN = 5
    STOP = 6
    
    def __str__(self):
        return str(self.name)
    
class ProductStatus(Enum):
    ORDERED = 1
    PRODUCING = 2
    DONE = 3
    FAIL = 4
    ABORT = 5
    INCOMPLETE = 6
    
    def __str__(self):
        return str(self.name)

class FactoryStatus(Enum):
    OPEN = 1
    CLOSED = 2
    SHUTDOWN = 3
    
    def __str__(self):
        return str(self.name)
    
TICKS_PER_DAY = 100 # Number of ticks that represent a day of production 
CLOSE_RATE = 0.01   # Probability of having a catastrophic accident and close that day
REJECT_RATE = 0.05  # Probability of rejecting a product at the end of the process
MAX_RAW_BIN = 25    # The max number of items each station will have at any given time
RESTOCK_UNITS = 3   # Number of restock units that the factory will have
RESTOCK_TIME = 2    # The average time units it takes the bus boy to restock a station
FIX_TIME = 3        # The average time for fixing the station
WORK_TIME = 4       # The average working time for the stations
WRK_STATIONS = 6   # Number of work stations in the factory
WRK_STATION_RATES = [0.2,0.1,0.15,0.05,0.07,0.1]    # Declared error rate of work stations
DEBUG_LEVEL = Debug.ERROR
       
def debugLog(level: Debug, msg: str, extra: str = "") -> None:
    if(level.value >= DEBUG_LEVEL.value):
        print(msg + (": " + extra if extra != "" else extra))

class Factory(object):
    pass

class Product(object):
    def __init__(self, id: int, env: simpy.Environment, factory: Factory) -> None:
        self._id = id
        self._factory = factory
        self._env = env
        self._currentStation = -1
        self._wrkStat = [False] * WRK_STATIONS
        self._wrkStatTime = [0] * WRK_STATIONS
        self._startClock = 0
        self._endClock = 0
        self._totalWks = {}
        self._totalWksDay = {self._factory._day: {}}
        self._wksTimes = {}
        self._totalTimeWks = {}
        self._totalTimeWksDay = {self._factory._day: {}}
        self._wksTimeSeries = {}
        self._wksTimeSeriesDay = {self._factory._day: {}}
        self._totalStatus = {ProductStatus.ORDERED : 0, ProductStatus.PRODUCING : 0, ProductStatus.DONE : 0, ProductStatus.FAIL : 0, ProductStatus.ABORT : 0, ProductStatus.INCOMPLETE : 0}
        self._totalStatusDay = {self._factory._day: {ProductStatus.ORDERED : 0, ProductStatus.PRODUCING : 0, ProductStatus.DONE : 0, ProductStatus.FAIL : 0, ProductStatus.ABORT : 0, ProductStatus.INCOMPLETE : 0}}
        self._statusTimes = {ProductStatus.ORDERED : 0, ProductStatus.PRODUCING : {}, ProductStatus.DONE : 0, ProductStatus.FAIL : 0, ProductStatus.ABORT : 0, ProductStatus.INCOMPLETE : 0}
        self._totalTimeStatus = {ProductStatus.ORDERED : 0, ProductStatus.PRODUCING : 0, ProductStatus.DONE : 0, ProductStatus.FAIL : 0, ProductStatus.ABORT : 0, ProductStatus.INCOMPLETE : 0}
        self._totalTimeStatusDay = {self._factory._day : { ProductStatus.ORDERED : 0, ProductStatus.PRODUCING : 0, ProductStatus.DONE : 0, ProductStatus.FAIL : 0, ProductStatus.ABORT : 0, ProductStatus.INCOMPLETE : 0 } }
        self._statusTimeSeries = {ProductStatus.ORDERED : [], ProductStatus.PRODUCING : [], ProductStatus.DONE : [], ProductStatus.FAIL : [], ProductStatus.ABORT : [], ProductStatus.INCOMPLETE : []}
        self._statusTimeSeriesDay = {self._factory._day : {ProductStatus.ORDERED : 0, ProductStatus.PRODUCING : {}, ProductStatus.DONE : 0, ProductStatus.FAIL : 0, ProductStatus.ABORT : 0, ProductStatus.INCOMPLETE : 0}}
        self._status = ProductStatus.ORDERED
        self._totalStatus[self._status] += 1
        self._totalStatusDay[self._factory._day][self._status] +=1
        self._statusTimes[self._status] = self._factory._env.now

    @property
    def status(self) -> ProductStatus:
        return self._status
    
    @status.setter
    def status(self, value: ProductStatus) -> None:
        self._status = value
        if(self._status == ProductStatus.PRODUCING and self._startClock == 0):
            self._startClock = self._env.now
            debugLog(Debug.DEBUG, 'The product %06d started production at %.2f' % (self._id, self._startClock))
        elif(self._status == ProductStatus.DONE or self._status == ProductStatus.FAIL or self._status == ProductStatus.ABORT):
            self._endClock = self._env.now
            debugLog(Debug.DEBUG, 'The product %06d finished production at %.2f' % (self._id, self._endClock), str(self._status))
        
    @property
    def processBy(self) -> int:
        return self._currentStation
    
    @processBy.setter
    def processBy(self, value: int) -> None:
        if self._currentStation != -1 and self._currentStation in self._wksTimes:
            self._wksTimes[self._currentStation].update({"final": self._factory._env.now})
        self._currentStation = value
        self._wrkStat[value] = True
        self._wksTimes[value] = {"initial": self._factory._env.now}
        if value not in self._totalWks:
            self._totalWks[value] = 0
        self._totalWks[value] += 1
        if self._factory._day in self._totalWksDay:
            if value not in self._totalWksDay[self._factory._day]:
                self._totalWksDay[self._factory._day][value] = 0
            self._totalWksDay[self._factory._day][value] += 1
        self._wrkStatTime[value] = self._env.now
        if(self._currentStation == 0):
            self.status = ProductStatus.PRODUCING
            self._totalStatus[self._status] += 1
            self._totalStatusDay[self._factory._day][self._status] +=1
            self._statusTimes[self._status]["initial"] = self._factory._env.now
        debugLog(Debug.DEBUG, 'The product %06d received at workstation %02d at %.2f' % (self._id, (self._currentStation+1), self._wrkStatTime[value]))
        
    @property
    def isDone(self) -> bool:
        return all(self._wrkStat) and not self.isAborted
    
    @property
    def isAborted(self) -> bool:
        return self.status == ProductStatus.ABORT
    
    @property
    def nextStation(self) -> int:
        """Returns the next workstation that the product still has to visit

        Returns:
            int: The index of the next missing workstation
        """
        return next((i for i,v in enumerate(self._wrkStat) if not v), None)
    
    @property
    def prodTime(self) -> float:
        if(self._startClock == 0):
            return self._startClock
        elif(self._endClock == 0):
            return self._env.now - self._startClock
        return self._endClock - self._startClock
    
    def wasProccessedBy(self, id: int) -> bool:
        return self._wrkStat[id]
    
    def stopProduction(self, time: float) -> None:
        if self._status == ProductStatus.PRODUCING:
            self._statusTimes[self._status]["final"] = self._factory._env.now
        self._status = ProductStatus.INCOMPLETE
        self._totalStatus[self._status] += 1
        self._totalStatusDay[self._factory._day][self._status] +=1
        self._statusTimes[self._status] = self._factory._env.now
        self._endClock = time


class Workstation(object):
    def __init__(self, env: simpy.Environment, busBoy: simpy.Resource, id: int, errRate: float, factory: Factory) -> None:
        self._id = id
        self._env = env
        self._busBoy = busBoy
        self._errRate = errRate
        self._binItems = MAX_RAW_BIN
        self._product = None
        self._unit = simpy.Resource(self._env)
        self._action = None
        self._factory = factory
        self._totalProducts = []
        self._totalProductsDays = {self._factory._day : []}
        self._productTimes = {}
        self._productTimeSeries = {}
        self._productTimeSeriesDay = {self._factory._day : {}}
        self._totalProductTime = {}
        self._totalProductTimeDay = {self._factory._day : {}}
        self._totalStatusState = {WrkStationStatus.START : 0, WrkStationStatus.IDLE : 0, WrkStationStatus.PRODUCING : 0, WrkStationStatus.RESTOCK : 0, WrkStationStatus.DOWN : 0, WrkStationStatus.STOP: 0}
        self._totalStatusStateDay = {self._factory._day : {WrkStationStatus.START : 0, WrkStationStatus.IDLE : 0, WrkStationStatus.PRODUCING : 0, WrkStationStatus.RESTOCK : 0, WrkStationStatus.DOWN : 0, WrkStationStatus.STOP: 0}}
        self._totalStatusTimes = {WrkStationStatus.START : [], WrkStationStatus.IDLE : [], WrkStationStatus.PRODUCING : [], WrkStationStatus.RESTOCK : [], WrkStationStatus.DOWN : [], WrkStationStatus.STOP: []}
        self._statusTimeSeries = {}
        self._statusTimeSeriesDay = {self._factory._day : {}}
        self._totalStatus = {WrkStationStatus.START : 0, WrkStationStatus.IDLE : 0, WrkStationStatus.PRODUCING : 0, WrkStationStatus.RESTOCK : 0, WrkStationStatus.DOWN : 0, WrkStationStatus.STOP: 0}
        self._totalStatusDay = {self._factory._day : {WrkStationStatus.START : 0, WrkStationStatus.IDLE : 0, WrkStationStatus.PRODUCING : 0, WrkStationStatus.RESTOCK : 0, WrkStationStatus.DOWN : 0, WrkStationStatus.STOP: 0}}
        self._status = None
        self.setStatus(WrkStationStatus.START)

    @property
    def id(self) -> simpy.Process:
        return self._id + 1
    
    @property
    def action(self) -> simpy.Process:
        return self._action
    
    @action.setter
    def action(self, value) -> None:
        self._action = value
        
    @property
    def unit(self) -> simpy.Resource:
        return self._unit
    
    @property
    def product(self) -> Product:
        return self._product
    
    @product.setter
    def product(self, value: Product) -> None:
        self._product = value
        self._product.processBy = self._id

    def setStatus(self, value: WrkStationStatus) -> None:
        if (self._status is not None and len(self._totalStatusTimes[self._status]) == 0) or (self._status is not None and round(self._totalStatusTimes[self._status][-1], 2) != round(self._factory._env.now,2)):
            self._totalStatusTimes[self._status].append(self._factory._env.now)
        elif self._status is not None and len(self._totalStatusTimes[self._status]) > 0 and round(self._totalStatusTimes[self._status][-1], 2) == round(self._factory._env.now,2) :
                self._totalStatusTimes[self._status].pop(-1)
        self._totalStatusTimes[value].append(self._factory._env.now)
        self._status = value
        
    def endProduction(self, time: float) -> None:
        debugLog(Debug.DEBUG, 'The workstation %d end day at %.2f' % (self.id, time))
        if self._product:
            self._product.stopProduction(time)
    
    def processProd(self) -> simpy.Process:
        try:
            if self._status != WrkStationStatus.IDLE:
                self.setStatus(WrkStationStatus.IDLE)
            # Check if I have enough items to work
            if(self._binItems == 0):
                with self._busBoy.request() as req:
                    debugLog(Debug.WARN, 'The workstation %d request restock at %.2f' % (self.id, self._env.now))
                    yield req 
                    # The resource is available
                    debugLog(Debug.DEBUG, 'The workstation %d request is being restocked at %.2f' % (self.id, self._env.now))
                    restock_time = abs(random.normalvariate(RESTOCK_TIME,1))
                    debugLog(Debug.DEBUG, "The workstation %d will take %.2f units of time to restock" % (self.id,restock_time))
                    self.setStatus(WrkStationStatus.RESTOCK)
                    yield self._env.timeout(restock_time)
                    self._binItems = MAX_RAW_BIN
                    debugLog(Debug.DEBUG, "The workstation %d was restocked at %.2f" % (self.id,self._env.now))
                    self.setStatus(WrkStationStatus.IDLE)
            # Check if there is the need to fix this work station
            if random.random() < self._errRate:
                self.setStatus(WrkStationStatus.DOWN)
                debugLog(Debug.WARN, 'The workstation %d presented a failure at %.2f' % (self.id, self._env.now))
                fixing_time = abs(random.normalvariate(FIX_TIME,1))
                debugLog(Debug.DEBUG, "The workstation %d will take %.2f units of time to be fixed" % (self.id,fixing_time))
                yield self._env.timeout(fixing_time)
                debugLog(Debug.INFO, 'The workstation %d is back on line at %.2f' % (self.id, self._env.now))
                self.setStatus(WrkStationStatus.IDLE)
            # Process the product
            self._binItems -= 1
            self._totalProducts.append(self._product._id)
            self._totalProductsDays[self._factory._day].append(self._product._id)
            debugLog(Debug.DEBUG, 'The workstation %d starts processing product %06d at %.2f' % (self.id, self.product._id, self._env.now))
            self.setStatus(WrkStationStatus.PRODUCING)
            working_time = abs(random.normalvariate(WORK_TIME,1))
            yield self._env.timeout(working_time)
            debugLog(Debug.DEBUG, 'The workstation %d is done processing prod %06d at %.2f' % (self.id, self.product._id, self._env.now))
            self.setStatus(WrkStationStatus.IDLE)
        except simpy.Interrupt:
            debugLog(Debug.ERROR, "There was a catastrophic issue, %d at %.2f" % (self.id, self._env.now))
            if self._status == ProductStatus.PRODUCING:
                self._statusTimes[self._status]["final"] = self._factory._env.now
            self.product.status = ProductStatus.ABORT
            self._totalStatus[self._status] += 1
            self._totalStatusDay[self._factory._day][self._status] +=1
            self._statusTimes[self._status] = self._factory._env.now
            self.setStatus(WrkStationStatus.STOP)
            if self._product._id not in self._productTimes:
                self._productTimes[self._product._id] = {"initial": 0, "final": self._factory._env.now}
            else:
                self._productTimes[self._product._id]["final"] = self._factory._env.now
        finally:
            if self._status != WrkStationStatus.IDLE:
                self._status = WrkStationStatus.IDLE
            if self._product._id not in self._productTimes:
                self._productTimes[self._product._id] = {"initial": 0, "final": self._factory._env.now}
            else:
                self._productTimes[self._product._id]["final"] = self._factory._env.now
            self._product = None

class Factory(object):
    def __init__(self, env: simpy.Environment) -> None:
        self._env = env
        self.i = 1
        self._restockDevice = simpy.Resource(self._env, RESTOCK_UNITS)
        self._workstations = []
        self._storage = []
        today = datetime.today()
        formatted_date = today.strftime('%d/%m/%Y')
        self._day = "_" + formatted_date
        self._storageDays = {self._day : []}
        self._leftoversDays = {self._day: []}
        self._onFloorDays = {self._day: []}
        self._status = FactoryStatus.OPEN
        self._shutdownsCount = 0
        self._shutdownsDay = {self._day : False}
        self._totalDayOrderedProducts = 10
        self._totalProductsStatus = {ProductStatus.DONE : 0, ProductStatus.FAIL: 0, ProductStatus.ORDERED: 0, ProductStatus.INCOMPLETE: 0, ProductStatus.ABORT: 0}
        self._totalProductsStatusDay = {self._day : {ProductStatus.DONE : 0, ProductStatus.FAIL: 0, ProductStatus.ORDERED: 0, ProductStatus.INCOMPLETE: 0, ProductStatus.ABORT: 0}}
        # Create all the work stations
        for i in range(WRK_STATIONS):
            self._workstations.append(Workstation(self._env, self._restockDevice, i, WRK_STATION_RATES[i], self))
            debugLog(Debug.DEBUG, "Ready %s" % self._workstations[i])
        self.action = self._env.process(self.produce())
        #self._storageDays[self._day] = self._storage.copy()
        
    def __str__(self) -> str:
        output = "\n==========\nFactory %s %s" % (self._status, self._day)
        totalDone = sum(1 for i in self._storage if i._status == ProductStatus.DONE)
        totalFail = sum(1 for i in self._storage if i._status == ProductStatus.FAIL)
        totalOrdered = sum(1 for i in self._storage if i._status == ProductStatus.ORDERED)
        totalIncomplete = sum(1 for i in self._storage if i._status == ProductStatus.INCOMPLETE)
        output += "\nTotal orders planned: %d" % (len(self._storage))
        output += "\nTotal Produced %d items, Total %d failed quality inspection." % (totalDone, totalFail)
        output += "\nTotal Orders left planned: %d \tTotal Orders left on floor: %d" % (totalOrdered, totalIncomplete)
        output += "\n---------------------------------------------"
        totalDayPlanned = len(self._storageDays[self._day])
        dayLeftovers = len(self._leftoversDays[self._day])
        dayPlanned = totalDayPlanned - dayLeftovers
        dayDone = sum(1 for i in self._storageDays[self._day] if i._status == ProductStatus.DONE)
        dayFail = sum(1 for i in self._storageDays[self._day] if i._status == ProductStatus.FAIL)
        dayOrdered = sum(1 for i in self._storageDays[self._day] if i._status == ProductStatus.ORDERED)
        dayIncomplete = sum(1 for i in self._storageDays[self._day] if i._status == ProductStatus.INCOMPLETE)
        output += "\nToday orders planned: %d, (%d new, %d leftovers)" % (totalDayPlanned, dayPlanned, dayLeftovers)
        output += "\nToday Produced %d items today, Today %d failed quality inspection." % (dayDone, dayFail)
        output += "\nToday Orders left planned: %d \tToday Orders left on floor: %d" % (dayOrdered, dayIncomplete)
        if(self._status == FactoryStatus.SHUTDOWN):
            totalAbort = sum(1 for i in self._storage if i._status == ProductStatus.ABORT)
            output += "\nTotal orders aborted due shutdown: %d" % (totalAbort)
            todayAbort = sum(1 for i in self._storageDays[self._day] if i._status == ProductStatus.ABORT)
            output += "\nToday orders aborted due shutdown: %d" % (todayAbort)
        if(DEBUG_LEVEL.value == Debug.DEBUG):
            prod = sum(1 for i in self._storageDays[self._day] if i._status == ProductStatus.PRODUCING)
            output += "\tErr: %d" % (prod)
            for prd in self._storageDays[self._day]:
                if prd._status == ProductStatus.PRODUCING:
                    output += "\n%s" % str(prd)
        return output
    
    def getWorkstation(self, index : int) -> Workstation:
        return self._workstations[index]
    
    def orderProduct(self, id: int) -> simpy.Process:
        if(self._status == FactoryStatus.CLOSED or self._status == FactoryStatus.SHUTDOWN):
            return
        prod = Product(id, self._env, self)
        self._storage.append(prod)
        self._storageDays[self._day].append(prod)
        while not prod.isDone and prod._status != ProductStatus.ABORT:
            idx = prod.nextStation
            # Check the situation of parallel stations
            if(idx == 3):   # station 4
                if(not prod.wasProccessedBy(4) and self.getWorkstation(idx).unit.count > self.getWorkstation(idx+1).unit.count):
                    idx += 1
            debugLog(Debug.DEBUG, "Product %06d to be processed by WS %02d" % (prod._id, (idx+1)))
            station = self.getWorkstation(idx)
            with station.unit.request() as wrkProcess:
                yield wrkProcess
                station.product = prod
                station._productTimes[prod._id] = {"initial": self._env.now, "final": -1}
                station.action = yield self._env.process(station.processProd())
        if not prod.isAborted:
            if random.random() < REJECT_RATE:
                if prod._status == ProductStatus.PRODUCING:
                    prod._statusTimes[prod._status]["final"] = self._env.now
                prod.status = ProductStatus.FAIL
                prod._totalStatus[prod._status] += 1
                if self._day in prod._totalStatusDay:
                    prod._totalStatusDay[self._day][prod._status] +=1
                prod._statusTimes[prod._status] = self._env.now
            else:
                if prod._status == ProductStatus.PRODUCING:
                    prod._statusTimes[prod._status]["final"] = self._env.now
                prod.status = ProductStatus.DONE
                prod._totalStatus[prod._status] += 1
                if self._day in prod._totalStatusDay:
                    prod._totalStatusDay[self._day][prod._status] +=1
                prod._statusTimes[prod._status] = self._env.now
        
    def produce(self) -> simpy.Process:
        # for i in range(5):
        while True:
            self._env.process(self.orderProduct(self.i))
            timeout = TICKS_PER_DAY / self._totalDayOrderedProducts
            yield self._env.timeout(timeout)
            self.i += 1
          
    def shutDown(self) -> None:
        if random.random() < CLOSE_RATE:
            self._shutdownsCount += 1
            self._shutdownsDay[self._day] = True
            closing_in = abs(random.normalvariate(12,1))
            debugLog(Debug.INFO, "Factory will close today in %d units." % closing_in)
            yield self._env.timeout(closing_in)
            # Interrupt all actions when catastrophic event triggers.
            map(lambda s: s.action.interrupt(), self._workstations)
            debugLog(Debug.ERROR, "\nFactory closed at %.2f." % self._env.now)
            self._status = FactoryStatus.SHUTDOWN
            for prd in self._storageDays[self._day]:
                if prd._status == ProductStatus.PRODUCING:
                    if prd._status == ProductStatus.PRODUCING:
                        prd._statusTimes[prd._status]["final"] = self._env.now
                    prd.status = ProductStatus.ABORT
                    prd._totalStatus[prd._status] += 1
                    prd._totalStatusDay[self._day][prd._status] +=1
                    prd._statusTimes[prd._status] = self._env.now
            for wk in self._workstations:
                wk.setStatus(WrkStationStatus.STOP)
        else:
            debugLog(Debug.INFO, "Factory will be accident free today.")
    
    def closeDown(self, time: float) -> None:
        if self._status != FactoryStatus.SHUTDOWN:
            self._status = FactoryStatus.CLOSED
            # map(lambda s: s.endProduction(time), self._workstations)
            [w.endProduction(time) for w in self._workstations]
            for prd in self._storageDays[self._day]:
                    if prd._status == ProductStatus.PRODUCING:
                        prd.stopProduction(time)
            for wk in self._workstations:
                wk.setStatus(WrkStationStatus.STOP)
            debugLog(Debug.INFO, "Factory closed at %.2f." % time)

    def formatTimeSeries(self, ts: list, st: WrkStationStatus) -> dict:
        formatTS = {}
        initial = -1
        final = -1
        for time in ts:
            if initial == -1:
                initial = time
            else:
                final = time
                formatTS[len(formatTS)] = {"initial": initial, "final": final}
                initial = -1
        return formatTS
    
    def saveFactoryData(self) -> None:
        totalDone = sum(1 for i in self._storage if i._status == ProductStatus.DONE)
        self._totalProductsStatus[ProductStatus.DONE] += totalDone
        totalFail = sum(1 for i in self._storage if i._status == ProductStatus.FAIL)
        self._totalProductsStatus[ProductStatus.FAIL] += totalFail
        totalOrdered = sum(1 for i in self._storage if i._status == ProductStatus.ORDERED)
        self._totalProductsStatus[ProductStatus.ORDERED] += totalOrdered
        totalIncomplete = sum(1 for i in self._storage if i._status == ProductStatus.INCOMPLETE)
        self._totalProductsStatus[ProductStatus.INCOMPLETE] += totalIncomplete
        totalAbort = sum(1 for i in self._storage if i._status == ProductStatus.ABORT)
        self._totalProductsStatus[ProductStatus.ABORT] += totalAbort


        dayDone = sum(1 for i in self._storageDays[self._day] if i._status == ProductStatus.DONE)
        self._totalProductsStatusDay[self._day][ProductStatus.DONE] = dayDone
        dayFail = sum(1 for i in self._storageDays[self._day] if i._status == ProductStatus.FAIL)
        self._totalProductsStatusDay[self._day][ProductStatus.FAIL] = dayFail
        dayOrdered = sum(1 for i in self._storageDays[self._day] if i._status == ProductStatus.ORDERED)
        self._totalProductsStatusDay[self._day][ProductStatus.ORDERED] = dayOrdered
        dayIncomplete = sum(1 for i in self._storageDays[self._day] if i._status == ProductStatus.INCOMPLETE)
        self._totalProductsStatusDay[self._day][ProductStatus.INCOMPLETE] = dayIncomplete
        todayAbort = sum(1 for i in self._storageDays[self._day] if i._status == ProductStatus.ABORT)
        self._totalProductsStatusDay[self._day][ProductStatus.ABORT] = todayAbort

    def saveWkTimes(self) -> None:
        for wk in self._workstations:
            for status in [WrkStationStatus.START, WrkStationStatus.IDLE, WrkStationStatus.PRODUCING, WrkStationStatus.RESTOCK, WrkStationStatus.DOWN, WrkStationStatus.STOP]:
                t = (self.calculateTotalTime(wk._totalStatusTimes[status]))
                wk._totalStatus[status] += t
                wk._totalStatusDay[self._day][status] = t
                timeSeries = self.formatTimeSeries(wk._totalStatusTimes[status], status)
                if status not in wk._statusTimeSeries:
                    wk._statusTimeSeries[status] = {}
                wk._statusTimeSeries[status].update(timeSeries.copy())
                wk._statusTimeSeriesDay[self._day][status] = timeSeries.copy()
                wk._totalStatusState[status] += len(timeSeries)
                wk._totalStatusStateDay[self._day][status] = len(timeSeries)

    def saveWkProductTimes(self, i: int) -> None:
        for wk in self._workstations:
            for product in wk._productTimes:
                if wk._productTimes[product]["final"] == -1:
                    wk._productTimes[product]["final"] = self._env.now
                if wk._productTimes[product]["initial"] == 0:
                    wk._productTimes[product]["initial"] = (i - 1) * 100
                t = (wk._productTimes[product]["final"] - wk._productTimes[product]["initial"])
                if product not in wk._totalProductTime:
                    wk._totalProductTime[product] = 0
                wk._totalProductTime[product] += t
                wk._totalProductTimeDay[self._day][product] = t
                if product not in wk._productTimeSeries:
                    wk._productTimeSeries[product] = []
                wk._productTimeSeries[product].append(wk._productTimes[product].copy())
                wk._productTimeSeriesDay[self._day][product] = wk._productTimes[product].copy()

    def saveProductWkTimes(self) -> None:
        for prd in self._storageDays[self._day]:
            for wk in prd._wksTimes:
                if "final" not in prd._wksTimes[wk]:
                    prd._wksTimes[wk]["final"] = self._env.now
                time = prd._wksTimes[wk]["final"] - prd._wksTimes[wk]["initial"]
                if wk not in prd._totalTimeWks:
                    prd._totalTimeWks[wk] = 0
                prd._totalTimeWks[wk] += time
                prd._totalTimeWksDay[self._day][wk] = time
                if wk not in prd._wksTimeSeries:
                    prd._wksTimeSeries[wk] = []
                prd._wksTimeSeries[wk].append(prd._wksTimes[wk].copy())
                prd._wksTimeSeriesDay[self._day][wk] = prd._wksTimes[wk].copy()

    def saveProductStatusTimes(self) -> None:
        for prd in self._storageDays[self._day]:
            for status in [ProductStatus.ORDERED, ProductStatus.PRODUCING, ProductStatus.DONE, ProductStatus.FAIL, ProductStatus.ABORT, ProductStatus.INCOMPLETE]:
                if status == ProductStatus.PRODUCING:
                    if "initial" in prd._statusTimes[status] and "final" in prd._statusTimes[status]:
                        time = prd._statusTimes[status]["final"] - prd._statusTimes[status]["initial"]
                    elif "initial" in prd._statusTimes[status] and "final" not in prd._statusTimes[status]:
                        prd._statusTimes[status]["final"] = self._env.now
                        time = prd._statusTimes[status]["final"] - prd._statusTimes[status]["initial"]
                    elif "initial" not in prd._statusTimes[status] and "final" in prd._statusTimes[status]:
                        prd._statusTimes[status]["initial"] = 0
                        time = prd._statusTimes[status]["final"]
                    elif "initial" not in prd._statusTimes[status] and "final" not in prd._statusTimes[status]:
                        time = 0
                    prd._totalTimeStatus[status] += time
                    prd._totalTimeStatusDay[self._day][status] = time
                    prd._statusTimeSeries[status].append(prd._statusTimes[status].copy())
                    prd._statusTimeSeriesDay[self._day][status] = prd._statusTimes[status].copy()
                else:
                    time = prd._statusTimes[status]
                    prd._totalTimeStatus[status] += 1
                    prd._totalTimeStatusDay[self._day][status] = time
                    prd._statusTimeSeries[status].append(prd._statusTimes[status])
                    prd._statusTimeSeriesDay[self._day][status] = prd._statusTimes[status]

    def endDay(self, isLast: bool) -> None:
        nextDayStorage = []
        previousDayLeftovers = []
        previousDayOnFloor = []
        for product in self._storageDays[self._day]:
            if product._status == ProductStatus.INCOMPLETE or product._status == ProductStatus.ORDERED:
                nextDayStorage.append(product)
                previousDayLeftovers.append(product)
                if product._status == ProductStatus.INCOMPLETE:
                    previousDayOnFloor.append(product)
        if not isLast:
            self._day = self.nextDay(self._day)
            #if len(nextDayStorage) == 0:
            self._storageDays[self._day] = nextDayStorage.copy()
            self._leftoversDays[self._day] = previousDayLeftovers.copy()
            self._onFloorDays[self._day] = previousDayOnFloor.copy()
            self._totalProductsStatusDay = {self._day : {ProductStatus.DONE : 0, ProductStatus.FAIL: 0, ProductStatus.ORDERED: 0, ProductStatus.INCOMPLETE: 0, ProductStatus.ABORT: 0}}
            self._shutdownsDay = {self._day: False}
            for wk in self._workstations:
                wk._totalProductsDays[self._day] = []
                wk._totalStatusTimes = {WrkStationStatus.START : [], WrkStationStatus.IDLE : [], WrkStationStatus.PRODUCING : [], WrkStationStatus.RESTOCK : [], WrkStationStatus.DOWN : [], WrkStationStatus.STOP: []}
                wk._totalStatusDay[self._day] = {WrkStationStatus.START : 0, WrkStationStatus.IDLE : 0, WrkStationStatus.PRODUCING : 0, WrkStationStatus.RESTOCK : 0, WrkStationStatus.DOWN : 0, WrkStationStatus.STOP: 0}
                wk._productTimes = {}
                wk._totalProductTimeDay[self._day] = {}
                wk._productTimeSeriesDay[self._day] = {}
                wk._statusTimeSeriesDay[self._day] = {}
                wk._totalStatusStateDay = {self._day : {WrkStationStatus.START : 0, WrkStationStatus.IDLE : 0, WrkStationStatus.PRODUCING : 0, WrkStationStatus.RESTOCK : 0, WrkStationStatus.DOWN : 0, WrkStationStatus.STOP: 0}}
            for prd in self._storageDays[self._day]:
                prd._totalWksDay[self._day] = {self._day: {}}
                prd._wksTimes = {}
                prd._totalTimeWksDay = {self._day: {}}
                prd._wksTimeSeriesDay = {self._day: {}}
                prd._totalStatusDay = {self._day: {ProductStatus.ORDERED : 0, ProductStatus.PRODUCING : 0, ProductStatus.DONE : 0, ProductStatus.FAIL : 0, ProductStatus.ABORT : 0, ProductStatus.INCOMPLETE : 0}}
                prd._statusTimes = {ProductStatus.ORDERED : 0, ProductStatus.PRODUCING : {}, ProductStatus.DONE : 0, ProductStatus.FAIL : 0, ProductStatus.ABORT : 0, ProductStatus.INCOMPLETE : 0}
                prd._totalTimeStatusDay = {self._day : { ProductStatus.ORDERED : 0, ProductStatus.PRODUCING : 0, ProductStatus.DONE : 0, ProductStatus.FAIL : 0, ProductStatus.ABORT : 0, ProductStatus.INCOMPLETE : 0 } }
                prd._statusTimeSeriesDay = {self._day : {ProductStatus.ORDERED : 0, ProductStatus.PRODUCING : {}, ProductStatus.DONE : 0, ProductStatus.FAIL : 0, ProductStatus.ABORT : 0, ProductStatus.INCOMPLETE : 0}}

    def nextDay(self, currentDay: str) -> str:
        currentDay = currentDay[1:]
        currentDay = currentDay.split("/")
        day = int(currentDay[0])
        month = int(currentDay[1])
        year = int(currentDay[2])
        """
        if int(day) < 31:
            day = str(int(day)+1)
        else:
            if int(month) < 12:
                month = str(int(month) + 1)
                day = "1"
            else:
                day = "1"
                month = "1"
                year = str(int(year)+1)
        nextDay = "/".join([day,month,year])
        """
        currentDay = date(year, month, day)
        nextDay = currentDay + timedelta(days=1)
        nextDay = "_" + nextDay.strftime("%d/%m/%Y")
        return nextDay
    
    def calculateTotalTime(self, times: list[int]) -> int:
        initialTime = -1
        finalTime = 0
        time = 0
        for t in times:
            if initialTime == -1:
                initialTime = t
            else:
                finalTime = t
                time += (finalTime - initialTime)
                initialTime = -1
        return time

    def saveTotalProduction(self) -> None:
        for status in self._totalProductsStatus:
            self._totalProductsStatus[status] = 0
        for prod in self._storage:
            self._totalProductsStatus[prod._status] += 1

def main() -> None:
    env = simpy.Environment()
    factory = Factory(env)
    completeProductionDay = {}
    completeDaysProduction = {}
    days = 100
    for i in range(1,days+1):
        print(i, factory._day)
        env.process(factory.shutDown())
        env.run(until=TICKS_PER_DAY*i)
        factory.closeDown(TICKS_PER_DAY)
        factory.saveFactoryData()
        factory.saveWkTimes()
        factory.saveWkProductTimes(i)
        factory.saveProductWkTimes()
        factory.saveProductStatusTimes()
        #print(factory)
        day = factory._day
        factoryProductionDay = {
            #"productsPlanned": len(factory._storageDays[day]),
            #"newOrders": len(factory._storageDays[day]) - len(factory._leftoversDays[day]),
            #"leftoverOrders": len(factory._leftoversDays[day]),
            "productsFinished": factory._totalProductsStatusDay[day][ProductStatus.DONE],
            "productsFailed": factory._totalProductsStatusDay[day][ProductStatus.FAIL],
            "productsAborted": factory._totalProductsStatusDay[day][ProductStatus.ABORT],
            "productsOrdered": factory._totalProductsStatusDay[day][ProductStatus.ORDERED],
            "productsIncomplete": factory._totalProductsStatusDay[day][ProductStatus.INCOMPLETE],
            #"floorLeftoverOrders": len(factory._onFloorDays[day]),
            "shutdown": factory._shutdownsDay[day]
        }

        workstationsProductionDay = {}
        
        for wk in factory._workstations:
            wkProductTimeSeriesDay = {}
            for product in wk._productTimeSeriesDay[day]:
                wkProductTimeSeriesDay[str(product)] = wk._productTimeSeriesDay[day][product]
            wkProductTotalTimeDay = {}
            for product in wk._totalProductTimeDay[day]:
                wkProductTotalTimeDay[str(product)] = wk._totalProductTimeDay[day][product]
            wkStatusCountDay = {}
            for status in wk._totalStatusStateDay[day]:
                st = "_"
                if status == WrkStationStatus.START:
                    st = "START"
                if status == WrkStationStatus.IDLE:
                    st = "IDLE"
                if status == WrkStationStatus.PRODUCING:
                    st = "PRODUCING"
                if status == WrkStationStatus.RESTOCK:
                    st = "RESTOCK"
                if status == WrkStationStatus.DOWN:
                    st = "DOWN"
                if status == WrkStationStatus.STOP:
                    st = "STOP"
                wkStatusCountDay[st] = wk._totalStatusStateDay[day][status]
            wkStatusTimeSeriesDay = {}
            for status in wk._statusTimeSeriesDay[day]:
                wkStatusTimeSeriesDayTS = {}
                for series in wk._statusTimeSeriesDay[day][status]:
                    wkStatusTimeSeriesDayTS[str(series)] = wk._statusTimeSeriesDay[day][status][series]
                st = "_"
                if status == WrkStationStatus.START:
                    st = "START"
                if status == WrkStationStatus.IDLE:
                    st = "IDLE"
                if status == WrkStationStatus.PRODUCING:
                    st = "PRODUCING"
                if status == WrkStationStatus.RESTOCK:
                    st = "RESTOCK"
                if status == WrkStationStatus.DOWN:
                    st = "DOWN"
                if status == WrkStationStatus.STOP:
                    st = "STOP"
                wkStatusTimeSeriesDay[st] = wkStatusTimeSeriesDayTS
            wkStatusTotalTimeDay = {}
            for status in wk._totalStatusDay[day]:
                st = "_"
                if status == WrkStationStatus.START:
                    st = "START"
                if status == WrkStationStatus.IDLE:
                    st = "IDLE"
                if status == WrkStationStatus.PRODUCING:
                    st = "PRODUCING"
                if status == WrkStationStatus.RESTOCK:
                    st = "RESTOCK"
                if status == WrkStationStatus.DOWN:
                    st = "DOWN"
                if status == WrkStationStatus.STOP:
                    st = "STOP"
                wkStatusTotalTimeDay[st] = wk._totalStatusDay[day][status]
            wkProudctionDay = {
                str(wk._id) : {
                    #"productsProcessed": wk._totalProductsDays[day],
                    #"productsTimeSeries": wkProductTimeSeriesDay,
                    #"productsTime": wkProductTotalTimeDay,
                    #"statusCount": wkStatusCountDay,
                    #"statusTimeSeries": wkStatusTimeSeriesDay,
                    "statusTime": wkStatusTotalTimeDay
                }
            }
            workstationsProductionDay.update(wkProudctionDay.copy())

        productsProductionDay = {}

        for prod in factory._storageDays[day]:
            prodWksVisitedDay = {}
            for wks in prod._totalWksDay[day]:
                prodWksVisitedDay[str(wks)] = prod._totalWksDay[day][wks]
            prodWksTimeDay = {}
            for wks in prod._totalTimeWksDay[day]:
                prodWksTimeDay[str(wks)] = prod._totalTimeWksDay[day][wks]
            prodWksTimeSeriesDay = {}
            for wks in prod._wksTimeSeriesDay[day]:
                prodWksTimeSeriesDay[str(wks)] = prod._wksTimeSeriesDay[day][wks]
            prodStatusCountDay = {}
            for status in prod._totalStatusDay[day]:
                st = "_"
                if status == ProductStatus.ORDERED:
                    st = "START"
                if status == ProductStatus.PRODUCING:
                    st = "PRODUCING"
                if status == ProductStatus.DONE:
                    st = "DONE"
                if status == ProductStatus.FAIL:
                    st = "FAIL"
                if status == ProductStatus.ABORT:
                    st = "ABORT"
                if status == ProductStatus.INCOMPLETE:
                    st = "INCOMPLETE"
                prodStatusCountDay[st] = prod._totalStatusDay[day][status]
            prodStatusTimeDay = {}
            for status in prod._totalTimeStatusDay[day]:
                st = "_"
                if status == ProductStatus.ORDERED:
                    st = "START"
                if status == ProductStatus.PRODUCING:
                    st = "PRODUCING"
                if status == ProductStatus.DONE:
                    st = "DONE"
                if status == ProductStatus.FAIL:
                    st = "FAIL"
                if status == ProductStatus.ABORT:
                    st = "ABORT"
                if status == ProductStatus.INCOMPLETE:
                    st = "INCOMPLETE"
                prodStatusTimeDay[st] = prod._totalTimeStatusDay[day][status]
            prodStatusTimeSeriesDay = {}
            for status in prod._statusTimeSeriesDay[day]:
                st = "_"
                if status == ProductStatus.ORDERED:
                    st = "START"
                if status == ProductStatus.PRODUCING:
                    st = "PRODUCING"
                if status == ProductStatus.DONE:
                    st = "DONE"
                if status == ProductStatus.FAIL:
                    st = "FAIL"
                if status == ProductStatus.ABORT:
                    st = "ABORT"
                if status == ProductStatus.INCOMPLETE:
                    st = "INCOMPLETE"
                prodStatusTimeSeriesDay[st] = prod._statusTimeSeriesDay[day][status]
            prodProductionDay = {
                str(prod._id) : {
                    #"workstationsVisited": prodWksVisitedDay,
                    "timeWorkstations": prodWksTimeDay,
                    #"workstationsTimeSeries": prodWksTimeSeriesDay,
                    #"statusCount": prodStatusCountDay,
                    #"statusTime": prodStatusTimeDay,
                    #"statusTimeSeries": prodStatusTimeSeriesDay
                }
            }
            productsProductionDay.update(prodProductionDay.copy())

        dayProduction = {
            day: {
                "factory": factoryProductionDay.copy(),
                "workstations": workstationsProductionDay.copy(),
                #"products": productsProductionDay.copy()
            }
        }
        completeDaysProduction.update(dayProduction.copy())    
        if i == days:
            factory.endDay(True)
        else:
            factory.endDay(False)
        factory._status = FactoryStatus.OPEN
        for wk in factory._workstations:
            wk.setStatus(WrkStationStatus.START)
    factory._status = FactoryStatus.CLOSED
    factory.saveTotalProduction()
    totalFactoryProduction = {
        "productsPlanned": len(factory._storage),
        "productsFinished": factory._totalProductsStatus[ProductStatus.DONE],
        "productsFailed": factory._totalProductsStatus[ProductStatus.FAIL],
        "productsAborted": factory._totalProductsStatus[ProductStatus.ABORT],
        "productsOrdered": factory._totalProductsStatus[ProductStatus.ORDERED],
        "productsIncomplete": factory._totalProductsStatus[ProductStatus.INCOMPLETE],
        "totalShutdowns": factory._shutdownsCount,
        "totalDays": days
    }

    totalWorkstationsProduction = {}

    for wk in factory._workstations:
        wkProductTimeSeries = {}
        for product in wk._productTimeSeries:
            wkProductTimeSeries[str(product)] = wk._productTimeSeries[product]
        wkProductTotalTime = {}
        for product in wk._totalProductTime:
            wkProductTotalTime[str(product)] = wk._totalProductTime[product]
        wkStatusCount = {}
        for status in wk._totalStatusState:
            st = "_"
            if status == WrkStationStatus.START:
                st = "START"
            if status == WrkStationStatus.IDLE:
                st = "IDLE"
            if status == WrkStationStatus.PRODUCING:
                st = "PRODUCING"
            if status == WrkStationStatus.RESTOCK:
                st = "RESTOCK"
            if status == WrkStationStatus.DOWN:
                st = "DOWN"
            if status == WrkStationStatus.STOP:
                st = "STOP"
            wkStatusCount[st] = wk._totalStatusState[status]
        wkStatusTimeSeries = {}
        for status in wk._statusTimeSeries:
            wkStatusTimeSeriesTS = {}
            for series in wk._statusTimeSeries[status]:
                wkStatusTimeSeriesTS[str(series)] = wk._statusTimeSeries[status][series]
            st = "_"
            if status == WrkStationStatus.START:
                st = "START"
            if status == WrkStationStatus.IDLE:
                st = "IDLE"
            if status == WrkStationStatus.PRODUCING:
                st = "PRODUCING"
            if status == WrkStationStatus.RESTOCK:
                st = "RESTOCK"
            if status == WrkStationStatus.DOWN:
                st = "DOWN"
            if status == WrkStationStatus.STOP:
                st = "STOP"
            wkStatusTimeSeries[st] = wkStatusTimeSeriesTS
        wkStatusTotalTime = {}
        for status in wk._totalStatus:
            st = "_"
            if status == WrkStationStatus.START:
                st = "START"
            if status == WrkStationStatus.IDLE:
                st = "IDLE"
            if status == WrkStationStatus.PRODUCING:
                st = "PRODUCING"
            if status == WrkStationStatus.RESTOCK:
                st = "RESTOCK"
            if status == WrkStationStatus.DOWN:
                st = "DOWN"
            if status == WrkStationStatus.STOP:
                st = "STOP"
            wkStatusTotalTime[st] = wk._totalStatus[status]
        wkProudction = {
            str(wk._id) : {
                #"productsProcessed": wk._totalProducts,
                #"productsTimeSeries": wkProductTimeSeries,
                #"productsTotalTime": wkProductTotalTime,
                "statusCount": wkStatusCount,
                #"statusTimeSeries": wkStatusTimeSeries,
                "statusTotalTime": wkStatusTotalTime
            }
        }
        totalWorkstationsProduction.update(wkProudction.copy())

    totalProductsProduction = {}

    for prod in factory._storage:
        prodWksVisited = {}
        for wks in prod._totalWks:
            prodWksVisited[str(wks)] = prod._totalWks[wks]
        prodWksTime = {}
        for wks in prod._totalTimeWks:
            prodWksTime[str(wks)] = prod._totalTimeWks[wks]
        prodWksTimeSeries = {}
        for wks in prod._wksTimeSeries:
            prodWksTimeSeries[str(wks)] = prod._wksTimeSeries[wks]
        prodStatusCount = {}
        for status in prod._totalStatus:
            st = "_"
            if status == ProductStatus.ORDERED:
                st = "START"
            if status == ProductStatus.PRODUCING:
                st = "PRODUCING"
            if status == ProductStatus.DONE:
                st = "DONE"
            if status == ProductStatus.FAIL:
                st = "FAIL"
            if status == ProductStatus.ABORT:
                st = "ABORT"
            if status == ProductStatus.INCOMPLETE:
                st = "INCOMPLETE"
            prodStatusCount[st] = prod._totalStatus[status]
        prodStatusTime = {}
        for status in prod._totalTimeStatus:
            st = "_"
            if status == ProductStatus.ORDERED:
                st = "START"
            if status == ProductStatus.PRODUCING:
                st = "PRODUCING"
            if status == ProductStatus.DONE:
                st = "DONE"
            if status == ProductStatus.FAIL:
                st = "FAIL"
            if status == ProductStatus.ABORT:
                st = "ABORT"
            if status == ProductStatus.INCOMPLETE:
                st = "INCOMPLETE"
            prodStatusTime[st] = prod._totalTimeStatus[status]
        prodStatusTimeSeries = {}
        for status in prod._statusTimeSeries:
            st = "_"
            if status == ProductStatus.ORDERED:
                st = "START"
            if status == ProductStatus.PRODUCING:
                st = "PRODUCING"
            if status == ProductStatus.DONE:
                st = "DONE"
            if status == ProductStatus.FAIL:
                st = "FAIL"
            if status == ProductStatus.ABORT:
                st = "ABORT"
            if status == ProductStatus.INCOMPLETE:
                st = "INCOMPLETE"
            prodStatusTimeSeries[st] = prod._statusTimeSeries[status]
        prodProduction = {
            str(prod._id) : {
                "workstationsVisited": prodWksVisited,
                "timeWorkstations": prodWksTime,
                "workstationsTimeSeries": prodWksTimeSeries,
                "statusCount": prodStatusCount,
                "statusTime": prodStatusTime,
                "statusTimeSeries": prodStatusTimeSeries
            }
        }
        totalProductsProduction.update(prodProduction.copy())

    totalProduction = {
        "factory": totalFactoryProduction.copy(),
        "workstations": totalWorkstationsProduction.copy(),
        #"products": totalProductsProduction.copy()
    }

    obj = {
            "sim" : {
                "ticks": TICKS_PER_DAY,
                "closeRate": CLOSE_RATE,
                "rejectRate": REJECT_RATE,
                "maxRawBin": MAX_RAW_BIN,
                "restockUnits": RESTOCK_UNITS,
                "restockTime": RESTOCK_TIME,
                "fixTime": FIX_TIME,
                "workTime": WORK_TIME,
                "workStations": WRK_STATIONS,
                "workSationRate": WRK_STATION_RATES,
                "productsOrderedDay": factory._totalDayOrderedProducts,
                "simulationDurationDays": days,
                "production": {
                    "daily": {},
                    "total": totalProduction.copy()
                }
            }
        }
    print("===================================================")
    print(obj)
    #print(obj)
    doc_ref = db.collection("sim")
    docs = doc_ref.stream()
    docsNum = 0
    for doc in docs:
        docsNum += 1
    doc_ref = db.collection("sim").document("1")
    doc_ref.set(obj["sim"])
    for day in completeDaysProduction:
        update_data = {f"production.daily.{day[1:]}": completeDaysProduction[day]}
        doc_ref.update(update_data)
    
if __name__ == '__main__':
    main()