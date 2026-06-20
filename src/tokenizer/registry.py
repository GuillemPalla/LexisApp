from src.tokenizer.tokenizers import OnlySportsTokenizer, PythonTokenizer, TinyStoriesTokenizer


TOKENIZER_REGISTRY = {
    "tiny_stories_unk": lambda: TinyStoriesTokenizer("tinystories_vocab_unk.json"),
    "onlysports": lambda: OnlySportsTokenizer(),
    "python_edu": lambda: PythonTokenizer(),
}