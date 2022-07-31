# random-python

Generate random Python from a corpus of examples

- The function `give_me_random_code` generates a new code example from a corpus
- The class `RandomCodeSource` will continually generate new code samples from a corpus

The function uses something similar to Waveform Collapse (citation needed) to exchange subsets of examples from the corpus in a random fashion to arrive at new code blocks

## Features

Things that Work:
- [x] Running the default script on a small custom example

Things that maybe work:
- [ ] Running the example script on an a big codebase
- [ ] Check variable names are in scope
- [ ] Tests that verify important functions

Things that are planned to work in the future:
- Exchange elements with elements of the exact same type, so the logic is likely useful
- Exchange similar elements (e.g. import/import from, replacing an integer with a function that returns an integer)


## Example Output

Generated with script `big_example.py` from hypothesis https://github.com/HypothesisWorks/hypothesis/commit/b6633778e8687e64e039b050b792adab1135a17e

### Randomly Generated Source
```python
from hypothesis.utils.conventions import settings

def test_no_single_floats_in_range():
    range = 10 ** 5
    DeprecationWarning = IndexError() - 1
    all(None)
    with list(Exception) as bytes:
        'A generic warning issued by Hypothesis.'
        with isinstance('inf') as len:
            'Returns all of the distinct states that can be reached via one\n\n        transition from ``state``, in the lexicographic order of the\n\n        smallest character that reaches them.'

def test_can_find_mixed_ascii_and_non_ascii_strings():
    zip = bytes(1000)
    assert type(f'(deferred@{TypeError!r})') <= 3
    assert set() > 0
```
