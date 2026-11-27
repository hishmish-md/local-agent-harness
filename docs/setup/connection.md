# Connecting Windows Hermes to a notebook

**Decision: keep the service local if Hermes needs a private HTTP endpoint.** A hosted Colab notebook and your Windows PC are separate machines. `127.0.0.1` in a notebook cell reaches the Colab VM; the same address in Windows Hermes reaches Windows. A successful request inside the notebook proves only the first path works. Neither a private notebook sharing link nor an API token changes routing. Leave the hosted notebook out of Hermes's provider configuration.

| Goal | No-purchase option | Limit |
|---|---|---|
| Use an HTTP service from Windows Hermes | Run the compatible service on your own Windows machine, bound only to `127.0.0.1`. Check its documented health or model-list endpoint from Windows before configuring Hermes. | Uses your hardware, not a Colab GPU. No firewall opening needed. |
| Use hosted compute interactively | If your account is authorized, review and run cells in the Colab notebook yourself; download only the outputs you intend to bring back. | Manual handoff, not a live connection. Don't upload credentials. |
| Use the Colab UI with local compute | Google's [local runtimes guide](https://research.google.com/colaboratory/local-runtimes.html) connects the browser to a runtime on your PC. | This is the opposite direction from accessing a hosted port. Run only trusted notebooks: cells can read, modify or delete local files. |

Google also documents a [Colab MCP server](https://github.com/googlecolab/colab-mcp) for agents working with notebook cells. Notebook tools are not a private HTTP address for a model server. Do not use them as a request relay or as an alternative way to access an age-restricted feature.

## Account and runtime rules

Checked November 27, 2026. The [Colab FAQ](https://research.google.com/colaboratory/faq.html) requires an 18+ Google account for **Colab's AI features**. That is not a blanket age rule for ordinary notebooks. For a school account, the administrator controls Colab access, and the school must obtain parental consent for students under 18. If access is disabled or eligibility is unclear, stay local; do not borrow an account or change a birth date.

The [Colab terms](https://research.google.com/colaboratory/tos_v6.html) require Google-authorized access. The FAQ disallows remote proxies and unrelated web-service hosting on managed runtimes; on free runtimes without a positive compute-unit balance it also disallows remote control such as SSH and using a separate web UI as the primary interface. Do not expose or forward the notebook port, use a tunnel, or purchase compute to make this setup work. No hosted connection is required for the Windows-only option.
