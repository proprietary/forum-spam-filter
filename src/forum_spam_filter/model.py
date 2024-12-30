from transformers import DistilBertTokenizer

checkpoint = "distilbert-base-uncased"


tokenizer = DistilBertTokenizer.from_pretrained(checkpoint)
