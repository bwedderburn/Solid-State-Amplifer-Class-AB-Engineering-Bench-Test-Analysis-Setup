# Security Policy

## Supported Versions

We currently support the following versions of amp-benchkit:

| Version | Supported          |
| ------- | ------------------ |
| 0.3.x   | :white_check_mark: |
| 0.2.x   | :warning: Critical fixes only |
| < 0.2.0 | :x:                |

The 0.3.x development series receives active security updates. Earlier 0.2.x releases may receive critical security fixes at maintainer discretion, but users are encouraged to upgrade to 0.3.x.

## Reporting a Vulnerability

**Please do not open public issues for security vulnerabilities.**

To report a security vulnerability in amp-benchkit, please use GitHub's Private Vulnerability Reporting feature:

1. Navigate to [https://github.com/bwedderburn/amp-benchkit/security/advisories/new](https://github.com/bwedderburn/amp-benchkit/security/advisories/new)
2. Provide a detailed description of the vulnerability, including:
   - Steps to reproduce
   - Affected versions
   - Potential impact
   - Any suggested fixes (if applicable)

### What to Expect

- **Acknowledgment**: We aim to acknowledge receipt of your vulnerability report within 5 business days.
- **Assessment**: We will assess the severity and impact of the reported vulnerability.
- **Remediation**: Depending on severity, we aim to triage and provide a fix within a reasonable timeframe (typically 30 days for high-severity issues, longer for lower severity).
- **Disclosure**: We appreciate coordinated disclosure. We will work with you to determine an appropriate public disclosure timeline after a fix is available.

### Security Contact

We do not provide a dedicated security contact email at this time. All security reports should be submitted through GitHub's Private Vulnerability Reporting system as described above.

For general security questions or concerns that are not vulnerability reports, you may open a public discussion in the repository's Discussions section.

## Security Best Practices

When using amp-benchkit:

- Keep your installation up to date with the latest patches
- Review the CHANGELOG.md for security-related updates
- Follow the principle of least privilege when configuring hardware access
- Validate and sanitize any user inputs in custom automation scripts
- Be cautious when using the tool with untrusted instrument firmware or network-connected devices

## Security Update Process

When a security vulnerability is confirmed and fixed:

1. A security advisory will be published on GitHub
2. The fix will be included in the next patch release
3. The CHANGELOG.md will document the security fix (with appropriate disclosure timing)
4. Users will be notified through GitHub release notes

Thank you for helping keep amp-benchkit and its users secure!
