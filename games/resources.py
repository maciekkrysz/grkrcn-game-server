import unicodedata


def normalize_str(to_normalize):
    return unicodedata.normalize('NFD', to_normalize).encode(
        'ascii', 'ignore').decode()
