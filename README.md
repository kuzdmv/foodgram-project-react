![example workflow](https://github.com/kuzdmv/foodgram-project-react/actions/workflows/foodgram_workflow.yml/badge.svg)
# praktikum_new_diplom
# Проект Foodgram
## Описание
Проект для обмена рецептами среди пользователей.

### Автор проекта:
- Дмитрий Кузнецов 
https://github.com/kuzdmv

### Развертывание проекта локально:
```
Для развертывния проекта локально, из дерриктории infra/
Заменяем файл docker-compose и nginx в infra/ из infra/local/

Далее из дерриктории infra/ необходимо выполнить команду:
docker-compose up -d --build

Далее выполнить миграции:
docker-compose exec web python manage.py makemigrations
docker-compose exec web python manage.py migrate

Создать суперпользователя:
docker-compose exec web python manage.py createsuperuser

Сбор статики:
docker-compose exec web python manage.py collectstatic --no-input

Проект юуде доступен по ссылке:
http://localhost/

```
### Развернутый проект доступен по ссылкам:
```
http://62.84.121.38/
http://62.84.121.38/admin/
http://62.84.121.38/api/docs/
```
### Данные на администратора:
```
username - admin
email - admin@mail.ru
password - pass1900
```

