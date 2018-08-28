"""
Copyright (C) 2018 kanishka-linux kanishka.linux@gmail.com

This file is part of Reminiscence.

Reminiscence is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Reminiscence is distributed in the hope that it will be useful, 
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with Reminiscence.  If not, see <http://www.gnu.org/licenses/>.
"""

import os
import re
import nltk
from bs4 import BeautifulSoup
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.tag import pos_tag
from django.conf import settings
from collections import Counter

class Summarizer:
    
    nltk_data_path = settings.NLTK_DATA_PATH
    nltk.data.path.append(nltk_data_path)
    
    @classmethod
    def check_data_path(cls):
        if not os.path.exists(cls.nltk_data_path):
            os.makedirs(cls.nltk_data_path)
            nltk.download(
                [
                    'stopwords', 'punkt',
                    'averaged_perceptron_tagger'
                ], download_dir=cls.nltk_data_path
            )
    
    @classmethod
    def get_summary_and_tags(cls, content, total_tags):
        cls.check_data_path()
        soup = BeautifulSoup(content, 'lxml')
        text = ''
        for para in soup.find_all('p'):
            text = text + '\n' + para.text
        stop_words = set(stopwords.words('english')) 
        word_tokens = pos_tag(word_tokenize(text))
        
        stemmer = PorterStemmer()
        filtered = []
        
        for w in word_tokens:
            if (not w[0].lower() in stop_words and w[0].isalnum()
                    and len(w[0]) > 2
                    and w[1] in set(('NN', 'NNS', 'VBZ', 'NNP'))):
                filtered.append(w[0])

        freq = Counter(filtered)
        tags = freq.most_common(total_tags)
        final_tags = []
        for i, j in enumerate(tags):
            ps = stemmer.stem(j[0])
            ntags = [stemmer.stem(l[0]) for k, l in enumerate(tags) if i != k]
            if ps not in ntags and ps not in stop_words:
                final_tags.append(j[0])
                
        freq_dict = dict(freq)
        sentence = sent_tokenize(text)
        nd = []
        words = 0
        for index, sen in enumerate(sentence):
            w = word_tokenize(sen)
            val = 0
            for j in w:
                val += int(freq_dict.get(j, 0))
            nd.append([index, sen, val])
            words += len(w)
            
        length = int(words/3)
        nsort = sorted(nd, key=lambda x: x[2], reverse=True)
        
        final = []
        s = 0
        for i in nsort:
            w = word_tokenize(i[1])
            final.append(i)
            s += len(w)
            if s > length:
                break
            
        final = sorted(final, key=lambda x: x[0])
        
        sumr = ''
        for i, j in enumerate(final):
            nsum = j[1].strip()
            nsum = re.sub(r' +', ' ', nsum)
            nsum = re.sub(r'\n', '. ', nsum)
            if i == 0:
                sumr = nsum
            else:
                sumr = sumr + '\n\n' +nsum
        
        return sumr.strip(), final_tags
