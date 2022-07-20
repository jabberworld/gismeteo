## Gismeteo Jabber Weather Transport

* Транспорт для Jabber (XMPP), позволяющий получать данные о погоде с сайта https://gismeteo.ru или https://www.meteonova.ru. За основу взят транспорт, полученный от jabbercity.ru, который, в свою очередь, базируется на коде mail-transport (https://github.com/xmpppy/mail-transport) и погодном плагине для бота Talisman.

## Требования

* python2
* python-xmpppy

Библиотека находится в каталоге транспорта, поэтому, фактически, никаких дополнительных компонентов не требуется. Работа проверялась на Debian 11.

## Установка

* Разместить файлы транспорта в любом удобном каталоге.
* Добавить в конфиг-файл Jabber-сервера описание транспорта. На примере ejabberd:

Старый формат:
```
     {5555, ejabberd_service, [
                              {ip, {127.0.0.1}},
                              {access, all},
                              {shaper_rule, fast},
                              {host, "gismeteo.domain.com", [{password, "superpassword"}]}
                              ]},
```
 Новый формат:
```
    -
      port: 5555
      ip: "127.0.0.1"
      module: ejabberd_service
      access: all
      hosts:
       "gismeteo.domain.com":
         password: "superpassword"
      shaper_rule: fast
```

* В файле config.xml транспорта прописать используемые параметры подключения к Jabber-серверу (название транспорта, IP, порт, пароль), при необходимости поправить остальные параметры.
* Тем или иным способом запустить gism.py (в идеале от отдельного пользователя) - можно в GNU screen или с помощью идущего в комплекте gism.service-файла для systemd. Последний можно разместить в ~/.config/systemd/user/gism.service, далее выполнить:
```
    systemctl --user enable gism.service
    systemctl --user start gism.service
```
* Для автостарта пользовательского service-файла использовать команду:
```
    # loginctl enable-linger username
```

* ...либо все то же самое, но глобально, разместив service-файл в /etc/systemd/system, а в gism.service указать нужные имя и группу пользователя.

## Использование

Открыть браузер сервисов, найти транспорт, нажать "Поиск". В поле поиска ввести название населенного пункта, в результатах поиска выбрать нужную строку и нажать "Добавить контакт". На любое сообщение бот присылает данные о погоде, кроме того, она отображается в статусном сообщении. Бот обновляет информацию о погоде при любом изменении статуса у Jabber-клиента.

----

JabberWorld, https://jabberworld.info