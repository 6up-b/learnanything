"""Sign in with ChatGPT (token sharing for open-source apps) for the ``chatgpt_plan`` provider.

``store`` keeps the machine-local sign-in (outside every vault), ``oauth`` runs
the PKCE authorization-code flow, ``session`` hands out access tokens and
tracks plan-usage state, and ``responses`` sends one streamed Responses
request. The transport itself is ``learnloop.ai.providers.chatgpt_plan``.
"""
