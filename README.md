### 1. Usage

1. Clone repository.
2. Sync uv with `uv sync` command.
3. Go to the directory with the microservice `charts_service` and perform `uv sync` there.
4. Activate venv with `source .venv/bin/activate' command.
5. Apply migrations with `alembic upgrade head` command.
6. Add `certs` folder to the root.
7. Generate two files with keys inside the `certs` folder using the RS256 algorithm: `private_key.pem` & `public_key.pem`.
8. Rename `.env.dev.example` in the root folder to `env.dev`.
9. Rename `.env.dev.example` to `charts_service` to `env.dev`.
10. Run `charts_service` with the `uv ru charts_service/app/main.py ` command.
11. Launch the main application using the module `app/main.py `.
12. Enjoy!