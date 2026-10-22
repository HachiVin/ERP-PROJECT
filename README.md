# ERP Dashboard (Proof of Concept)

A multi-page [Streamlit](https://streamlit.io) dashboard for exploring ERP data, built during a
Machine Learning Developer internship. It shows eleven ERP modules (CRM, Sales, Finance,
Inventory, Purchase, Payment, Partners, Products, Credit, HR, GA) as tables and charts, and can
ask a large language model for a short written insight about what it is looking at.

**Live demo:** [ISI: Streamlit app URL]

> **Scope note.** The data is synthetic and follows the Odoo schema, because the company's main
> product runs on Odoo. The AI part is a single call to an LLM that reads only the **first five
> rows** of the selected table. It is an insight generator, not an autonomous agent: it has no
> tools, no memory and no multi-step loop, and it does not analyse the whole dataset.

## Features

- **11 ERP modules, 17 views.** Every module has a table view; CRM and Sales also have six
  matplotlib charts (stage distribution, revenue by salesperson, revenue trend, sales by
  salesperson, sales trend, status distribution).
- **Login with per-user sessions.** Passwords are checked against bcrypt hashes stored in
  Streamlit secrets. There is no self-registration.
- **Per-user AI history.** Each account has its own saved insights, so one user never sees
  another user's results. History is stored as JSON in `ai_logs/`.
- **LLM insight via OpenRouter.** Uses the OpenAI SDK against `https://openrouter.ai/api/v1`.
  Only free models are accepted (see [Free model](#free-model-and-api-key)). Failures are
  shown as readable messages and never saved as if they were insights.
- **Company picker.** Eleven companies are listed; only FisTx has a dashboard so far, the rest
  show a "not built yet" notice.

## Project structure

```
.
├── main.py                    # Entry point: login, then company picker
├── pages/
│   └── dashboard_fistx.py     # FisTx dashboard: module picker, table/chart, AI insight
├── erp_dashboard/             # Application code (no Streamlit logic except ui.py)
│   ├── config.py              # Paths, companies, session keys, AI defaults
│   ├── auth.py                # bcrypt login check, session start/end
│   ├── loaders.py             # JSON -> pandas DataFrame, one loader per module
│   ├── charts.py              # matplotlib figures
│   ├── modules.py             # Registry: module -> loader -> views (table or chart)
│   ├── ai.py                  # OpenRouter client, prompt, per-user history store
│   └── ui.py                  # Theme, header, login guard
├── data/fistx/                # Synthetic Odoo-style JSON data
├── tests/                     # pytest suite (unit + end-to-end with Streamlit AppTest)
├── .streamlit/secrets.toml.example
├── .env.example
├── requirements.txt           # Runtime dependencies (pinned)
└── requirements-dev.txt       # + pytest, ruff
```

Adding a module means adding a loader in `loaders.py` and one entry in `modules.py`; the
dashboard page picks it up without further changes.

## Run locally

Requires Python 3.12 or newer.

```bash
python -m venv .venv
source .venv/bin/activate          # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
```

Then create your configuration (next section) and start the app:

```bash
streamlit run main.py
```

## Configuration

Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` for local runs. On
Streamlit Community Cloud, paste the same content into **Manage app → Settings → Secrets**.
`secrets.toml` and `.env` are git-ignored; never commit real keys or hashes.

```toml
[users]
kevin = "$2b$12$...bcrypt hash..."

[openrouter]
api_key = "sk-or-..."
model = "openai/gpt-oss-20b:free"
```

### Create a login

Accounts are defined only in the secrets. Generate a hash for a password (it is typed
hidden) and add it as `username = "<hash>"` under `[users]`:

```bash
python -c "import bcrypt, getpass; print(bcrypt.hashpw(getpass.getpass().encode(), bcrypt.gensalt()).decode())"
```

Passwords longer than 72 bytes are not supported by bcrypt and are rejected at login.

### Free model and API key

1. Create an API key at [openrouter.ai/keys](https://openrouter.ai/keys).
2. Use a model whose ID ends in `:free`, for example `openai/gpt-oss-20b:free`, or the
   router `openrouter/free`, which picks any currently available free model.
3. Put both in `[openrouter]` as above. For local runs you can instead set the
   `OPENROUTER_API_KEY` and `OPENROUTER_MODEL` environment variables (see `.env.example`);
   they take priority over secrets.

The app refuses to send a request to any other model, so a paid model cannot be used by
accident. Free models are rate limited by OpenRouter (about 20 requests per minute, and a
daily cap that depends on your account's purchased credits), and availability changes over
time, so check the current list and limits in the OpenRouter documentation. If a call fails,
the message shown next to the AI box states the reason (invalid key, no credit, rate limit,
unknown model, network).

Without an API key the dashboard still works; only the AI buttons are hidden.

## Tests

```bash
pytest          # no network access needed
ruff check .
ruff format --check .
```

The suite covers login and session handling, data loaders, charts, the AI client (with a
fake client, including every error path) and the real Streamlit pages end to end.

## Limitations

- The AI sees only the first five rows of a table (`AI_SAMPLE_ROWS` in `config.py`), so its
  text describes that sample, not the full dataset. The prompt and the page both say so.
- AI history is written to `ai_logs/` on the server. On Streamlit Community Cloud this
  storage is temporary and is cleared when the app restarts or is redeployed.
- Only the FisTx dashboard is implemented; the other ten companies are placeholders.
- Accounts are managed in the secrets; there is no registration or admin screen.
- Pinned to Streamlit 1.37.1. Newer releases deprecate `use_container_width`; replace it with
  `width="stretch"` when upgrading.
- The data is synthetic and small. Charts and tables are meant to demonstrate the workflow, not
  to support business decisions.

## Tech stack

Python, Streamlit, pandas, matplotlib, bcrypt, OpenAI SDK (OpenRouter), python-dotenv, pytest,
ruff.
