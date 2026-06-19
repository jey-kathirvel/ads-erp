install:

    pip install -r requirements.txt

run:

    uvicorn main:app --reload

lint:

    flake8 .

format:

    black .

test:

    pytest

docker:

    docker compose up --build
