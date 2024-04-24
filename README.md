# Foodgram
## Блог с рецептами

![example workflow](https://github.com/kise2k/foodgram-project-react/actions/workflows/main.yml/badge.svg)

## Описание проекта
Социальная сеть для публикации рецептов. Позволяет выкладывать рецепты, фото готовых блюд, добавлять рецепты в избранное и список покупок.

## Стэк технологий
![Python 3.9](https://img.shields.io/badge/Python-3.9-blue.svg)
![Django 3.2.16](https://img.shields.io/badge/Django-3.2.16-green.svg)
![djangorestframework
3.12.4](https://img.shields.io/badge/djangorestframework-3.12.4-green)

## Другие пакеты и библиотеки
Включены в requirements.txt. Адрес: backend/requirements.txt

### Как запустить проект: 
Клонируйте репозиторий:

```bash
git clone https://github.com/kise2k/foodgram-project-react.git
```
Перейдите в него в командной строке:

```bash
cd foodgram-project-react
```

Cоздайте и активируйте виртуальное окружение:

```bash
python3 -m venv venv 
```

Установите зависимости
```bash
source venv/Scripts/activate
```

Обновите pip и установите зависимости: каждая команда - отдельно
```bash
python -m pip install --upgrade pip
pip install -r backend/requirements.txt
```

В корне проекта создайте файл .env и присвойте значения переменным окружения.

Пример:


POSTGRES_DB=foodgram

POSTGRES_USER=foodgram_user

POSTGRES_PASSWORD=foodgram_password

DB_NAME=foodgram_user

DB_HOST=db

DB_PORT=5432

DEBUG=False

ALLOWED_HOSTS=***.***.**.***,127.0.0.1,localhost,foodramkise2k.zapto.org


Установите [docker](https://www.docker.com/) на свой компьютер.

Запустите проект через docker compose:

```bash
docker compose -f docker-compose.yml up --build -d
```

Выполните миграции:

```bash
docker compose -f docker-compose.yml exec backend python manage.py migrate
```

Соберите статику:

```bash
docker compose -f docker-compose.yml exec backend python manage.py collectstatic
```
Скопируйте статику:
```bash
docker compose -f docker-compose.yml exec backend cp -r /app/collected_static/. /backend_static/static/
```

## Workflow

Для использования Continuous Integration (CI) и Continuous Deployment (CD): в репозитории GitHub Actions Settings/Secrets/Actions создайте Secrets - переменные окружения для доступа к сервисам:


DOCKER_USERNAME                # имя пользователя в DockerHub
DOCKER_PASSWORD                # пароль пользователя в DockerHub
HOST                           # ip_address сервера
USER                           # имя пользователя
SSH_KEY                        # приватный ssh-ключ (cd ~/.ssh/id_rsa)
PASSPHRASE                     # кодовая фраза (пароль) для ssh-ключа

TELEGRAM_TO                    # id телеграм-аккаунта (можно узнать у @userinfobot, команда /start)
TELEGRAM_TOKEN                 # токен бота (получить токен можно у @BotFather, /token, имя бота)


При push в ЛЮБУЮ ветку автоматически отрабатывают сценарии:
* *tests* - проверка кода на соответствие стандарту PEP8.

При push в ветку main автоматически отрабатывают сценарии:
* *build\_and\_push\_to\_docker\_hub* - сборка и доставка докер-образов на DockerHub
* *deploy* - автоматический деплой проекта на боевой сервер. Выполняется копирование файлов из DockerHub на сервер;
* *send\_message* - отправка уведомления в Telegram.

## Примеры запросов и ответов

GET-запрос на эндпойнт 

http://localhost:8000/api/users/1/

дает следующий ответ:

{
  "email": "user@example.com",
  "id": 1,
  "username": "string",
  "first_name": "Вася",
  "last_name": "Пупкин",
  "is_subscribed": false
}


POST-запрос на эндпойнт 

http://localhost:8000/api/auth/token/login/

с телом запроса:

{
  "password": "string",
  "email": "string"
}

дает следующий ответ:

{
  "auth_token": "string"
}

PATCH-запрос на эндпойнт

http://localhost:8000/api/recipes/1123/

с телом запроса:

{
  "ingredients": [
  {
    "id": 1123,
    "amount": 10
  }
],
  "tags": [
    1,
    2
],
  "image": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABAgMAAABieywaAAAACVBMVEUAAAD///9fX1/S0ecCAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAACklEQVQImWNoAAAAggCByxOyYQAAAABJRU5ErkJggg==",
  "name": "string",
  "text": "string",
  "cooking_time": 1
}

дает следующий ответ:

{
  "id": 0,
  "tags": [
    {
      "id": 0,
      "name": "Завтрак",
      "color": "#E26C2D",
      "slug": "breakfast"
    }
  ],
  "author": {
    "email": "user@example.com",
    "id": 0,
    "username": "string",
    "first_name": "Вася",
    "last_name": "Пупкин",
    "is_subscribed": false
  },
  "ingredients": [
    {
      "id": 0,
      "name": "Картофель отварной",
      "measurement_unit": "г",
      "amount": 1
    }
  ],
  "is_favorited": true,
  "is_in_shopping_cart": true,
  "name": "string",
  "image": "http://localhost:8000/media/recipes/images/image.jpeg",
  "text": "string",
  "cooking_time": 1
}


## Данные для входа в админ-зону
адрес: https://foodramkise2k.zapto.org
логин: sedyakin00@bk.ru
пароль: snak4228
## Автор
Данный учебный проект был разработан [yandex-praktikum](https://github.com/yandex-praktikum) и выполнен by kise2k
