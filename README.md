# Foodgram
«Фудграм» — сайт, на котором пользователи будут публиковать свои рецепты, добавлять чужие рецепты в избранное и подписываться на публикации других авторов.
## Как запустить проект
1. Клонируйте репозиторий к себе на компьютер:
```bash
git clone git@github.com:PolinaTutygina/foodgram.git
```
2. Перейдите в директорию infra:
```bash
cd foodgram/infra
```
3. Создайте файл `.env` в директории `infra` на основе `.env.example`:
```bash
cp .env.example .env
```
4. В директории `infra` запустите проект:
```bash
docker compose up -d
```
5. Выполните миграции:
```bash
docker compose exec backend python manage.py migrate
```
6. Заполните базу ингредиентами:
```bash
docker compose exec backend python manage.py download_ingredients
```
7. Соберите статику:
```bash
docker compose exec backend python manage.py collectstatic --noinput
```
8. Создайте суперпользователя:
```bash
docker compose run --rm backend python manage.py createsuperuser
```
## Доступные адреса
 - [Интерфейс веб-приложения](http://localhost)
 - [Спецификация API](http://localhost/api/docs/)
 - [Админ-панель](http://localhost/admin/)
