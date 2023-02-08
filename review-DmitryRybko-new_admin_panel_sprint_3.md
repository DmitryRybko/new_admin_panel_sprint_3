# Review проекта [new_admin_panel_sprint_3](https://github.com/DmitryRybko/new_admin_panel_sprint_3)
* Круто, что ETL процесс идёт в одном скрипте.
* Вот тут [new_admin_panel_sprint_3/etl/main_project/](https://github.com/DmitryRybko/new_admin_panel_sprint_3/tree/main/etl/main_project) конфиги nginx можно собрать в отдельный каталог.
* Вот тут [new_admin_panel_sprint_3/etl/main_project/etl_process/Dockerfile](https://github.com/DmitryRybko/new_admin_panel_sprint_3/blob/main/etl/main_project/etl_process/Dockerfile) хорошо бы сделать так, чтобы копирование py файлов было после pip install, тогда при изменении кода ETL при пересборке контейнера не будут переустанавливаться пакеты.
Также можно разделить логические блоки пустыми строками.
* Не знаю насколько правильно использование cron, но у меня ETL контейнер "падает" при отсутствии данных в postgresql и приходится его (контейнер) перезапускать.
Это говорит о том, что cron работает не так как хочется.
Я видел вот такую статью: https://habr.com/ru/company/redmadrobot/blog/305364/ где говорилось, что cron в докере не самая лучшая идея, так что я делал только sleep в скрипте без крона.
* Вот тут: [etl_process.py:62](https://github.com/DmitryRybko/new_admin_panel_sprint_3/blob/main/etl/main_project/etl_process/etl_process.py#L62) будет больно, если персон будет много.
* Вот тут: [etl_process.py:89](https://github.com/DmitryRybko/new_admin_panel_sprint_3/blob/main/etl/main_project/etl_process/etl_process.py#L89) переменная называется role_**dict**, но (насколько я понял) туда кладётся list.
* Было бы круто использовать дата классы, или именованные tuple, или pydantic, чтобы заменить record[] на что-то читабельнее в [etl_process.py:95](https://github.com/DmitryRybko/new_admin_panel_sprint_3/blob/main/etl/main_project/etl_process/etl_process.py#L95).
* Вот тут: [etl_process.py:146](https://github.com/DmitryRybko/new_admin_panel_sprint_3/blob/main/etl/main_project/etl_process/etl_process.py#L146) можно использовать Python библиотеку для работы с эластиком вместо requests.
* Вот тут: [etl_process.py:216](https://github.com/DmitryRybko/new_admin_panel_sprint_3/blob/main/etl/main_project/etl_process/etl_process.py#L216), мне кажется, стоит проверять наличие индекса перед созданием.
* [etl_process.py:221](https://github.com/DmitryRybko/new_admin_panel_sprint_3/blob/main/etl/main_project/etl_process/etl_process.py#L221) если скрипт упадёт, то сервис завершится. Можно добавить "отлов" всех ошибок и их логирование. Для того, чтобы скрипт завершился можно добавить лимит по времени.
