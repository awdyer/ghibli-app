import os
from collections import defaultdict

import falcon
import requests
import requests.exceptions
import jinja2
import cachetools.func


def load_template(name):
    path = os.path.join(os.path.dirname(__file__), 'templates', name)
    with open(os.path.abspath(path), 'r') as fp:
        return jinja2.Template(fp.read())


class GhibliApiError(Exception):
    pass


class GhibliApi:

    _base_url = 'https://ghibliapi.herokuapp.com'

    def get_films(self):
        return self._get_json('/films')

    def get_people(self):
        return self._get_json('/people')

    def _get_json(self, path):
        try:
            r = requests.get(self._base_url + path)
            r.raise_for_status()
            return r.json()
        except (requests.exceptions.RequestException, ValueError) as e:
            raise GhibliApiError('An error occurred querying the Ghibli API') from e


class MoviesService:

    def __init__(self, ghibli_api):
        self._ghibli_api = ghibli_api

    @cachetools.func.ttl_cache(ttl=60)
    def get_ghibli_movies(self):
        movies = self._ghibli_api.get_films()
        people = self._ghibli_api.get_people()

        movie_people = defaultdict(list)
        for person in people:
            for film in person['films']:
                movie_id = film.split('/')[-1]
                movie_people[movie_id].append(person['name'])

        for movie in movies:
            movie['people'] = movie_people.get(movie['id'], [])

        return movies


class MoviesResource:

    def __init__(self, movies_service):
        self._movies_service = movies_service

    def on_get(self, req, resp):
        movies = self._movies_service.get_ghibli_movies()
        template = load_template('movies.j2')
        resp.content_type = falcon.MEDIA_HTML
        resp.body = template.render(movies=movies)


def create_app(movies_service):
    app = falcon.API()
    app.add_route('/movies', MoviesResource(movies_service=movies_service))
    return app


def get_app():
    ghibli_api = GhibliApi()
    movies_service = MoviesService(ghibli_api=ghibli_api)
    return create_app(movies_service)
