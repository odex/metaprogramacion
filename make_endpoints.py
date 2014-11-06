#!/usr/bin/env python
"""
Convierte la documentación de Trello en un módulo de python que contiene
un diccionario anidado con los endpoints y métodos que acepta la API.

"""
from base64 import b64encode
from collections import defaultdict
from lxml import html
import gzip
import re

from html2text import html2text
from lxml import etree
import requests
import yaml

TRELLO_API_DOC = 'https://trello.com/docs/api/'
HTTP_METHODS = {'OPTIONS', 'GET', 'HEAD', 'POST', 'PUT', 'DELETE',
                'TRACE', 'CONNECT'}
EP_DESC_REGEX = re.compile(
    '.*({methods})\s([\/a-zA-Z0-9\[\]\s_]+).*'.format(
        methods='|'.join(HTTP_METHODS)))

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
        for char in text:
            if char.islower():
                yield char
            else:
                yield '_'
                if char.isalpha():
                    yield char.lower()
    return ''.join(upper2underscore(url))


def create_tree(endpoints):
    """
    Crea el árbol de endpoints de Trello.

    >>> r = {'1': { \
                'boards': { \
                    '_board_id_': { \
                        'members': { \
                            '_id_member_': {'METHODS': [['DELETE', 'doc2']]} \
                        } \
                    } \
                }, \
                'actions': { \
                   '_id_action_': {'METHODS': [['GET', 'doc1']]} \
                } \
            }}
    >>> r == create_tree([ \
                 ('GET', '/1/actions/[idAction]', 'doc1'), \
                 ('DELETE', '/1/boards/[board_id]/members/[idMember]', 'doc2')])
    True

    """
    tree = {}

    for method, url, doc in endpoints:
        path = [p for p in url.strip('/').split('/')]
        here = tree

        # Primer elemento (Versión de la API).
        version = path[0]
        here.setdefault(version, {})
        here = here[version]

        # Resto de elementos de la URL.
        for p in path[1:]:
            part = _camelcase_to_underscore(p)
            here.setdefault(part, {})
            here = here[part]

        # Métodos HTTP admitidos.
        if not 'METHODS' in here:
            here['METHODS'] = [[method, doc]]
        else:
            if not method in here['METHODS']:
                here['METHODS'].append([method, doc])

    return tree


def main():
    """
    Convierte la documentación de Trello en una estructura de datos y la
    imprime por salida estándar.

    """
    ep = requests.get(TRELLO_API_DOC).content
    root = html.fromstring(ep)

    links = root.xpath('//a[contains(@class, "reference internal")]/@href')
    pages = [requests.get(TRELLO_API_DOC + u)
             for u in links if u.endswith('index.html')]

    endpoints = []
    for page in pages:
        root = html.fromstring(page.content)
        sections = root.xpath('//div[@class="section"]/h2/..')
        for sec in sections:
            ep_html = etree.tostring(sec).decode('utf-8')
            ep_text = html2text(ep_html).splitlines()
            match = EP_DESC_REGEX.match(ep_text[0])
            if not match:
                continue
            ep_method, ep_url = match.groups()
            ep_text[0] = ' '.join([ep_method, ep_url])
            ep_doc = b64encode(gzip.compress('\n'.join(ep_text).encode('utf-8')))
            endpoints.append((ep_method, ep_url, ep_doc))

    print(yaml.dump(create_tree(endpoints)))


if __name__ == '__main__':
    main()
