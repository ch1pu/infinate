# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

We take security seriously. If you discover a security vulnerability in Infinite, please report it responsibly.

### How to Report

**Please DO NOT report security vulnerabilities through public GitHub issues.**

Instead, please report them via one of these methods:

1. **GitHub Security Advisories** (Preferred)
   - Go to the [Security tab](https://github.com/ch1pu/infinate/security/advisories)
   - Click "Report a vulnerability"
   - Fill out the form with details

2. **Email**
   - Send details to the repository maintainer
   - Use a descriptive subject line: "Security Vulnerability Report: [Brief Description]"

### What to Include

Please include the following information:

- Type of vulnerability (e.g., XSS, SQL injection, authentication bypass)
- Location of the affected code (file path and line numbers if possible)
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if available)
- Impact assessment
- Suggested fix (if you have one)

### Response Timeline

- **Initial Response:** Within 48 hours
- **Status Update:** Within 7 days
- **Resolution Target:** Within 30 days (depending on complexity)

### What to Expect

1. **Acknowledgment:** We will acknowledge your report within 48 hours
2. **Assessment:** We will assess the vulnerability and its impact
3. **Updates:** We will keep you informed of our progress
4. **Fix:** We will work on a fix and coordinate disclosure
5. **Credit:** We will credit you in the security advisory (unless you prefer anonymity)

### Safe Harbor

We consider security research conducted in accordance with this policy to be:

- Authorized and not subject to legal action
- Helpful to the security of the project
- Exempt from any bug bounty restrictions

We will not pursue legal action against researchers who:

- Make a good faith effort to avoid privacy violations and data destruction
- Only interact with accounts they own or with explicit permission
- Do not exploit vulnerabilities beyond what is necessary to demonstrate the issue
- Report vulnerabilities promptly and do not disclose publicly until a fix is available

## Security Best Practices for Contributors

When contributing to Infinite, please follow these guidelines:

### Never Commit Secrets

- Use `.env` files for sensitive configuration (already gitignored)
- Use `CHANGE_ME_*` placeholders in examples
- Check your commits for accidental secret exposure

### Dependencies

- Keep dependencies up to date
- Review dependency changes for security implications
- Report any vulnerable dependencies you discover

### Code Review

All code changes undergo security review. Please:

- Follow secure coding practices
- Validate all input
- Use parameterized queries
- Implement proper authentication and authorization

## Security Features

Infinite includes several security features:

- **No hardcoded secrets:** All sensitive values use environment variables
- **Comprehensive .gitignore:** Prevents accidental secret commits
- **Type safety:** mypy strict mode helps prevent type-related vulnerabilities
- **High test coverage:** 90% minimum helps identify untested code paths

## Acknowledgments

We thank the following researchers for responsibly disclosing vulnerabilities:

*No vulnerabilities reported yet.*

---

**Last Updated:** 2026-01-18
