#!/bin/bash
mkdir -p providers 
curl https://raw.githubusercontent.com/nicolay-r/nlp-thirdgate/refs/heads/master/llm/replicate_104.py -o providers/replicate_104.py
curl https://raw.githubusercontent.com/nicolay-r/nlp-thirdgate/refs/heads/master/text-translation/googletrans_402.py -o providers/googletrans_402.py
curl https://raw.githubusercontent.com/nicolay-r/nlp-thirdgate/refs/heads/master/ner/dp_130.py -o providers/dp_130.py