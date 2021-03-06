import re
import json
from collections import defaultdict

class DistantSupervisor:
    def __init__(self, input_file, criterion):
        self.input_filename = input_file
        self.criterion = criterion
        # self.criteria = [criterion]
        self.criterion_type = self.criterion.name
        # self.criterion_types = [criterion.name for criterion in self.criteria]
        self.output_filenames = ['{}-{}-{}.json'.format(self.input_filename.split('.json')[0], self.criterion.name, category)
                                 for category in self.criterion.categories]
        self.output_fs = dict()
        self.counts = defaultdict(int)

    def run(self, append_evidence=False, print_progress=True):
        self.open_output_files()

        with open(self.input_filename) as input_f:
            for line in input_f:
                line = line.strip()
                try:
                    tweet = json.loads(line)

                    if all(['text' in tweet, 'lang' in tweet, tweet['lang'] == 'en', 'retweeted_status' not in tweet]):

                        if append_evidence:
                            category, evidence = self.criterion.categorise(tweet['text'])

                            if category is not None:
                                tweet['evidence'] = evidence
                                self.output_fs[category].write(json.dumps(tweet) + '\n')
                                self.counts['total'] += 1
                                self.counts[category] += 1
                        else:
                            category = self.criterion.categorise(tweet['text'], return_evidence=False)

                            if category is not None:
                                self.output_fs[category].write(json.dumps(tweet) + '\n')
                                self.counts['total'] += 1
                                self.counts[category] += 1

                        if print_progress:
                            print('{} {}'.format(self.input_filename, self.criterion_type) +
                                  ', '.join([' -{}: {}'.format(category, count) for category, count in self.counts.items()]),
                                  end='\r')
                except:
                    continue

        print('{} {}'.format(self.input_filename, self.criterion_type) +
              ', '.join([' -{}: {}'.format(category, count) for category, count in self.counts.items()]))

        self.close_output_files()

    def open_output_files(self):
        for filename, category in zip(self.output_filenames, self.criterion.categories):
            self.output_fs[category] = open(filename, 'w')

    def close_output_files(self):
        for output_f in self.output_fs.values():
            output_f.close()


class Criterion:
    def __init__(self, **kwargs):
        self.name = kwargs.get('name', 'Dummy')
        self.categories = kwargs.get('categories', [])
        self.num_of_categories = len(self.categories)

    def categorise(self, tweet, return_evidence=True):
        raise NotImplementedError


class GroupCriterion(Criterion):
    def __init__(self, list_of_criteria, **kwargs):
        super().__init__()
        assert all([isinstance(list_of_criteria, list),
                   all(isinstance(c, Criterion) for c in list_of_criteria)])
        categories = list_of_criteria[0].categories
        assert all(c.categories == categories for c in list_of_criteria[1:])
        self.criteria = list_of_criteria
        self.categories = categories

        self.mode = kwargs.get('mode', 'any')
        self.name = kwargs.get('name', 'Group')
        assert self.mode in ['all', 'any']

    def categorise(self, tweet, return_evidence=True):

        if self.mode == 'any':
            tweet_category = None
            if return_evidence:
                all_evidence = list()
                for criterion in self.criteria:
                    category, evidence = criterion.categorise(tweet)
                    if evidence is None:   # if there is a contradiction within any criterion.
                        return None, None  # TODO: there is no equivalence of this for not use_evidence yet.
                    if category is not None:
                        if tweet_category not in [None, category]:
                            return None, None
                        tweet_category = category
                        all_evidence = all_evidence + evidence

                return tweet_category, all_evidence

            else:
                for criterion in self.criteria:
                    category = criterion.categorise(tweet)
                    if category is not None:
                        if tweet_category not in [None, category]:
                            return None
                        tweet_category = category
                    break

                return tweet_category

        elif self.mode == 'all':
            tweet_category = None
            if return_evidence:
                all_evidence = list()
                for criterion in self.criteria:
                    category, evidence = criterion.categorise(tweet)
                    if evidence is None:   # if there is a contradiction within any criterion.
                        return None, None  # TODO: there is no equivalence of this for not use_evidence yet.
                    if category is None or tweet_category not in [None, category]:
                        return None, None
                    tweet_category = category
                    all_evidence = all_evidence + evidence

                return tweet_category, all_evidence

            else:
                for criterion in self.criteria:
                    category = criterion.categorise(tweet)
                    if category is None or tweet_category not in [None, category]:
                        return None, None
                    tweet_category = category

                return tweet_category


class KeywordCriterion(Criterion):
    def __init__(self, keywords, **kwargs):
        super().__init__()

        self.name = kwargs.get('name', 'Keyword')
        self.keyword_mode = kwargs.get('keyword_mode', 'in')
        assert self.keyword_mode in ['in', 'split', 'regex']
        if kwargs.get('consider_surrounding', False):
            self.keyword_mode = 'regex'

        if self.keyword_mode == 'regex':
            self.keywords = dict()
            self.orig_keywords = dict()
            for category in keywords.keys():
                regexes = list()
                for keyword in keywords[category]:
                    regex = process_string_keyword(keyword)
                    regexes.append(regex)
                    self.orig_keywords[regex] = keyword
                self.keywords[category] = regexes
        else:
            self.keywords = keywords

        self.categories = list(self.keywords.keys())
        self.num_of_categories = len(self.categories)

    def _keyword_in_tweet(self, keyword, tweet):
        if self.keyword_mode == 'regex':
            return re.search(keyword, tweet) is not None
        elif self.keyword_mode == 'split':
            return keyword in tweet.split()
        else:
            return keyword in tweet

    def _get_orig_keyword(self, keyword):
        if self.keyword_mode == 'regex':
            return self.orig_keywords[keyword]
        else:
            return keyword

    def categorise(self, tweet, return_evidence=True):
        tweet_category = None
        if return_evidence:
            evidence = list()
            for category in self.categories:
                for keyword in self.keywords[category]:
                    if self._keyword_in_tweet(keyword, tweet):
                        if tweet_category not in [None, category]:
                            return None, None
                        tweet_category = category
                        evidence.append(self._get_orig_keyword(keyword))

            return tweet_category, evidence

        else:
            for category in self.categories:
                for keyword in self.keywords[category]:
                    if self._keyword_in_tweet(keyword, tweet):
                        if tweet_category not in [None, category]:
                            return None
                        tweet_category = category
                        break

            return tweet_category


def process_string_keyword(string):
    escaped = re.escape(string)
    return "(\s|\A)" + escaped + "(\s|\Z)"


