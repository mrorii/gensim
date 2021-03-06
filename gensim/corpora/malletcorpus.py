#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Licensed under the GNU LGPL v2.1 - http://www.gnu.org/licenses/lgpl.html

"""
Corpus in Mallet format of List-Of-Words.
"""

from __future__ import with_statement

import logging

from gensim import utils
from gensim.corpora import LowCorpus


logger = logging.getLogger('gensim.corpora.malletcorpus')

class MalletCorpus(LowCorpus):
    """
    Quoting http://mallet.cs.umass.edu/import.php:

        One file, one instance per line
        Assume the data is in the following format:

        [URL] [language] [text of the page...]

    Or, more generally,
        [document #1 id] [label] [text of the document...]
        [document #2 id] [label] [text of the document...]
        ...
        [document #N id] [label] [text of the document...]

    Note that language/label is *not* considered in Gensim.

    """
    def __init__(self, fname, id2word=None, metadata=False):
        self.metadata = metadata
        LowCorpus.__init__(self, fname, id2word)

    def _calculate_num_docs(self):
        with utils.smart_open(self.fname) as fin:
            result = sum([1 for x in fin])
        return result

    def __iter__(self):
        """
        Iterate over the corpus at the given filename.

        Yields a bag-of-words, a.k.a list of tuples of (word id, word count), based on the given id2word dictionary.
        """
        with utils.smart_open(self.fname) as f:
            for line in f:
                yield self.line2doc(line)

    def line2doc(self, line):
        l = [word for word in utils.to_unicode(line).strip().split(' ') if word]
        docid, doclang, words = l[0], l[1], l[2:]

        doc = super(MalletCorpus, self).line2doc(' '.join(words))

        if self.metadata:
            return doc, (docid, doclang)
        else:
            return doc


    @staticmethod
    def save_corpus(fname, corpus, id2word=None, metadata=False):
        """
        Save a corpus in the Mallet format.

        The document id will be generated by enumerating the corpus.
        That is, it will range between 0 and number of documents in the corpus.

        Since Mallet has a language field in the format, this defaults to the string '__unknown__'.
        If the language needs to be saved, post-processing will be required.

        This function is automatically called by `MalletCorpus.serialize`; don't
        call it directly, call `serialize` instead.

        """
        if id2word is None:
            logger.info("no word id mapping provided; initializing from corpus")
            id2word = utils.dict_from_corpus(corpus)

        logger.info("storing corpus in Mallet format into %s" % fname)

        truncated = 0
        offsets = []
        with utils.smart_open(fname, 'wb') as fout:
            for doc_id, doc in enumerate(corpus):
                if metadata:
                    doc_id, doc_lang = doc[1]
                    doc = doc[0]
                else:
                    doc_lang = '__unknown__'

                words = []
                for wordid, value in doc:
                    if abs(int(value) - value) > 1e-6:
                        truncated += 1
                    words.extend([str(id2word[wordid])] * int(value))
                offsets.append(fout.tell())
                fout.write(utils.to_utf8('%s %s %s\n' % (doc_id, doc_lang, ' '.join(words))))

        if truncated:
            logger.warning("Mallet format can only save vectors with "
                            "integer elements; %i float entries were truncated to integer value" %
                            truncated)

        return offsets


    def docbyoffset(self, offset):
        """
        Return the document stored at file position `offset`.
        """
        with utils.smart_open(self.fname) as f:
            f.seek(offset)
            return self.line2doc(f.readline())
