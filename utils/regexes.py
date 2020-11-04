emoticon_regex = r"""(\s|\A)(?:[<>]?[:;=8][\-o\*\']?[\)\]\(\[dDpP/\:\}\{@\|\\]|[\)\]\(\[dDpP/\:\}\{@\|\\][\-o\*\']?[:;=8][<>]?|<3)(\s|\Z)"""

url_regex = r"""https?:\/\/\S+\b|www\.(\w+\.)+\S*"""

username_regex = r"""(?:@[\w_]+)"""

word_or_punct_regex = r"\w+|[^\w\s]+"
