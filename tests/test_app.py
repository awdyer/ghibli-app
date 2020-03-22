import time
import re
from unittest.mock import MagicMock

import pytest
import falcon.testing

from app.app import MoviesService, create_app


def strip_tags(text):
    return re.sub('<[^<]+?>|\\s+', '', text)


@pytest.fixture
def mock_ghibli_api():
    return MagicMock()


class TestMoviesService:

    @pytest.fixture
    def movies_service(self, mock_ghibli_api):
        return MoviesService(ghibli_api=mock_ghibli_api)

    def test_get_ghibli_movies_no_movies_returns_empty_list(
        self,
        mock_ghibli_api,
        movies_service
    ):
        mock_ghibli_api.get_films.return_value = []

        assert movies_service.get_ghibli_movies() == []

    def test_get_ghibli_movies_no_people_returns_no_people(
        self,
        mock_ghibli_api,
        movies_service
    ):
        mock_ghibli_api.get_films.return_value = [
            {'id': '1', 'title': 'AAA'},
            {'id': '2', 'title': 'BBB'},
        ]
        mock_ghibli_api.get_people.return_value = []

        assert movies_service.get_ghibli_movies() == [
            {'id': '1', 'title': 'AAA', 'people': []},
            {'id': '2', 'title': 'BBB', 'people': []},
        ]

    def test_get_ghibli_movies_with_people_returns_expected(
        self,
        mock_ghibli_api,
        movies_service
    ):
        mock_ghibli_api.get_films.return_value = [
            {'id': '1', 'title': 'AAA'},
            {'id': '2', 'title': 'BBB'},
            {'id': '3', 'title': 'CCC'},
        ]
        mock_ghibli_api.get_people.return_value = [
            {'name': 'Person 1', 'films': ['abc/xyz/1']},
            {'name': 'Person 2', 'films': ['def/xyz/2']},
            {'name': 'Person 3', 'films': ['abc/xyz/1', 'def/xyz/2']},
            {'name': 'Person 4', 'films': ['def/xyz/2']},
            {'name': 'Person 5', 'films': ['abc/xyz/9']},
        ]

        assert movies_service.get_ghibli_movies() == [
            {
                'id': '1',
                'title': 'AAA',
                'people': ['Person 1', 'Person 3']
            },
            {
                'id': '2',
                'title': 'BBB',
                'people': ['Person 2', 'Person 3', 'Person 4']
            },
            {
                'id': '3',
                'title': 'CCC',
                'people': []
            },
        ]

    def test_get_ghibli_movie_caches_result(
        self,
        mock_ghibli_api,
        movies_service
    ):
        mock_ghibli_api.get_films.return_value = []
        mock_ghibli_api.side_effect = time.sleep(0.2)

        movies_service.get_ghibli_movies()

        start = time.monotonic()
        movies_service.get_ghibli_movies()

        assert time.monotonic() - start < 0.2


class TestMoviesRequest:

    @pytest.fixture
    def client(self, mock_ghibli_api):
        movies_service = MoviesService(ghibli_api=mock_ghibli_api)
        api = create_app(movies_service)
        return falcon.testing.TestClient(api)

    def test_get_movies_returns_movies(self, client, mock_ghibli_api):
        mock_ghibli_api.get_films.return_value = [
            {'id': '1', 'title': 'AAA'},
            {'id': '2', 'title': 'BBB'},
            {'id': '3', 'title': 'CCC'},
        ]
        mock_ghibli_api.get_people.return_value = [
            {'name': 'Person 1', 'films': ['abc/xyz/1']},
            {'name': 'Person 2', 'films': ['def/xyz/2']},
            {'name': 'Person 3', 'films': ['abc/xyz/1', 'def/xyz/2']},
            {'name': 'Person 4', 'films': ['def/xyz/2']},
            {'name': 'Person 5', 'films': ['abc/xyz/9']},
        ]

        response = client.simulate_get('/movies')
        result = strip_tags(response.text)

        assert 'AAA' in result
        assert 'Person1Person3' in result
        assert 'BBB' in result
        assert 'Person2Person3Person4' in result
        assert 'CCC' in result
        assert 'Person5' not in result
