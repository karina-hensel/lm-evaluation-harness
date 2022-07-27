"""
German Legal Entity Recognition Dataset
https://link.springer.com/chapter/10.1007/978-3-030-33220-4_20

Git: https://github.com/elenanereiss/Legal-Entity-Recognition

The dataset consists of a selection of German court decisions from 2017 and 2018 which have been published online by the Federal Ministry of Justice and Consumer Protection. 
The documents come from seven federal courts: Federal Labour Court (BAG), Federal Fiscal Court (BFH), Federal Court of Justice (BGH), 
Federal Patent Court (BPatG), Federal Social Court (BSG), Federal Constitutional Court (BVerfG) and Federal Administrative Court (BVerwG). Data can be used for 
Named Entity Recognition (NER) in German language documents from the legal domain. For this purpose the documents were manually annotated with 19 more fine-grained  and 
7 rather general semantic classes. The dataset consists of approximately 67,000 sentences and contains 54,000 annotated entities.
"""
import datasets
from lm_eval.base import Task, rf
from lm_eval.metrics import mean
from functools import partial
import numpy as np

_CITATION = """
@inproceedings{leitner2019fine,
  author = {Elena Leitner and Georg Rehm and Julian Moreno-Schneider},
  title = {{Fine-grained Named Entity Recognition in Legal Documents}},
  booktitle = {Semantic Systems. The Power of AI and Knowledge
                  Graphs. Proceedings of the 15th International Conference
                  (SEMANTiCS 2019)},
  year = 2019,
  editor = {Maribel Acosta and Philippe Cudré-Mauroux and Maria
                  Maleshkova and Tassilo Pellegrini and Harald Sack and York
                  Sure-Vetter},
  keywords = {aip},
  publisher = {Springer},
  series = {Lecture Notes in Computer Science},
  number = {11702},
  address = {Karlsruhe, Germany},
  month = 9,
  note = {10/11 September 2019},
  pages = {272--287},
  pdf = {https://link.springer.com/content/pdf/10.1007%2F978-3-030-33220-4_20.pdf}}
}"""

# Helper functions for aggregation (separate function for each metric)
def _german_ler_agg_precision(key, items):
    references, predictions = zip(*items)
    precision_metric = datasets.load_metric("precision")
    return precision_metric.compute(references=references, predictions=predictions, average='macro', labels= np.unique(predictions))[key]

def _german_ler_agg_recall(key, items):
    references, predictions = zip(*items)
    recall_metric = datasets.load_metric("recall")
    return recall_metric.compute(references=references, predictions=predictions, average='macro', labels= np.unique(predictions))[key]

def _german_ler_agg_f1(key, items):
    references, predictions = zip(*items)
    f1_metric = datasets.load_metric("f1")
    return f1_metric.compute(references=references, predictions=predictions, average='macro', labels= np.unique(predictions))[key]

class GermanLegalEntityRecognition(Task):
    VERSION = 0
    DATASET_PATH = 'wikiann'
    DATASET_NAME = 'de'


    def has_training_docs(self):
        print(DATASET_NAME)
        return True

    def has_validation_docs(self):
        return False

    def has_test_docs(self):
        return False
      
    def training_docs(self):
        if self.has_training_docs():
            if self._training_docs is None:
                self._training_docs = list(self.dataset["train"])
                print("Processing docs")
            return self._training_docs

    def validation_docs(self):
        pass

    def test_docs(self):
        pass
      
    def doc_to_text(self, doc): 
        print("Extracting text")
        return "tokens: "+ ' '.join(doc['tokens']) + "\n\n"+ "NER tags: "

    def doc_to_target(self, doc):
        # The prepended `" "` is required to space out the `doc_to_text` and
        # `doc_to_target` strings.

        target = doc["ner_tags"]
        print("Generating fewshot examples")
        return " " + str(target)

    def construct_requests(self, doc, ctx):
        """Uses RequestFactory to construct Requests and returns an iterable of
        Requests which will be sent to the LM.

        :param doc:
            The document as returned from training_docs, validation_docs, or
            test_docs.
        :param ctx: str
            The context string, generated by fewshot_context. This includes the natural
            language description, as well as the few shot examples, and the question
            part of the document for `doc`.
        """
        
        ner_tag_sequence = rf.greedy_until(ctx, ["."])

        while len(ner_tag_sequence) < len(ctx.split(" ")):
            tmp = rf.greedy_until(ctx[len(ner_tag_sequence):], ["."])
            ner_tag_sequence += tmp
        print("Constructing requests")
        return ner_tag_sequence

    def process_results(self, doc, results):
        """Take a single document and the LM results and evaluates, returning a
        dict where keys are the names of submetrics and values are the values of
        the metric for that one document

        :param doc:
            The document as returned from training_docs, validation_docs, or test_docs.
        :param results:
            The results of the requests created in construct_requests.
        """
        tag_sequence = results
        
        true_label = doc["ner_tags"]

        predictions = {"id":doc["id"], "tags":tag_sequence}
        references = {"id":doc["id"], "true tags":doc["ner_tags"]}
        print(predictions)
        return {"acc": pred==true_label, "precision":(predictions, references), "recall":(predictions, references), "f1":(predictions, references)}

    def aggregation(self):
        """
        :returns: {str: [metric_score] -> float}
            A dictionary where keys are the names of submetrics and values are
            functions that aggregate a list of metric scores
        """
        return {"acc":mean, "precision": partial(_german_ler_agg_precision, "precision"), 
                "recall" : partial(_german_ler_agg_recall, "recall"), 
                "f1" : partial(_german_ler_agg_f1, "f1")}

    def higher_is_better(self):
        return {"acc":True, "precision":True, "recall":True, "f1":True}    
