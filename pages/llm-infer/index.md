---
hide:
  - toc
---

# llm-infer

One client for OpenAI, Anthropic, Google and any OpenAI-compatible server, with routing,
cross-provider fallback, retries and rate limiting; plus `llm-infer serve`, which puts local
models behind one OpenAI-compatible endpoint.
{ .lw-lead }

<div class="grid cards" markdown>

-   :lucide-book-open:{ .lw-card-icon }

    **[Usage guide](usage.md)**

    Running `llm-infer serve`: setup, CLI commands, the OpenAI SDK against it, tuning and
    debugging.

-   :lucide-settings:{ .lw-card-icon }

    **[Configuration](config.md)**

    The server's configuration: backend selection, engine configs, API and request settings.

-   :lucide-compass:{ .lw-card-icon }

    **[Architecture](architecture.md)**

    The server's layers and engine backends, a request's lifecycle, memory and batching.

-   :lucide-braces:{ .lw-card-icon }

    **[API reference](reference/index.md)**

    Every public module, class and function, generated from the source at the release tag.

</div>

Source: [llm-works/llm-infer](https://github.com/llm-works/llm-infer)
