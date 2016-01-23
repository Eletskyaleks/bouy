import random
import math
import time
import _thread

#singleton
class ModelCore(object):
    arrayOfBuoys = {}
    topValueDist = 1
    bottomValueDist = 3

    arrayOfBuoysWithMessages = []

    def __new__(cls, isMessageDelivered):
        if not hasattr(cls, 'instance'):
            cls.instance = super(ModelCore, cls).__new__(cls)
            cls.isMessageDelivered = isMessageDelivered
        return cls.instance

    def __init__(self,isMessageDelivered):
        self.isMessageDelivered = isMessageDelivered

    def generateBoys(self, quantity, averageDist, sigma):
        coord = 0
        for i in range(0 , quantity):
            coord += random.normalvariate(averageDist, sigma) #previous + rand Gauss value
            self.arrayOfBuoys[i] = [coord, Bouy(i)]

    #sends all messages from bouy
    def sendMessageFromBouy(self, id):
        arrayOfCatchedBouysIds = []     #array of boys recieving messages from bouy
        #checking if message is delivered
        for i in self.arrayOfBuoys:
            distBetweenBouys = math.fabs(self.arrayOfBuoys[id][0] - self.arrayOfBuoys[i][0])
            if i == id: continue # avoiding sending to itself
            if self.isMessageDelivered(self.bottomValueDist, self.topValueDist, distBetweenBouys):
                arrayOfCatchedBouysIds.append(self.arrayOfBuoys[i])
        #handling of catched bouys
        for catchedBouy in arrayOfCatchedBouysIds:
                catchedBouy.modem.getMessages(self.arrayOfBuoys[id].modem.sendMessages())

    def setRouters(self, arrayOfRouters ):
        for i in arrayOfRouters:
            if i < len(self.arrayOfBuoys):
                self.arrayOfBuoys[i].isRouter = True

    def setBouyesWithMessages(self, arrayOfBouysIds):
        for i in arrayOfBouysIds:
            if i < len(self.arrayOfBuoys):
                self.arrayOfBuoys[i].sendData()

    def sendAllMessagesFromBouys(self):
        while True:
            #checking bouys for existence of messages
            arrayOfBouysWithMessages = []
            for i in self.arrayOfBuoys:
                if len(i.modem.messagesToSent) > 0:
                    arrayOfBouysWithMessages.append(i)

            if len(arrayOfBouysWithMessages) == 0: break
            else:
                for i in arrayOfBouysWithMessages:
                    self.sendMessageFromBouy(i.id)


class Modem:
    #bouy = None
    #messagesToSent = {}

    def __init__(self, bouy):
        self.bouy = bouy
        self.messagesToSent = {}

    def sendMessages(self):
        tempMessToSent = self.messagesToSent
        self.messagesToSent = {}
        return tempMessToSent


    def getMessage(self, messageArr):
        for messageKey in messageArr:
            self.bouy.getData(messageKey, messageArr[messageKey])

    def incrementAllMessageaToAck(self):
        self.bouy.incrementAllMesToAck()


class MessagesRecievedAndAck:
    #messKeep = []
    #length

    def __init__(self, length):
        self.messKeep = []
        self.length = length

    def addMess(self, messKey):
        if len(self.messKeep) == self.length:
            self.messKeep.pop(0)
        idKey = messKey.split() # first element - bouy id, second - mess id
        self.messKeep.append([idKey[0],idKey[1]])

    def searchForMes(self, messKey):
        idKey = messKey.split()
        if idKey in self.messKeep: return True
        else: return False


class Bouy:
    #id = 0
    #messageCounter = 0
    #messageData = "dataOfBouy"
    #logOfMessages = []
    #modem = None
    #isRouter = False
    #messagesRecievedAndAck
    #messagesToAck
    #messagesToAckSendCounter
    #timeForWaitingOfAck = 30

    def __init__(self, id):
        self.id = id
        self.modem = Modem(self)
        self.messageData = "dataOfBouy"
        self.isRouter = False
        self.messageCounter = 0
        self.messagesRecievedAndAck = MessagesRecievedAndAck(30) #temporary buffer
        self.messagesToAck = {}  #messages are needed to be acknowledged
        self.messagesToAckSendCounter = 5  #counter to ack
        self.timeForWaitingOfAck = 30

    def getData(self, messageKey, messageData):
        #check if it's a message to acknowledge
        if self.messagesToAck.get(messageKey):
            #save if temporary buffer and delete form acknolegment array
            self.messagesRecievedAndAck.addMess(messageKey)
            #the message acknowledged, so delete it from messagesToAck
            self.messagesToAck.pop(messageKey)
        #check the message in temp buffer
        else:
            if self.messagesRecievedAndAck.searchForMes(messageKey) == False:
                #if not in buffer, it's completely new, so resend the message and wait for acknowledge
                self.modem.messagesToSent[messageKey] = messageData
                self.messagesToAck[messageKey] = [messageData,1]# it stores the message data and a counter of times message was sent
                _thread.start_new_thread(self.watingForAck, (messageKey,))

    #is locking needed here?
    #if there is a message, which is wating to ack, it will be sent messagesToAckSendCounter times with period timeForWaitingOfAck
    # and then stops, if not, the thread stops
    def watingForAck(self, messageKey):
        while 1:
            time.sleep(self.timeForWaitingOfAck)
            if self.messagesToAck.get(messageKey):
                if self.messagesToAck[messageKey][1] <= self.messagesToAckSendCounter:
                    self.modem.messagesToSent[messageKey] = self.messageData#sending message another time
                    self.messagesToAck[messageKey][1] += 1 #incrementing ack counter
                else: #ack counter overflow
                    self.messagesToAck.pop(messageKey)
                    break
            else:
                break

    def sendData(self):
        messageKey = self.id +"_"+ self.messageCounter #bouy id + message id
        if self.messageCounter == 255: self.messageCounter = 0
        self.messageCounter += 1
        self.modem.messagesToSent[messageKey] = self.messageData #the message will be sent to other boys
        self.messagesToAck[messageKey] = [self.messageData,1] # it stores the message data and a counter of times message was sent
        _thread.start_new_thread(self.watingForAck, (messageKey,))
