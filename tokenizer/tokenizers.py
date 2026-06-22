from abc import abstractmethod
import json
from pathlib import Path
import sys

from tokenizers import Tokenizer
from transformers import GPT2Tokenizer

def resolve_asset_path(relative_path: str) -> Path:
    """
    Dynamically finds assets whether running in a live dev environment
    or inside a frozen PyInstaller executable.
    """
    # PyInstaller creates a temporary folder and stores its path in sys._MEIPASS
    if hasattr(sys, '_MEIPASS'):
        return Path(sys._MEIPASS) / relative_path
    
    # Dev environment fallback (relative to your project root)
    return Path(__file__).parent / relative_path

class BaseTokenizer:
    @abstractmethod
    def encode(self, text: str):
        pass

    @abstractmethod
    def decode(self, tokens):
        pass

    @property
    def vocab_size(self):
        pass

    @property
    def eot_token(self):
        pass

    @property
    def pad_token(self):
        pass


class TinyStoriesTokenizer(BaseTokenizer):
    def __init__(self, vocab_filename="tinystories_vocab.json"):
        self._base = GPT2Tokenizer.from_pretrained("EleutherAI/gpt-neo-125M", clean_up_tokenization_spaces=False)

        vocab_path = resolve_asset_path(vocab_filename)

        with open(vocab_path) as f:
            data = json.load(f)

        # int keys for fast lookup
        self._new_to_old: dict[int, int] = {int(k): v for k, v in data["new_to_old"].items()}
        self._old_to_new: dict[int, int] = {int(k): v for k, v in data["old_to_new"].items()}

        # For unknown token handling
        self._use_unk = data.get("use_unk", False)
        self._unk_id = data.get("unk_token_id")

    def _encode_single(self, base_id: int) -> list[int]:
        """
        Map one base(gpt-neo) token ID to reduced vocab.
        If token is not in vocab, split to character level, or return unk token if we are in unk mode.
        """
        if base_id in self._old_to_new:
            return [self._old_to_new[base_id]]

        # If we are in UNK mode, return the designated UNK token
        if self._use_unk and self._unk_id is not None:
            return [self._unk_id]
        
        # Token not in vocab: decode to string and re-encode character by character
        token_str = self._base.decode([base_id])
        result = []
        for char in token_str:
            char_ids = self._base.encode(char)
            for c_id in char_ids:
                if c_id in self._old_to_new:
                    result.append(self._old_to_new[c_id])
                else:
                    # This should never trigger
                    pass
        return result

    def encode(self, text: str) -> list[int]:
        base_ids = self._base.encode(text)
        result = []
        for base_id in base_ids:
            result.extend(self._encode_single(base_id))
        return result

    def decode(self, tokens: list[int]) -> str:
        decoded_parts = []
        for t in tokens:
            if t == self._unk_id:
                decoded_parts.append("[UNK]")
            else:
                decoded_parts.append(self._base.decode([self._new_to_old[t]]))
        return "".join(decoded_parts)

    @property
    def vocab_size(self) -> int:
        return len(self._new_to_old)
    
    @property
    def eot_token(self) -> int:
        return self._old_to_new.get(50256, 0)
    
    @property
    def pad_token(self):
        return self._old_to_new.get(50256, 0)


class OnlySportsTokenizer(BaseTokenizer):
    def __init__(self):
        path = resolve_asset_path("onlysports_vocab.json")
        self.enc = Tokenizer.from_file(str(path))

    def encode(self, text: str) -> list[int]:
        return self.enc.encode(text).ids

    def decode(self, tokens: list[int]) -> str:
        return self.enc.decode(tokens)

    @property
    def vocab_size(self) -> int:
        return self.enc.get_vocab_size()

    @property
    def eot_token(self) -> int:
        return self.enc.token_to_id("<|endoftext|>")

    @property
    def pad_token(self) -> int:
        return self.enc.token_to_id("<|pad|>")


class PythonTokenizer(BaseTokenizer):
    def __init__(self):
        path = resolve_asset_path("python_vocab.json")
        self.enc = Tokenizer.from_file(str(path))

    def encode(self, text: str) -> list[int]:
        return self.enc.encode(text).ids

    def decode(self, tokens: list[int]) -> str:
        return self.enc.decode(tokens)

    @property
    def vocab_size(self) -> int:
        return self.enc.get_vocab_size()

    @property
    def eot_token(self) -> int:
        return self.enc.token_to_id("<|endoftext|>")

    @property
    def pad_token(self) -> int:
        return self.enc.token_to_id("<|pad|>")