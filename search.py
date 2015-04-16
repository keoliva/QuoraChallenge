import copy
import random
import time
import heapq

class Item(object):
    '''Item is what's ADDed, where it's data string is what's matched
       against queries.
       
       Attributes:
         type: options are user | topic | question | board
         id: a unique id of the item
         score
         dataStr: this is what's matched against the queries
         insertionID: newly added items will have larger insertionIDs
    '''
    def __init__(self, type_, id_, score, dataStr, insertionID):
        self.type = type_
        self.id = id_
        self.score = float(score)
        self.dataStr = dataStr
        self.insertionID = insertionID
        
    def __repr__(self):
        info = (self.type, self.id, self.score, self.dataStr)
        return "Item(type:%r, id:%r, score:%f, data string:%r)" % info
    
    def __cmp__(self, other):
        comp = cmp(self.score, other.score)
        if comp == 0:
            #when there's a tie in the score, newer items are ranked higher
            return cmp(self.insertionID, other.insertionID)
        #<id>s are printed in descending score order
        return comp
    
    def __eq__(self, other):
        return self.id == other.id

class TrieNode(object):
    '''A node within a trie.

       Attributes:
         char: the character that the node represents
         middle: the set of nodes that branch off the node
         items: set of objects of type Item that contain the prefixes
         upto the node within their data string
    '''         
    def __init__(self, c=""):
        self.char = c
        self.middle = {}
        self.items = set()

class Trie(object):
    def __init__(self):
        self.root = TrieNode()
            
    def remove(self, words, item):
        '''removes an item from the set of items in all the nodes
           within the path in the trie, of every word in the item's
           data string'''
        for word in words:
            currNode = self.root
            for i,ltr in enumerate(word):
                currNode = currNode.middle[ltr]
                currNode.items.discard(item)
        
    def insert(self, words, item):
        '''includes the item in the set of items in all the nodes
           within the path in the trie, of every word in the item's
           data string
        '''
        for word in words:
            currNode = self.root
            for i,ltr in enumerate(word):
                try:
                    currNode = currNode.middle[ltr]
                except KeyError:
                    newNode = TrieNode(ltr)
                    currNode.middle[ltr] = newNode
                    currNode = currNode.middle[ltr]
                currNode.items.add(item)
        
    def isPrefix(self, word):
        '''returns the set of items at the end of the path of the word in the
           trie if the word is in the trie
        '''
        currNode = self.root
        for i,ltr in enumerate(word):
            try:
                currNode = currNode.middle[ltr]
            except KeyError:
                return set()
        return currNode.items

class ManageTopItems(object):
        '''Makes sure that the first n elements are kept in the heap,
           where n represents the number of results required from the query
        '''
        def __init__(self, numOfResults):
            self.heap = []
            self.numOfResults = numOfResults
            self.itemsInserted = 0

        def push(self, item):
            if self.itemsInserted >= self.numOfResults:
                _ = heapq.heappushpop(self.heap, item)
            else:
                heapq.heappush(self.heap, item)
                self.itemsInserted += 1
                
        def heapify(self, iterable):
            heapq.heapify(iterable)
            self.heap = iterable

class MainHandler(object):
    '''Handles the commands passed in as input
    '''
    def __init__(self):
        self.items = {}
        self.trie = Trie()
        
    def add(self, commandData, insertionID):
        '''ADD <type> <id> <score> <data string that contain spaces>'''
        [type_,id_,score,dataStr] = commandData.split(" ",3)
        item = Item(type_,id_,score,dataStr,insertionID)
        self.items[id_] = item
        self.trie.insert(dataStr.lower().split(), item)
        
    def delete(self, commandData):
        '''DEL <id>'''
        itemID = commandData
        item = self.items.pop(itemID, None)
        self.trie.remove(item.dataStr.lower().split(), item)
        
    def query(self, commandData):
        '''QUERY <number of results> <query string that can contain spaces>'''
        [numOfResults, queryStr] = commandData.split(" ",1)
        numOfResults = int(numOfResults)
        queryTokens = queryStr.lower().split(" ")
        
        print self._query({}, numOfResults, queryTokens)
        
    def wquery(self, commandData):
        '''WQUERY <number of results> <number of boosts>
                  (<type>:<boost>)* (<id>:<boost>)*
                  <query string that can contain spaces>'''
        [numOfResults, numOfBoosts, restOfQuery] = commandData.split(" ", 2)
        numOfResults = int(numOfResults)
        numOfBoosts = int(numOfBoosts)
        restOfQuery = restOfQuery.split(" ", numOfBoosts)

        boosts = {}
        for i in range(numOfBoosts):
            [affected,boost] = restOfQuery[i].split(":")
            try:
                boosts[affected] += [float(boost)]
            except KeyError:
                boosts[affected] = [float(boost)]
                                                          
        queryStr = restOfQuery[-1]
        queryTokens = queryStr.lower().split(" ")
        
        print self._query(boosts, numOfResults, queryTokens)

    def _query(self, boosts, numOfResults, queryTokens):
        '''prints the items that match the words in the query string, upto
           a certain number -- numOfResult'''
        types = ['user','topic','question','board']

        deepcopy = copy.deepcopy
        isPrefix = self.trie.isPrefix 
        valuesWithTokens = map(lambda x: isPrefix(x), queryTokens)
        try:
            values = reduce(lambda x,y: x & y, valuesWithTokens[1:],
                                               valuesWithTokens[0])
        except IndexError:
            values = set()            

        heapHandler = ManageTopItems(numOfResults)
        if boosts:
            for (i,value) in enumerate(values):
                for bKey in boosts.keys():
                    for boost in boosts[bKey]:
                        if bKey in types:
                            if value.type == bKey:
                                value = deepcopy(value)
                                value.score *= boost
                        else: #an id is specified
                            value = deepcopy(self.items[bKey])
                            value.score *= boost
                heapHandler.push(value)
        else:
            heapHandler.heapify(list(values))
            
        largeInputSize = 1000    
        if numOfResults < largeInputSize:
            results = heapq.nlargest(numOfResults, heapHandler.heap)
        else:
            results = sorted(heapHandler.heap,
                             lambda x,y:-1*cmp(x,y))[:numOfResults]
        return " ".join([item.id for item in results])


def main():
    lines = raw_input().split('\n')
    #lines = inputt.split('\n')
    N = int(lines[0])
    Main = MainHandler()
    add = Main.add
    delete = Main.delete
    query = Main.query
    wquery = Main.wquery
    inserted = 0
    for line in lines[1:N+1]:
        [command, commandData] = line.strip().split(" ", 1)

        if command == 'ADD':
            add(commandData,inserted)
            inserted += 1
        elif command == 'DEL':
            delete(commandData)
        elif command == 'QUERY':
            query(commandData)
        elif command == 'WQUERY':
            wquery(commandData)

if __name__ == '__main__':
    main()

############################################################################
##############################Test Time#####################################
def make_input():
    types = ['user','topic','question','board']
    inputt = "30000\n"
    data_str = '''This is a true story.

    A few years ago, I was at a party. Most people there were very wealthy. There were many diplomats, executives and wealthy businessmen. 

    There was a tiny man who dressed very average.  He stood at the corner drinking his scotch. I came over and  said hi. In a room of  expensive tailored suits, the man looked like someone's chauffeur. 

    We chatted for a while and he took out his phone for something . He had an old "dumb phone" that costed less than the  drink I was holding at a decent bar.  The amount of high end and luxury phone in that room was ridiculous. We had people who flashed their 10K+ gold phone.

    Anyway we exchanged number. When it was time to go home, he just took a taxi home when everyone else called their chauffeurs. 

    I had too many drinks to try to figure out who he was. But from the clothes, phone, and car, he didn't look like a big deal.

    The next day, I sent him a thank you text for watering down my drink. It was nice of him to make sure I was not drinking too much. He asked to hang out. I said yes because he was cool and nice. I love meeting random smart people and bounce ideas.

    When I got to dinner, It was at a lovely nice restaurant in a nice high end building. Turned out the tiny guy was one of the main investors of this skyscraper in the heart of the city. He also invested in many other projects in town. His net worth was more than many people at that party with fancy + luxury smartphones combined.

    I asked him why he uses a dumb phone when he can buy the most expensive phone on the market.

    He replied- It works and does exactly what I need. 

    Never judge a person by his phone. Jack Dorsey used to take the bus to work. His net worth is 2.7 B. Warren Buffet lives in a normal 5 bedroom house. It doesn't stop me from admiring these people. It makes them even more interesting

    You won't be able to afford the girls who have a problem with your phone anyway. It is a nice filter to have.'''
    data_str = data_str.split("\n")
    data_str = filter(lambda x: x!="", data_str)
    dat_str = map(lambda x: x[:100], data_str)
    x=[]
    sc = 0.0
    for i in range(39999):
        random.shuffle(data_str)
        item_type = types[random.randrange(0,4)]
        item_id = item_type[0]+str(i)

        x += [item_id]
        score = float(random.randrange(1,100)) 

        comm = 'ADD %s %s %f %s' % (item_type,item_id,score,data_str[0])
        inputt += (comm + '\n')
        
    inputt += 'DEL %s\n' % x[0]
    inputt += 'QUERY 10 I\n'
    inputt += 'QUERY 10 girls\n'
    inputt += 'QUERY 10 His\n'
    inputt += 'DEL %s\n' % x[80]
    inputt += 'QUERY 30 I\n'
    inputt += 'WQUERY 3 3 board:2.0 topic:9.99 user:5.0 phone\n'
    inputt += 'DEL %s\n' % x[8]
    inputt += 'DEL %s\n' % x[90]
    inputt += 'WQUERY 20 1 user:5.6 he can buy most expensive\n'
    inputt += 'DEL %s\n' % x[99]
        
    return inputt

##x=make_input()
##s = time.time()
##main(x)
##e = time.time()
##print '%d' % (e-s)
