# Optional email integration (not enabled)

Email needs a provider login and an internet connection. The app currently does not read or send email because credentials and provider details have not been configured. A safe integration should:

1. Use a dedicated app password or OAuth token with the narrowest available mail scope.
2. Store secrets in an untracked local `.env` or OS keychain, never in Git.
3. Fetch only when you explicitly request inbox access.
4. Show the exact recipient, subject, and body, then require a separate confirmation before sending.
5. Keep email content out of logs and model prompts unless you explicitly request a summary or draft.

For Gmail, use Google's OAuth flow rather than your account password. For other providers, use their documented OAuth or app-password flow. This prototype's browser server has no authentication; do not expose it to an untrusted network.
