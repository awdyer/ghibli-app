# Instructions

## Install dependencies
```bash
python -m venv env
env/bin/activate
pip install -r requirements.txt
```

## Run the app
```bash
python -m waitress --port 8000 --call "app.app:get_app"
```

## Run tests
```bash
pytest tests
```

# Roadmap
- log errors
