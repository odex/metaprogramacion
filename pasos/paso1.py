# Comenzamos...
#
# Recodamos **chaining methods** (ya hemos puesto un ejemplo antes)
# pero ahora lo hacemos con vistas a Trello.

class TrelloAPI:

    def __init__(self):
        pass

    def board(self):
        return TrelloAPI()


>>> t = TrelloAPI()
>>> t.board().board()


# Nos ayudamos de **setattr** en la instanciación para ir encadenando
# la clase TrelloAPI dinámicamente mientras recorremos el árbol de EPs.

from functools import partial

from endpoints import ENDPOINTS

class TrelloAPI:

    def __init__(self, endpoints):
        self._ep = endpoints
        for name, content in self._ep.items():
            setattr(self, name, partial(self._api_part, name))

    def _api_part(self, name):
        return TrelloAPI(self._ep[name])


>>> t = TrelloAPI(ENDPOINTS['TrelloV1'])
>>> t.boards().cards().METHODS


# Ahora falta el caso en el que llegamos a una hoja del árbol. Se
# introduce el concepto **getattr**.

from functools import partial

from endpoints import ENDPOINTS

class TrelloAPI:

    def __init__(self, endpoints, apikey):
        self._ep = endpoints
        self._apikey = apikey
        for name, content in self._ep.items():
            if name == 'METHODS':
                for method in content:
                    verb = method.lower()
                    setattr(self, verb, partial(self._api_call, verb))
            else:
                setattr(self, name, partial(self._api_part, name))

    def _api_part(self, name):
        return TrelloAPI(self._ep[name], self._apikey)

    def _api_call(self, method_name, *args, **kwargs):
        kwargs.setdefault('params', {}).update({'key': self._apikey})

        http_method = getattr(requests, method_name)
        return http_method(TRELLO_URL + self._url, *args, **kwargs)


>>> t = TrelloAPI(ENDPOINTS['TrelloV1'], '1')
>>> t.boards().cards().get


# Ahora enseñamos el código final donde se incorpora el método `_url`.

import requests
from functools import partial
from endpoints import ENDPOINTS

TRELLO_URL = 'https://trello.com/'

class TrelloAPI:
    def __init__(self, endpoints, name, apikey, parent=None, arg=None):
        self._ep = endpoints
        self._arg = str(arg) if arg else None
        self._parent = parent
        self._name = name
        self._apikey = apikey
        for name, content in self._ep.items():
            if name == 'METHODS':
                for method in content:
                    verb = method.lower()
                    setattr(self, verb, partial(self._api_call, verb))
            else:
                setattr(self, name, partial(self._api_part, name))

    @property
    def _url(self):
        mypart = '/'.join(filter(None, [self._name, self._arg]))
        if self._parent:
            return '/'.join(filter(None, [self._parent._url, mypart]))
        else:
            return mypart
    
    def _api_part(self, name, arg=None):
        return TrelloAPI(self._ep[name], name, self._apikey, self, arg)
    
    def _api_call(self, method_name, *args, **kwargs):
        kwargs.setdefault('params', {}).update({'key': self._apikey})
    
        http_method = getattr(requests, method_name)
        return http_method(TRELLO_URL + self._url, *args, **kwargs)


>>> t = TrelloAPI(ENDPOINTS['TrelloV1'], '1')
>>> t.boards().cards()._url
