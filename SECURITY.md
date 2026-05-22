# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 3.0.x   | :white_check_mark: |
| < 3.0   | :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability in Bhisma, please report it responsibly.

**DO NOT** create a public GitHub issue for security vulnerabilities.

Instead, please send an email to: [security@bhisma.dev](mailto:security@bhisma.dev)

Please include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

We will respond within 48 hours and work with you to verify and fix the issue.

## Security Considerations

### API Key Storage
- API keys are stored with AES-256 encryption
- Keys are never logged or transmitted insecurely
- Use environment variables for CI/CD environments

### Network Safety
- Bhisma includes safety gates to prevent attacks on whitelisted networks
- Always obtain explicit written permission before testing
- Use the `--stealth` flag for evasive operations
- Monitor the dashboard for unexpected behavior

### Privilege Requirements
- Monitor mode requires root/administrator privileges
- Some tools require additional system permissions
- Run with minimal required privileges

## Disclosure Policy

We follow a 90-day disclosure timeline:
1. Report received
2. Initial response within 48 hours
3. Fix developed and tested
4. Coordinated disclosure after fix is available

## Acknowledgments

We thank the security researchers who help keep Bhisma safe.
