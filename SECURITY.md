# Security

SXS Control is a local automation tool with the invoking user's permissions. It is not an isolation boundary. PowerShell, launching applications, registry writes and desktop input can affect the computer beyond file-tool `allowed_roots`.

Use only authorized computers and trusted local clients. Keep client-side approval for actions with side effects. Prefer stdio. Do not proxy the HTTP endpoint to a network interface. The required fixed local header and Host/Origin checks block ordinary browser cross-site calls; they do not authenticate or isolate other local processes. HTTP request actions are serialized inside one server instance; separate CLI processes are not mutually isolated.

Desktop accessibility labels can change after a UI update. Refresh a snapshot before acting. File path checks resolve symlinks but do not prevent every race with another local process changing files at the same time.

For a security-sensitive finding, contact the maintainer through the GitHub profile or repository private reporting if it is enabled. Do not assume private reporting is enabled. Do not post working credentials or sensitive exploit details in a public issue. Non-sensitive defects may be reported as ordinary GitHub issues.

Version 0.1.0 is an alpha release. No formal security audit, code signing or guaranteed support period is claimed.

