from helper.slug import slugify


def label_for(value: str) -> str:
    return slugify(value)
