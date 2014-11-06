import requests
from functools import partial
from endpoints import ENDPOINTS

TRELLO_URL = 'https://trello.com/'


class TrelloAPI:
    def __init__(self, endpoints, name, apikey, parent=None):
        self._ep = endpoints
        self._arg = None
        self._parent = parent
        self._name = name
        self._apikey = apikey
        for name, content in self._ep.items():
            if name == 'METHODS':
                for method in content:
                    verb = method.lower()
                    setattr(self, verb, partial(self._api_call, verb))
            else:
                setattr(self, name,
                        TrelloAPI(self._ep[name], name, self._apikey, self))

    @property
    def _url(self):
        """
        Resuelve la URL hasta este punto.

        >>> trello = TrelloAPI(ENDPOINTS['TrelloV1'], '1', 'APIKEY')
        >>> trello.batch._url
        '1/batch'
        >>> trello.boards('BOARD_ID')._url
        '1/boards/BOARD_ID'
        >>> trello.boards('BOARD_ID')('FIELD')._url
        '1/boards/BOARD_ID/FIELD'
        >>> trello.boards('BOARD_ID').cards('FILTER')._url
        '1/boards/BOARD_ID/cards/FILTER'

        """
        mypart = '/'.join(filter(None, [self._name, self._arg]))

        if self._parent:
            return '/'.join(filter(None, [self._parent._url, mypart]))
        else:
            return mypart

    def _api_call(self, method, *args, **kwargs):
        if 'params' in kwargs:
            kwargs['params']['key'] = self._apikey
        else:
            kwargs['params'] = {'key': self._apikey}

        method = getattr(requests, method)

        return method(TRELLO_URL + self._url, *args, **kwargs)

    def __call__(self, arg):
        self._arg = str(arg)

        return TrelloAPI(self._ep, None, self._apikey, self)


if __name__ == '__main__':
    TrelloV1 = TrelloAPI(ENDPOINTS['TrelloV1'], '1', 'INSERT_KEY_HERE')
