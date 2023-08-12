Проект «Продуктовый помощник» - это приложение, на котором пользователи публикуют рецепты кулинарных изделий, подписываться на публикации других авторов и добавлять рецепты в избранное. Сервис «Список покупок» позволит пользователю создавать список продуктов, которые нужно купить для приготовления выбранных блюд по рецепту.

## Для ревью:
Адрес сайта: https://yapr.ddns.net
superuser:
           Username: pdy
           Email: pdy@pdy.pdy
           Password: pdy

## Запуск проекта на удаленном сервере:

Клонировать репозиторий:
```bash
git clone git@github.com:pdyakovlev/foodgram-project-react.git
```
Скопировать на сервер файлы docker-compose.yml, default.conf из папки infra
В папке проекта создать файл .env с полями:
```bash
DB_ENGINE=django.db.backends.postgresql
DB_NAME=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
DB_HOST=db
DB_PORT=5432
```
Создать и запустить контейнеры Docker:
```bash
sudo docker compose up -d
```
Создать миграции:
```bash
sudo docker compose exec web python manage.py makemigrations
```

Выполнить миграции:
```bash
sudo docker compose exec web python manage.py migrate
```

Собрать статику:
```bash
sudo docker compose exec web python manage.py collectstatic --noinput
```

Создать суперпользователя:
```bash
sudo docker compose exec web python manage.py createsuperuser
```