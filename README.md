# 🗂️ Flashcard App

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](#-license)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![codecov](https://codecov.io/github/ScotRossman/flashCards/graph/badge.svg?token=GEPWWJL3B5)](https://codecov.io/github/ScotRossman/flashCards)
A Python flashcard application for studying and retaining information, starting with a terminal interface and designed to grow into a GUI and web app.

---

## 📑 Table of Contents

- [Features](#-features)
- [Quick Start](#-quick-start)
- [Usage](#-usage)
- [Project Structure](#-project-structure)
- [Development](#-development)
- [Continuous Integration](#-continuous-integration)
- [Roadmap](#-roadmap)
- [License](#-license)

---

## 🚀 Features

- **Interactive terminal study sessions:** create, review, and manage flashcards from the command line.
- **Streamlit web UI:** practice math flashcards and view database-backed practice statistics.
- **React web UI:** frontend scaffold for a separate browser-based interface; implementation is planned.
- **Installable command:** installs a `flashcards` command via the project's console-script entry point.
- **Editable installs:** code changes take effect on the next run without reinstalling.
- **Automated quality checks:** formatting with `black`, tests with `pytest` and `pytest-cov`.
- **CI pipeline:** GitHub Actions validates every push and pull request to `dev`, with coverage reported to Codecov.

---

## ⚡ Quick Start

**Requirements:** Python 3.10 or newer and `git`.

```bash
# 1. Clone the repository
git clone https://github.com/ScotRossman/flashCards.git
cd flashCards

# 2. Create and activate a virtual environment
python -m venv .venv

# Windows (PowerShell)
.\.venv\Scripts\Activate.ps1
# macOS / Linux
source .venv/bin/activate

# 3. Install the app with development tools (editable mode)
python -m pip install --upgrade pip
pip install -e ".[dev]"
pip install pytest-cov

# 4. Run it
flashcards
```

> **Tip:** if the `flashcards` command isn't found, make sure your virtual environment is activated, or run the module directly with `python -m flashcardApp.main`.

---

## 💻 Usage

Launch the app from anywhere inside your activated environment:

```bash
flashcards
```

Because the project is installed in editable mode (`pip install -e`), edit the code in your IDE and simply re-run the command to see your changes.

### Run the Streamlit web UI

Install the web dependencies and start Streamlit from the repository root:

```powershell
pip install -e ".[web]"
streamlit run src/flashcardApp/web.py
```

The Streamlit UI calls the deployed API Gateway and Lambda backend. Lambda
connects to the `flashcards` schema on the `flashcard-1` RDS MySQL instance;
the local UI does not need direct database credentials or an RDS tunnel.

### Streamlit backend and deployment notes

Streamlit sends player creation/lookups and completed-session writes to the
Lambda API. The Lambda function connects to the `flashcards` schema on the
`flashcard-1` RDS instance.

The app includes a **Database & stats** screen. It displays aggregate practice
statistics, up to 100 player records, and up to 100 recent sessions. This screen
is public, so names and practice records are visible to anyone who can access
the app.

Before deploying the Lambda changes:

```powershell
.\terraform\build_lambda.ps1
Set-Location .\terraform
terraform plan -var 'db_secret_arn=<Secrets Manager secret ARN>' -var 'lambda_subnet_ids=["<subnet-id-a>","<subnet-id-b>"]' -var 'rds_security_group_id=<RDS security group ID>'
```

For GitHub Actions deployment, add these as repository variables under
**Settings → Secrets and variables → Actions → Variables**:

- `DB_SECRET_ARN`: the Secrets Manager secret ARN.
- `LAMBDA_SUBNET_IDS`: a JSON array of subnet IDs in the RDS VPC, such as
  `["subnet-abc123","subnet-def456"]`.
- `RDS_SECURITY_GROUP_ID`: the ID of the RDS security group to allow inbound
  MySQL connections from the Lambda's dedicated security group.
- `COGNITO_USER_POOL_ID`: the Cognito user pool ID that authenticates React
  users.
- `COGNITO_APP_CLIENT_ID`: the public Cognito app client ID (without a client
  secret) used by the React app.

The deployment workflow maps these to Terraform's `TF_VAR_*` inputs and checks
that all are set before applying. Create the Cognito user pool and public app
client before deploying this configuration. These values are identifiers, not passwords;
the database username and password remain in Secrets Manager.

The secret must contain JSON keys `username` and `password`. The Terraform
configuration creates a dedicated Lambda security group, a Secrets Manager
interface VPC endpoint in the Lambda subnets, and a TCP 3306 ingress rule on
the selected RDS security group. Interface endpoints incur hourly and data
processing charges. The Lambda execution role receives permission to read only
the configured secret. Use a MySQL user limited to the `flashcards` schema,
not the RDS master account.

Streamlit POST requests use the IAM-authorized `/streamlit/flashcard` route.
Grant the Streamlit identity `execute-api:Invoke` on the ARN printed by the
`streamlit_player_api_invoke_arn` Terraform output. React uses the separate
JWT-authorized `/flashcard` POST route. For Streamlit Community Cloud, add the
identity's credentials under **App → Settings → Secrets**:

The Lambda POST action `get_player_stats` accepts a positive `player_id` and
returns that player's lifetime totals and totals grouped by practice type. It
returns `404` when the player ID is not found. It is available on either
protected POST route.

To see the API actions supported by the deployed Lambda, request
`GET <API_URL>?action=capabilities`, replacing `<API_URL>` with the API URL
above. The response lists each action's HTTP method, authorization requirement,
purpose, and parameters. This endpoint describes the public API operations; it
does not expose internal Lambda implementation details.

```toml
[aws]
aws_access_key_id = "AKIA..."
aws_secret_access_key = "..."
# Include this only when using temporary credentials.
aws_session_token = "..."
```

Create a dedicated IAM identity for the app and attach a policy like this,
replacing the `Resource` value with the exact
`streamlit_player_api_invoke_arn` Terraform output:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "execute-api:Invoke",
      "Resource": "arn:aws:execute-api:us-east-1:<account-id>:<api-id>/$default/POST/streamlit/flashcard"
    }
  ]
}
```

Create an access key for that identity and put it only in Streamlit's Secrets
settings. Do not use personal administrator credentials. Access keys are
long-lived unless rotated; rotate or revoke them if exposed. The app signs POST
requests using SigV4; set `API_AWS_REGION` if the API is not in `us-east-1`.
Locally, the app can continue to use Boto3's default credential chain if no
`[aws]` secrets are configured. No local RDS credentials or SSM tunnel are
needed for Streamlit database writes.

---

### React web UI (planned)

The `frontend/` directory is the starting structure for a React frontend. It is
currently a scaffold; React dependencies, application components, and hosting
configuration have not yet been added. The intended hosting direction is a
static frontend host such as AWS Amplify Hosting, calling the existing API
Gateway/Lambda backend. Before the browser UI makes protected write requests,
design browser-appropriate API authorization; never put AWS access keys or
database credentials in frontend code. See the [AWS Amplify Hosting
guide](https://docs.aws.amazon.com/amplify/latest/userguide/welcome.html).

## 🧱 Project Structure

```text
flashCards/
├── frontend/                 # React UI scaffold (implementation planned)
│   ├── public/
│   └── src/
│       ├── app/
│       ├── components/
│       ├── features/
│       │   ├── practice/
│       │   └── stats/
│       ├── services/
│       └── types/
├── src/
│   └── flashcardApp/         # Python CLI, Streamlit UI, Lambda handler, and database code
├── terraform/                # API Gateway, Lambda, and RDS connectivity infrastructure
├── tests/                    # pytest test suite
├── pyproject.toml            # Python packaging, dependencies, and tool configuration
└── README.md
```

---

## 🛠️ Development

### Dependencies

| Group        | Install command            | Contents                                       |
| ------------ | -------------------------- | ---------------------------------------------- |
| Core         | `pip install -e .`         | `click`, `pydantic`                            |
| Dev          | `pip install -e ".[dev]"`  | `pytest`, `black`, `flake8`, `boto3`            |
| Streamlit UI | `pip install -e ".[web]"`  | `streamlit`, `PyMySQL`, `boto3`                |
| React UI     | Not set up yet             | React toolchain and dependencies are not added |

### Run the tests

```bash
pytest --cov=./src --cov-report=xml
```

**Tests hang?** Interactive menu prompts can wait for input while `pytest` captures output. Disable capturing and enable verbose mode to see where it's waiting:

```bash
pytest --cov=./src --cov-report=xml -v -s
```

### Check and apply formatting

```bash
black --check src/ tests/   # verify only
black src/ tests/           # auto-format
```

### Lint

```bash
flake8 src/ tests/
```

---

## 🤖 Continuous Integration

GitHub Actions runs on every push and pull request to the `dev` branch:

1. **Formatting:** `black --check` enforces a consistent style.
2. **Testing:** the full `pytest` suite runs.
3. **Coverage:** reports upload to [Codecov](https://codecov.io) so you can track code health over time.

---

## 🗺️ Roadmap

- [x] Command-line interface
- [x] Streamlit web UI
- [ ] React web UI
- [ ] Host the React UI and configure browser-safe API authorization
- [ ] Raise test coverage across `main.py` and `operations.py`

---

## 📄 License

Released under the [MIT License](https://opensource.org/licenses/MIT).

---

*Built by Scot Rossman as a hands-on Python learning project.*
