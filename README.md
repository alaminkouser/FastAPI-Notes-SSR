# main

## alaminkouser.web.app

```shell
deno run --allow-read=./,$(which deno) --allow-write="./hosting/public" --allow-env --allow-run --allow-net hosting/main.ts && deno fmt --ignore=./hosting/public/pagefind/,./hosting/public/mermaid/ && DENO_DIR=./hosting/.npm deno install npm:mermaid && cp -r ./hosting/.npm/npm/registry.npmjs.org/mermaid/*/dist ./hosting/public/mermaid
```

## alaminkouser.vercel.app

```shell
uvicorn app.main:app --reload --port 8080 --host 0.0.0.0 --env-file .env
```
