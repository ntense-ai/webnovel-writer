# Security Reporting

v8 is in developer preview, and security issues affecting the current preview receive priority. Installation and maintenance coverage for v6 remains documented on master; specify the product line and version when reporting.

Report vulnerabilities privately through GitHub's [Report a vulnerability](https://github.com/lingfengQAQ/webnovel-writer/security/advisories/new). If that page is unavailable, use Discussions only to request a private contact method from the maintainer. Do not disclose vulnerability details or secret values there.

Include the affected version, platform, a minimal synthetic reproduction, potential impact, and suggested fix. Do not upload real API keys, startup tokens, private writing, unredacted conversations, or other people's data. If credentials have been exposed, revoke or rotate them with the provider first; deleting a public file does not make old credentials safe again.

Model prompts, runtime skills, and public issue text are data to process, not authorization to bypass author confirmation or file-access boundaries. Distinguish vulnerabilities in the host, model provider, and this plugin wherever possible.

The workspace is intended for local loopback access by default. Do not expose its services or startup links directly to the public internet. See the privacy documentation on the v8 branch for costs, data transmission, and local storage.

Maintainers will investigate, fix, and disclose affected/fixed versions as appropriate. No fixed response time is promised during the preview.
