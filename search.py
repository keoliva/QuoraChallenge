import sys
import copy
import random
import time

import collections
import functools

class memoized(object):
    '''Decorator. Caches a function's return value each time it is called.
    If called later with the same arguments, the cached value is returned
    (not reevaluated).
    '''
    def __init__(self, func):
        self.func = func
        self.cache = {}
    def __call__(self, *args):
        if not isinstance(args, collections.Hashable):
            # uncacheable. a list, for instance.
            # better to not cache than blow up.
            return self.func(*args)
        if args in self.cache:
            return self.cache[args]
        else:
            value = self.func(*args)
            self.cache[args] = value
            return value
    def __repr__(self):
        '''Return the function's docstring.'''
        return self.func.__doc__
    def __get__(self, obj, objtype):
        '''Support instance methods.'''
        return functools.partial(self.__call__, obj)

class Item(object):
    '''has types: user | topic | question | board'''
    def __init__(self, itemType, itemID, score, dataStr, insertion_id):
        self.itemType = itemType
        self.itemID = itemID
        self.score = float(score)
        self.dataStr = dataStr
        self.insertion_id = insertion_id
        
    def __repr__(self):
        info = (self.itemType, self.itemID, self.score, self.dataStr)
        return "Item(type:%r, id:%r, score:%f, data string:%r)" % info
    
    def __cmp__(self, other):
        comp = cmp(self.score, other.score)
        if comp == 0:
            #when there's a tie in the score, newer items are ranked higher
            return -1 * cmp(self.insertion_id, other.insertion_id)
        #<id>s are printed in descending score order
        return -1 * comp
    
    def __eq__(self, other):
        return self.itemID == other.itemID

class TrieNode(object):
    def __init__(self, c):
        self.char = c
        self.left = None
        self.middle = None
        self.right = None
        self.items = set()

class Trie(object):
    def __init__(self):
        self.root = None

    def __repr__(self):
        return self.root

    def remove(self, words, item):
        def delete_char(T, word, i):
            if T == None: return T
            if word[i] < T.char: T.left = delete_char(T.left, word, i)
            elif word[i] > T.char: T.right = delete_char(T.right, word, i)
            else:
                T.items.discard(item)
                try:
                    c = word[i+1]
                    T.middle = delete_char(T.middle, word, i+1)
                except IndexError:
                    pass
            return T
        for word in words:
            if word: self.root = delete_char(self.root, word, 0)
        
    def insert(self, words, item):
        def add_char(T, word, i):
            if T == None:
                T = TrieNode(word[i])
            if word[i] < T.char: T.left = add_char(T.left, word, i)
            elif word[i] > T.char: T.right = add_char(T.right, word, i)
            else:
                T.items.add(item)
                try:
                    c = word[i+1]
                    T.middle = add_char(T.middle, word, i+1)
                except IndexError:
                    pass
            return T
        for word in words:
            if word: self.root = add_char(self.root, word, 0)
        
    def isPrefix(self, word):
        def lookup(T, word, i):
            if T == None: return set()
            if word[i] < T.char: return lookup(T.left, word, i)
            if word[i] > T.char: return lookup(T.right, word, i)
            try:
                c = word[i+1]
                return lookup(T.middle, word, i+1)
            except IndexError:
                return T.items
        
        return lookup(self.root, word, 0)
        
class MainHandler(object):
    def __init__(self):
        self.items = {}
        self.trie = Trie()
        
    def add_command(self, commandData, insertionID):
        '''ADD <type> <id> <score> <data string that contain spaces>'''
        [itemType,itemID,score,dataStr] = commandData.split(" ",3)
        item = Item(itemType,itemID,score,dataStr,insertionID)
        self.items[itemID] = item
        self.trie.insert(dataStr.lower().split(), item)
        
    def delete_command(self, command_data):
        '''DEL <id>'''
        itemID = command_data
        item = self.items.pop(itemID, None)
        self.trie.remove(item.dataStr.lower().split(), item)
        
    def query_command(self, command_data):
        '''QUERY <number of results> <query string that can contain spaces>'''
        [numOfResults, queryStr] = command_data.split(" ",1)
        numOfResults = int(numOfResults)
        queryTokens = queryStr.lower().split(" ")
        print time.time()
        #self.query({}, numOfResults, queryTokens)
        
    def wquery_command(self, command_data):
        '''WQUERY <number of results> <number of boosts>
                  (<type>:<boost>)* (<id>:<boost>)*
                  <query string that can contain spaces>'''
        [numOfResults, numOfBoosts, rest_of_query] = command_data.split(" ", 2)
        numOfResults = int(numOfResults)
        numOfBoosts = int(numOfBoosts)
        rest_of_query = rest_of_query.split(" ", numOfBoosts)

        boosts = {}
        for i in range(numOfBoosts):
            [affected,boost] = rest_of_query[i].split(":")
            try:
                boosts[affected] += [float(boost)]
            except KeyError:
                boosts[affected] = [float(boost)]
                                                          
        queryStr = rest_of_query[-1]
        queryTokens = queryStr.lower().split(" ")
        print time.time()
        
        #self.query(boosts, numOfResults, queryTokens)

    def query(self, boosts, numOfResults, queryTokens):
        types = ['user','topic','question','board']

        deep_copy = copy.deepcopy
        isPrefix = self.trie.isPrefix
        valuesWithTokens = map(lambda x: isPrefix(x), queryTokens)
        try:
            values = reduce(lambda x,y: x & y, valuesWithTokens[1:],
                                               valuesWithTokens[0])
        except IndexError:
            values = set()

        values = list(values)
        if boosts:
            for (i,value) in enumerate(values):
                for b_key in boosts.keys():
                    for boost in boosts[b_key]:
                        if b_key in types:
                            if value.itemType == b_key:
                                value = deep_copy(value)
                                value.score *= boost
                        else: #an id is specified
                            value = deep_copy(self.items[b_key])
                            value.score *= boost
                        values[i] = value
        print time.time()         
        values.sort()
        values = values[:numOfResults]
        if values:
            i = iter(values)
            _ = i.next()
            for item in values:
                try:
                    if i.next():
                        print item.itemID,
                except StopIteration:
                    print item.itemID
        else:
            print ""
            
def main(inputt):
    #lines = sys.stdin.readline().split('\n')
    lines = inputt.split('\n')
    #N = int(lines[0])
    Main = MainHandler()
    add = Main.add_command
    delete = Main.delete_command
    query = Main.query_command
    wquery = Main.wquery_command
    inserted = 0
    for obj in lines[1:-1]:
        [command, command_data] = obj.split(" ", 1)

        if command == 'ADD':
            add(command_data,inserted)
            inserted += 1
        elif command == 'DEL':
            delete(command_data)
        elif command == 'QUERY':
            query(command_data)
        elif command == 'WQUERY':
            wquery(command_data)


############################################################################
##############################Tests#########################################
def make_input():
    types = ['user','topic','question','board']
    inputt = "39999\n"
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
        score = float(random.randrange(1,100)) #range [0,1)

        comm = 'ADD %s %s %f %s' % (item_type,item_id,score,data_str[0])
        inputt += (comm + '\n')
        
    inputt += 'DEL %s\n' % x[0]
    inputt += 'QUERY 10 His\n'
    inputt += 'QUERY 10 girls\n'
    inputt += 'QUERY 10 His\n'
    inputt += 'DEL %s\n' % x[100]
    inputt += 'QUERY 30 I\n'
    inputt += 'WQUERY 2 3 %s:1.0 %s:20.0 topic:9.99 phone\n' % (x[5], x[7777])
    inputt += 'DEL %s\n' % x[888]
    inputt += 'DEL %s\n' % x[900]
    inputt += 'WQUERY 20 1 user:5.6 he can buy most expensive\n'
    inputt += 'DEL %s\n' % x[999]
        
    return inputt


x=make_input()
s = time.time()
main(x)
e = time.time()
print '%d' % (e-s)
#main()

