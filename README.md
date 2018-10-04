## Setup and start

Install docker and docker-compose.

**local** environment - create local config file. It can be used for overriding any field in *build-files/config.json*:
```
cp build-files/config.json build-files/secrets.json
```

Use the google app credentials and copy it to `build-files/secrets.json`.

**local** environment - build
```
docker-compose -f docker-compose.yml build
```

**local** environment - start applications
```
docker-compose -f docker-compose.yml up -d
```

**local** environment - run initial migrations
```
docker exec -it sync-engine_sync-engine-api_1 sh -c 'python ./bin/create-db'
```

Run **production** environment
```
docker-compose -f docker-compose-production.yml up -d
```

Run migrations
```
docker exec -it sync-engine_sync-engine-api_1 sh -c 'alembic -x shard_id=0 upgrade +1'
```

## License

This code is free software, licensed under the The GNU Affero General Public License (AGPL). See the `LICENSE` file for more details.
