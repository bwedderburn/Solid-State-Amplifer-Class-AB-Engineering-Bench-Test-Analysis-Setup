# Signing & Commit Signature Verification

This repository enforces (or encourages) signed commits for provenance and supply chain integrity. A prior private key was **removed from history** via a forced rewrite after accidental inclusion. Treat any previously exposed key as compromised.

## Current Status

- History rewrite performed to purge `private-key-backup.asc` (sensitive PGP private key).
- Tags were force-updated (v0.3.1+). Collaborators must resync (see below).
- A new signing key should now be generated locally by each maintainer who signs releases.

## Generate a New GPG Key

Interactive (recommended):

```bash
gpg --full-generate-key
# Choose: (1) RSA and RSA, 4096 bits, 1y expiry (extendable)
```

List and capture the LONG key ID:

```bash
gpg --list-secret-keys --keyid-format LONG
```

Export public key and add to GitHub (Settings → SSH and GPG keys → New GPG key):

```bash
KEYID=YOURKEYIDHERE
gpg --armor --export "$KEYID"
```

Configure git to sign by default:

```bash
git config --global user.signingkey "$KEYID"
git config --global commit.gpgsign true
git config --global gpg.program gpg
```

Create a test signed commit:

```bash
git commit --allow-empty -m "chore: test signed commit (new key)"
git log --show-signature -1
```

## Revocation Certificate

Generate immediately and store **outside** the repository:

```bash
gpg --output revoke-${KEYID}.asc --gen-revoke "$KEYID"
```

If compromise occurs:

```bash
gpg --import revoke-${KEYID}.asc
gpg --keyserver hkps://keys.openpgp.org --send-keys "$KEYID"
```

## Secure Backup (Do Not Commit)

```bash
gpg --armor --export-secret-keys "$KEYID" > private-key-backup-${KEYID}.asc
chmod 600 private-key-backup-${KEYID}.asc
# Move this file to an encrypted vault / password manager attachment.
```

## History Rewrite Notes

A destructive rewrite removed the accidentally committed private key. Collaborators must resynchronize:

```bash
git fetch origin
git checkout main
git reset --hard origin/main
git fetch --tags --force
```

If local divergent work existed, back it up first:

```bash
git branch backup-pre-rewrite
```

## Optional: Secret Scanning Pre-Commit

Install `detect-secrets` (optional defense in depth):

```bash
pip install detect-secrets
detect-secrets scan > .secrets.baseline
```

Add to `.pre-commit-config.yaml`:

```yaml
- repo: https://github.com/Yelp/detect-secrets
	rev: v1.5.0
	hooks:
		- id: detect-secrets
			args: ["--baseline", ".secrets.baseline"]
```

## Policy Recommendations

- Never commit any `*private*` key material.
- Generate revocation certificates at key creation time.
- Rotate keys annually or at suspicion of compromise.
- Use hardware-backed keys (YubiKey) for higher assurance when possible.

---
Last updated after security remediation & key rotation guidance.
