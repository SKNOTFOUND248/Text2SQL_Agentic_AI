import dspy 


lm = dspy.LM(
    "ollama_chat/qwen3:4b-instruct",
    api_base="http://localhost:11434",
    api_key=""
)

dspy.configure(lm=lm)