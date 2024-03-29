import sys
from collections import OrderedDict
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
    def __init__(self, itemType, itemID, score, dataStr, insertion_id):
        self.itemType = itemType
        self.itemID = itemID
        self.score = float(score)
        self.dataStr = dataStr
        #self.trie = Trie()
        #for word in dataStr.lower().split(" "):
        #self.trie.add(set(dataStr.lower().split(" ")), self)
        self.insertion_id = insertion_id

    def __repr__(self):
        info = (self.itemType, self.itemID, self.score, self.dataStr)
        return "Item(type:%r, id:%r, score:%f, data string:%r)" % info
        
    def __cmp__(self,other):
        comp = cmp(self.score, other.score)
        if comp == 0:
            # newer items, which
            # are initially put into the list of results, rank higher
            return -1 * cmp(self.insertion_id, other.insertion_id)
        elif comp == -1:
            return 1
        else:
            return -1

    def foundToken(self, word):
        return self.trie.isPrefix(word)

class Trie(object):
    def __init__(self):
        self.root = {}
        self.items = {}

    def __repr__(self):
        return self.root
    
    def add(self, word, item):
        curr_vertex = self.root
        for i,ltr in enumerate(word):
            #print curr_vertex, ltr
            try:
                curr_vertex = curr_vertex[ltr][0]
            except KeyError:    
##                    if i == len(word) - 1:
##                        curr_vertex[ltr] = curr_vertex.get(ltr, []) + [item]
##                    else:
                curr_vertex[ltr] = [{}]
                #print curr_vertex,'\n\n'   
                curr_vertex = curr_vertex[ltr][0]
                    
    def isPrefix(self, word):
        curr_node = self.root
        for ltr in word:
            branch = curr_node.get(ltr, None)
            if branch is None:
                return False
            else:
                curr_node = branch[0]
        return True
        
class OrdDict(object):
    def __init__(self):
        self.words = Trie()
        self.items = {}

    def add(self, words, item):
        for word in words:
            #self.words.add(word, item)
            pass
        
    def add_command(self, commandData, insertionID):
        [itemType,itemID,score,dataStr] = commandData.split(" ",3)
        item = Item(itemType,itemID,score,dataStr,insertionID)
        self.items[itemID] = item

        self.add(set(dataStr.lower().split(" ")), item)
        
    def delete_command(self, command_data):
        itemID = command_data
        self.items.pop(itemID, None)
        
    def query_command(self, command_data):
        #print 'Beginning to query......',command_data
        [numOfResults, queryStr] = command_data.split(" ",1)
        numOfResults = int(numOfResults)
        queryTokens = queryStr.lower().split(" ")
        
        self.query({}, numOfResults, queryTokens)
        
    def wquery_command(self, command_data):
        #print 'Beginning to wquery....'
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
        
        self.query(boosts, numOfResults, queryTokens)

    def query(self, boosts, numOfResults, queryTokens):
        results = []
        results_found = 0

        types = ['user','topic','question','board']

        deep_copy = copy.deepcopy

        for key in self.items:
            value = self.items[key]

            if boosts:
                for b_key in boosts.keys():
                    for boost in boosts[b_key]:
                        if b_key in types:
                            if value.itemType == b_key:
                                value = deep_copy(value)
                                value.score *= boost
                        else: #an id is specified
                            value = deep_copy(self.items[b_key])
                            value.score *= boost

            noneUnfound = False
            for token in queryTokens:
                if not value.foundToken(token):
                    noneUnfound = True
            if not noneUnfound:
                results += [value]
                results_found += 1
        
        results.sort()
        results = results[:numOfResults]
        if results:
            i = iter(results)
            _ = i.next()
            for item in results:
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
    Dict = OrdDict()
    add = Dict.add_command
    delete = Dict.delete_command
    query = Dict.query_command
    wquery = Dict.wquery_command
    inserted = 0
    for obj in lines[1:-1]: #last element will be '',first element is N
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
    #print Dict.words.root
    


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
        
##    inputt += 'DEL %s\n' % x[0]
##    inputt += 'QUERY 10 His\n'
##    inputt += 'QUERY 10 girls\n'
##    inputt += 'QUERY 10 His\n'
##    inputt += 'DEL %s\n' % x[100]
##    inputt += 'QUERY 30 I\n'
##    inputt += 'WQUERY 2 1 topic:9.99 phone\n'
##    inputt += 'DEL %s\n' % x[888]
##    inputt += 'DEL %s\n' % x[900]
##    inputt += 'WQUERY 20 1 user:5.6 he can buy most expensive\n'
##    inputt += 'DEL %s\n' % x[999]
        
    return inputt


x=make_input()
s = time.time()
main(x)
e = time.time()
print '%d' % (e-s)
#main()

