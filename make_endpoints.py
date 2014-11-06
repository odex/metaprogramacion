#!/usr/bin/env python
"""
Convierte la documentación de Trello en un módulo de python que contiene
un diccionario anidado con los endpoints y métodos que acepta la API.

"""
from collections import defaultdict
from lxml import html
from pprint import pprint

import requests

TRELLO_API_DOC = 'https://trello.com/docs/api/index.html'
HTTP_METHODS = {'OPTIONS', 'GET', 'HEAD', 'POST', 'PUT', 'DELETE',
                'TRACE', 'CONNECT'}

def _is_url_arg(p):
    """
    Es un argumento que forma parte de la URL.

    >>> _is_url_arg('[idAction]')
    True
    >>> _is_url_arg('actions')
    False

    """
    return p.startswith('[')


def _is_api_definition(line):
    """
    Es una definición de API de Trello.

    >>> _is_api_definition('GET /1/actions/[idAction]')
    True
    >>> _is_api_definition('action')
    False

    """
    return line.split(' ', 1)[0] in HTTP_METHODS


def _camelcase_to_underscore(url):
    """
    Transforma el formato camelCase a formato underscore.

    >>> _camelcase_to_underscore('minutesBetweenSummaries')
    'minutes_between_summaries'

    """
    def upper2underscore(text):
        for letter in text:
            if letter.islower():
                yield letter
            else:
                yield '_'
                if letter.isalpha():
                    yield letter.lower()
    return ''.join(upper2underscore(url))


def create_tree(endpoints):
    """
    Crea el árbol de endpoints de Trello.

    >>> r = {'TrelloV1': { \
                 'actions': {'METHODS': {'GET'}}, \
                 'boards': { \
                     'members': {'METHODS': {'DELETE'}}}} \
            }
    >>> r == create_tree([ \
                 'GET /1/actions/[idAction]', \
                 'DELETE /1/boards/[board_id]/members/[idMember]'])
    True

    """
    tree = {}

    for ep in endpoints:
        # 'GET /1/actions/[idAction]' => ['GET', ['1', 'actions']]
        verb, url = ep.split(' ', 1)
        path = [p for p in url.strip('/').split('/')
                if not _is_url_arg(p)]
        here = tree

        # Primer elemento (Versión de la API).
        cls_name = 'TrelloV' + path[0]
        here.setdefault(cls_name, {})
        here = here[cls_name]

        # Resto de elementos de la URL.
        for p in path[1:]:
            part = _camelcase_to_underscore(p)
            here.setdefault(part, {})
            here = here[part]

        # Métodos HTTP admitidos.
        if not 'METHODS' in here:
            here['METHODS'] = {verb}
        else:
            here['METHODS'].add(verb)

    return tree


def main():
    """
    Convierte la documentación de Trello en un diccionario y lo imprime
    por salida estándar.

    """
    ep = requests.get(TRELLO_API_DOC).content
    root = html.fromstring(ep)

    links = root.xpath('//a/text()')
    endpoints = [ep for ep in links if _is_api_definition(ep)]

    print('ENDPOINTS = ', end='')
    pprint(create_tree(endpoints), compact=True)


if __name__ == '__main__':
    main()
