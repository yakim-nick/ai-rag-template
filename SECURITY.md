# Security Policy

## Supported Versions

| Version | Supported          |
|---------|--------------------|
| latest  | :white_check_mark: |

## Reporting a Vulnerability

If you believe you have found a security vulnerability:

- **Do not** open a public issue describing it.
- Report it privately by email or through GitHub's Security Advisories
  ("Report a vulnerability") flow on this repository.
- Include a description of the issue, how to reproduce it, and the affected
  version.

You will receive a response within 5 business days, and we will coordinate a
fix before disclosing details publicly.

## Security considerations

- This is a RAG template: it ingests documents and evaluates LLM responses.
  Treat ingested content and model output as untrusted.
- Never commit real API keys, model credentials, or dataset secrets. Use
  environment variables or a secret manager.
- Review the `.github/workflows` configuration for secret handling before
  enabling CI on a fork or shared environment.
