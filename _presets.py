MODELS = [
    "meta/llama-3.3-70b-instruct",
    "mistralai/mistral-small-3.1-24b-instruct-2503",
    "mistralai/mistral-large-3-675b-instruct-2512",
    "deepseek-ai/deepseek-v3.2"
]

PARAM_SETS = [
    {"name": "proposed", "temp": 0.15, "top_p": 0.70},
    {"name": "strict", "temp": 0.01, "top_p": 0.10},
    {"name": "baseline", "temp": 0.90, "top_p": 0.95},
    {"name": "chaotic", "temp": 1.50, "top_p": 1.00},
]