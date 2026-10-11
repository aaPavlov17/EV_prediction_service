# Пункт 1

- успешный прогон: https://github.com/aaPavlov17/EV_prediction_service/actions/runs/38141985488
- пакет: https://github.com/aaPavlov17/EV_prediction_service/pkgs/container/ev_prediction_service/1369091933?tag=sha-b7806304c62a059521f914904487c91ea882b943

# Пункт 2

- красный и зеленый прогоны: https://github.com/aaPavlov17/EV_prediction_service/pull/1

# Пункт 3

- Конфиг
    Сломал конфиг: https://github.com/aaPavlov17/EV_prediction_service/actions/runs/38146942213
    Починил: https://github.com/aaPavlov17/EV_prediction_service/actions/runs/38147370754
    Как понять: видно, что падает на деплое, кубернетес не смог запустить образ, нужно смотреть в манифест deployment при дебаге
- Секрет
    Сломал секрет: https://github.com/aaPavlov17/EV_prediction_service/actions/runs/38150860628
    Починил: https://github.com/aaPavlov17/EV_prediction_service/actions/runs/38150883169
    Как понять: CreateContainerConfigError в статусе пода
- Ресурсы
    Сломал память: https://github.com/aaPavlov17/EV_prediction_service/actions/runs/38147875871
    Починил: https://github.com/aaPavlov17/EV_prediction_service/actions/runs/38147899255
    Как понять: буквально строчка The Deployment "postgres" is invalid: spec.template.spec.containers[0].resources.requests: Invalid value: "9223372036854775807": must be less than or equal to memory limit of 256Mi

# Пункт 4

Ответы на вопросы:
1. В первй раз - 1 минуты 33 сек (https://github.com/aaPavlov17/EV_prediction_service/actions/runs/38055188787/job/114222176103), во второй - 42 секунды (https://github.com/aaPavlov17/EV_prediction_service/actions/runs/38058574282/job/114232095595). Берутся слои установки зависимости тк они занимают больше всего времени
2. Потому что сначала приименябтся манифесты с образом, который указан в там, но если он недоступен, то поды получают такой статус. Потом ci меняет его на рабочий и прогон проходит
3. Пароль из хранилища на гитхабе попадает в переменную окружения, а потом появляется в окружении кластера, как секрет. Нельзя чтобы пароль попал в код, поэтому его кладут в гитхаб
4. Тогда у нас сбилдится нерабочая потенциально версия кода и в прод попадут баги. Например баги в бизнес логике и тд, которые не проверяют смоук тесты
5. За это отвечает if: github.ref == 'refs/heads/main', это сделано, чтобы сборка лишний раз не происходила в побочных веткахх проекта, это логично делать только из мейн ветки
6. Имеется в виду реплики базы данных в подах, если это не прописать, то в целом ничего не сломается, но тогда при одновременных запросах состояние бд в репликах может не сойтись
7. ErrImagePull - не смогли получить образ, CreateContainerConfigError - получили образ, но не смогли собрать конфиг, CrashLoopBackOff - контейнер запустился, но крашнулся, в нашем случае бд не захотела стартовать без пароля

# Журнал проблем

Падал ci тестов из-за ruff, также сначала ruff вообще неправильно работал, тк написал roof вместо ruff, не совпадало название секрета в гитхабе и в пайплайне
