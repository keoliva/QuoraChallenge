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
    def __init__(self, type_, id_, score, dataStr, insertion_id):
        self.type = type_
        self.id = id_
        self.score = float(score)
        self.dataStr = dataStr
        self.insertion_id = insertion_id
        
    def __repr__(self):
        info = (self.type, self.id, self.score, self.dataStr)
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
    def __init__(self, c=""):
        self.char = c
        self.left = None
        self.middle = {}
        self.right = None
        self.items = set()

class Trie(object):
    def __init__(self):
        self.root = TrieNode()

    def __repr__(self):
        return ""
            
    def remove(self, words, item):
        for word in words:
            curr_node = self.root
            for i,ltr in enumerate(word):
                try:
                    curr_node = curr_node.middle[ltr]
                except KeyError:
                    new_node = TrieNode(ltr)
                    curr_node.middle[ltr] = new_node
                    curr_node = curr_node.middle[ltr]
                curr_node.items.discard(item)
        
    def insert(self, words, item):
        for word in words:
            curr_node = self.root
            for i,ltr in enumerate(word):
                try:
                    curr_node = curr_node.middle[ltr]
                except KeyError:
                    new_node = TrieNode(ltr)
                    curr_node.middle[ltr] = new_node
                    curr_node = curr_node.middle[ltr]
                curr_node.items.add(item)
        
    def isPrefix(self, word):
        curr_node = self.root
        for i,ltr in enumerate(word):
            try:
                curr_node = curr_node.middle[ltr]
            except KeyError:
                return set()
        return curr_node.items
  
class MainHandler(object):
    def __init__(self):
        self.items = {}
        self.trie = Trie()
        
    def add(self, commandData, insertionID):
        '''ADD <type> <id> <score> <data string that contain spaces>'''
        [type_,id_,score,dataStr] = commandData.split(" ",3)
        item = Item(type_,id_,score,dataStr,insertionID)
        self.items[id_] = item
        self.trie.insert(dataStr.lower().split(), item)
        
    def delete(self, command_data):
        '''DEL <id>'''
        itemID = command_data
        item = self.items.pop(itemID, None)
        self.trie.remove(item.dataStr.lower().split(), item)
        
    def query(self, command_data):
        '''QUERY <number of results> <query string that can contain spaces>'''
        [numOfResults, queryStr] = command_data.split(" ",1)
        numOfResults = int(numOfResults)
        queryTokens = queryStr.lower().split(" ")
        #print time.time()
        self._query({}, numOfResults, queryTokens)
        
    def wquery(self, command_data):
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
        #print time.time()
        
        self._query(boosts, numOfResults, queryTokens)

    def _query(self, boosts, numOfResults, queryTokens):
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
                            if value.type == b_key:
                                value = deep_copy(value)
                                value.score *= boost
                        else: #an id is specified
                            value = deep_copy(self.items[b_key])
                            value.score *= boost
                        values[i] = value
        #print time.time()         
        values.sort()
        values = values[:numOfResults]
        if values:
            i = iter(values)
            _ = i.next()
            for item in values:
                try:
                    if i.next():
                        print item.id,
                except StopIteration:
                    print item.id
        else:
            print ""
            
def main():
    lines = sys.stdin.readline().split('\n')
    #lines = inputt.split('\n')
    N = int(lines[0])
    Main = MainHandler()
    add = Main.add
    delete = Main.delete
    query = Main.query
    wquery = Main.wquery
    inserted = 0
    for obj in lines[1:N+1]:
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
    inputt += 'QUERY 10 I\n'
    inputt += 'QUERY 10 girls\n'
    inputt += 'QUERY 10 His\n'
    inputt += 'DEL %s\n' % x[100]
    inputt += 'QUERY 30 I\n'
    boost_ids = [str(i) for i in range(1,22)]
    sub_boost = ''
    for i in range(1,22):
        sub_boost += '%s:'+str(i)+' '
    boosts = ('board:2.0 topic:9.99 user:5.0 %s' % sub_boost) % tuple(boost_ids)
    inputt += 'WQUERY 2 24 %sphone\n' % boosts
    inputt += 'DEL %s\n' % x[888]
    inputt += 'DEL %s\n' % x[900]
    inputt += 'WQUERY 20 1 user:5.6 he can buy most expensive\n'
    inputt += 'DEL %s\n' % x[999]
        
    return inputt


##x=make_input()
##s = time.time()
##main(x)
##e = time.time()
##print '%d' % (e-s)
main()

