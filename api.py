import requests
from functools import partial
from endpoints import ENDPOINTS

TRELLO_URL = 'https://trello.com/'

class TrelloAPI:
    def __init__(self, endpoints, name, key, parent=None, arg=None):
        self._ep = endpoints
        self._arg = str(arg) if arg else None
        self._parent = parent
        self._name = name
        self._key = key
        for name, content in self._ep.items():
            if name == 'METHODS':
                for method in content:
                    verb = method.lower()
                    setattr(self, verb, partial(self.__api_call, verb))
            else:
                setattr(self, name, partial(self.__api_part, name))

    @property
    def _url(self):
        """
        Resuelve la URL hasta este punto.
        
        >>> trello = TrelloAPI(ENDPOINTS['TrelloV1'], '1', 'APIKEY')
        >>> trello.batch()._url
        '1/batch'
        >>> trello.boards('BOARD_ID')._url
        '1/boards/BOARD_ID'
        >>> trello.boards('BOARD_ID').cards('FILTER')._url
        '1/boards/BOARD_ID/cards/FILTER'

        """
        mypart = '/'.join(filter(None, [self._name, self._arg]))
        if self._parent:
            return '/'.join(filter(None, [self._parent._url, mypart]))
        else:
            return mypart

    def __api_part(self, name, arg=None):
        return TrelloAPI(self._ep[name], name, self._key, self, arg)

    def __api_call(self, method, *args, **kwargs):
        if 'params' in kwargs:
            kwargs['params']['key'] = self._key
        else:
            kwargs['params'] = {'key': self._key}

        method = getattr(requests, method)

        return method(TRELLO_URL + self._url, *args, **kwargs)

if __name__ == '__main__':
    TrelloV1 = TrelloAPI(ENDPOINTS['TrelloV1'],
                         '1',
                         'INSERT_KEY_HERE')
