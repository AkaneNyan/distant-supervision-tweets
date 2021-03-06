import sys
import json

# lower case, remove new lines, remove evidence

input_filename = sys.argv[1]
output_filename = '{}-cleaned.txt'.format(input_filename.split('.')[0])

with open(input_filename, 'r') as fi, open(output_filename, 'w+', encoding='utf8') as fo:
    for line in fi:
        line = line.strip()
        tweet = json.loads(line)
        text = tweet['text']
        evidence_list = tweet['evidence']
        for evidence in evidence_list:
            text = text.replace(evidence, '')
        text = ' '.join(text.split())
        text = text.lower()
        text = text.strip()
        fo.write(text + '\n')

print('finished writing to {}'.format(output_filename))
            

