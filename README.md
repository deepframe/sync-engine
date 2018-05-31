## Setup and start

Install docker and docker-compose.

**local** environment - create local config file. It can be used for overriding any field in *build-files/config.json*:
```
cp build-files/config.json build-files/secrets.json
```

**local** environment - build
```
docker-compose -f docker-compose.yml build
```

**local** environment - start applications
```
docker-compose -f docker-compose.yml up -d
```

**local** environment - run migrations
```
docker exec -it syncengine_sync-engine-api_1 sh -c 'python ./bin/create-db'
```

Run **production** environment
```
docker-compose -f docker-compose-production.yml up -d
```

## License

This code is free software, licensed under the The GNU Affero General Public License (AGPL). See the `LICENSE` file for more details.
