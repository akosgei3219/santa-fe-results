# FluentCRM email audit (read-only)

`fluentcrm_audit.py` pulls the state of our email setup straight from
FluentCRM on santafehalfmarathon.com and prints one report:

- every broadcast with its status and send-from address
- whether the **July 7** campaign actually sent, and whether **Aug 18** and
  **Sept 15** are really scheduled
- subscriber total vs. the expected **1,067** list, with a per-status
  breakdown where the API supports it
- all tags and lists with subscriber counts

It only sends GET requests — it can't change anything in the CRM.

## 1. Make a scoped API key

Don't use your main WordPress password. In wp-admin:

**FluentCRM → Settings → REST API → Add New Key** — name it something like
`Claude audit`. FluentCRM generates a username + password pair that only
works for FluentCRM endpoints.

## 2. Put the pair in environment variables

Keep the key out of files and chat logs — set it in the shell you'll run
the script from:

```powershell
# PowerShell
$env:FLUENTCRM_USER = "generated-username"
$env:FLUENTCRM_KEY  = "generated-password"
```

```bash
# bash / zsh
export FLUENTCRM_USER=generated-username
export FLUENTCRM_KEY=generated-password
```

Optional: `FLUENTCRM_SITE_URL` if the site ever moves (defaults to
`https://santafehalfmarathon.com`).

## 3. Run it

```bash
python fluentcrm_audit.py            # readable report
python fluentcrm_audit.py --json     # raw data if you want to dig
```

Useful flags: `--expect 1067` to change the expected list size,
`--key-dates 2026-07-07 2026-08-18 2026-09-15` to check different send
dates.

## 4. Kill the key

When you're done, go back to **FluentCRM → Settings → REST API** and delete
the `Claude audit` key. The pair stops working immediately.

## Tests

Offline, no credentials needed:

```bash
pytest test_fluentcrm_audit.py
```
