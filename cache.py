import pickle
from time import time


class Cache:
    def __init__(self):
        self.Cache = {}

    def read_cache(self, data):
        results = []
        for query in data[1]:
            cached = self.Cache.get((query["Type"], query["Name"]))
            if cached is not None:
                for data in cached:
                    if data[3] + data[0] > time():
                        results.append(cached)
        if results:
            return results
        else:
            return None

    def cache(self, data):
        for answers in [data[2], data[3], data[4]]:
            for answer in answers:
                cached = self.Cache.get((answer["Type"], answer["Name"]))
                if cached is None:
                    self.Cache.update({(answer["Type"], answer["Name"]):
                                           [(answer["TTL"], answer["Length"], answer["Address"], time())]})
                else:
                    if (answer["Address"], answer["TTL"]) not in cached:
                        cached.append((answer["TTL"], answer["Length"], answer["Address"], time()))

    def set_cache(self):
        with open("output.cache", "wb") as f:
            pickle.dump(self.Cache, f)

    def get_cache(self):
        try:
            with open("output.cache", "rb") as f:
                unchecked = pickle.load(f)
                keys = []
                for key in unchecked.keys():
                    for data in unchecked[key]:
                        if data[3] + data[0] < time():
                            keys.append(key)
                            break
                for key in keys:
                    unchecked.pop(key)
                self.Cache = unchecked
        except EOFError:
            pass

