# AppMetrica Funnels

Funnels based on AppMetrica events.

## How to use this image

To use this image you should generate [OAuth token](https://tech.yandex.com/appmetrica/doc/mobile-api/intro/authorization-docpage/) for [AppMetrica Logs API](https://tech.yandex.com/appmetrica/doc/mobile-api/logs/about-docpage/). This token should be provided via environment variable `TOKEN`.

Also you should copy app's numeric IDs. You could find them in General Settings of your app ("Application ID"). All IDs should be provided as JSON-array via environment variable `API_KEYS`.

### Start manualy
```bash
$ docker run -d --name clickhouse --ulimit nofile=262144:262144 yandex/clickhouse-server
$ docker run -d --name appmetrica-funnels --link clickhouse -p 5000:5000 -e 'CH_HOST=http://clickhouse:8123' -e 'TOKEN=YOUR_OAUTH_TOKEN' -e 'API_KEYS=["YOUR_APP_ID"]' yandex/appmetrica-funnels
```

More information about [ClickHouse server image](https://hud.docker.com/r/yandex/clickhouse-server).

### Start with Docker Compose
Download this repository and edit `docker-compose.yml` file with your Yandex OAuth Token and list of app IDs. Then run:
```bash
$ docker-compose up -d
```

## Configuration

Container exposes 5000 port for Web UI.
Environment variables:
* `TOKEN` - *(required)* Logs API OAuth token.
* `API_KEYS` - *(required)* JSON-array of numeric AppMetrica app identifiers.
* `CH_HOST` - host of ClickHouse DB to store events. (default: `http://localhost:8123`)
* `CH_USER` and `CH_PASSWORD` - login/password of ClickHouse DB. (default: empty)
* `LOGS_API_FETCH_INTERVAL` - Interval of time in seconds between events fetches from Logs API. (default: 43200 aka 12 hours)
* `LOGS_API_HISTORY_PERIOD` - Days count for the first events fetch. (default: 30)
* `FLASK_PORT` - Port for Web UI. (default: 5000)

## License
License agreement on use of Yandex AppMetrica is available at [EULA site][LICENSE]


[LICENSE]: https://yandex.com/legal/metrica_termsofuse/ "Yandex AppMetrica agreement"
