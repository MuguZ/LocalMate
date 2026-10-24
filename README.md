# LocalMate

A local-first personal assistant powered by Ollama. It runs on your computer and serves a responsive web app that you can open on your iPhone over your home network.

## Privacy defaults

- Chat requests go only to the configured Ollama URL (default `http://127.0.0.1:11434`).
- The app makes no internet requests unless you explicitly use **Search the web**.
- Email is optional and only accessed through the email actions you request. Sending is gated by an explicit confirmation.
- Never expose this server directly to the public internet. It has no user accounts or remote authentication yet.

## Run

1. Install [Ollama](https://ollama.com/) and download a model, for example `ollama pull qwen2.5:3b`.
2. From this directory run `python3 app.py`.
3. On this computer open `http://127.0.0.1:8765`.
4. To use it on your iPhone, connect both devices to the same trusted Wi-Fi, run `python3 app.py --host 0.0.0.0`, then open `http://<computer-lan-ip>:8765` on the phone. Use Safari's Share → Add to Home Screen.

The app can be installed as a PWA. Service worker caching is only for the interface shell; conversations are not cached by the service worker.

## Configuration

Environment variables: `OLLAMA_URL`, `OLLAMA_MODEL`, `LOCALMATE_HOST`, `LOCALMATE_PORT`. Defaults are `http://127.0.0.1:11434`, `qwen2.5:3b`, `127.0.0.1`, and `8765`.

Web search uses DuckDuckGo HTML only after you press **Search the web**. Search terms are sent to that provider. The search result text is treated as untrusted context.

Email access is not configured by default. See `docs/email.md` before adding credentials. Email sending requires an explicit confirmation in the app. This initial version does not connect to SMS, iMessage, WhatsApp, or other messaging accounts; those need provider-specific credentials and APIs.

## Limitations

This is an initial personal-use prototype, not an internet-facing multi-user service. iPhone access requires your computer to be on and reachable on the same local network. Remote access should be added only with authentication and a secure tunnel. Keep credentials out of the repository.
