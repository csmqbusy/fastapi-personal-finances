### 💭 About

A personal finance management tool for tracking income, spendings, and savings goals, with built-in analytics and a modular microservice architecture.
***

##### ✨ Key Features:
• **Transaction management:** Record income/spendings, categorize transactions, and filter them flexibly.  
• **Savings goals:** Set and track progress toward financial targets.  
• **Data visualization:** Interactive charts (via `charts_service`) for spending/income trends.  
• **CSV export:** Download transaction history for external analysis.  
• **Web interface:** Demo frontend (`Jinja2` + `Bootstrap` + `JS`) with full API-backed functionality.  
• **Auth:** Secure JWT-based authentication and authorization.  
• **Async microservices:** Decoupled `charts_service` communicating via RabbitMQ.  
***

##### 🛠️ Tech Stack
• **Backend:** `FastAPI` for core logic and chart generation.  
• **Database:** `PostgreSQL` for persistent storage.  
• **Messaging:** `RabbitMQ` for inter-service communication.  
• **Frontend:** Server-rendered templates (`Jinja2`) + dynamic `JS/Bootstrap`.  
• **Testing:** Extensive test coverage with `factoryboy` for fixtures.  
***

##### ⚡ Architecture Highlights
• **Modular design:** Core app and `charts_service` run independently.  
• **API-first:** All features accessible via RESTful endpoints.
***

### 🪲 Usage
1. Clone repository.  
2. Sync uv with `uv sync` command.  
3. Go to the `charts_service` directory and perform `uv sync` there.  
4. Activate venv with `source .venv/bin/activate` command.  
5. Apply migrations with `alembic upgrade head` command.  
6. Add `certs` folder to the root.  
7. Generate two files with keys inside the `certs` folder using the `RS256` algorithm: `private_key.pem` & `public_key.pem`.  
8. Rename `.env.dev.example` in the root folder to `env.dev`.  
9. Rename `.env.dev.example` to `charts_service` to `env.dev`.  
10. Run `charts_service` with the `uv ru charts_service/app/main.py ` command.  
11. Launch the main application using the module `app/main.py `.  
12. Enjoy!  
***

### 👀 Frontend overview
![frontend_overview](https://github.com/user-attachments/assets/1299f0bc-c7d6-4d9e-a27f-177e82a24d7a)

***
### 👀 API overview
<img width="1000" alt="api overview" src="https://github.com/user-attachments/assets/32d884df-641a-4a4d-ace4-16d3819d3019" />

***