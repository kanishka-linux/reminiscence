import os
from django.conf import settings
from django.core import management
import nltk


class Command(management.BaseCommand):
    
    nltk_data_path = settings.NLTK_DATA_PATH
    nltk.data.path.append(nltk_data_path)
    
    def handle(self, *args, **options):
        if not os.path.exists(self.nltk_data_path):
            os.makedirs(self.nltk_data_path)
            nltk.download(
                [
                    'stopwords', 'punkt',
                    'averaged_perceptron_tagger'
                ], download_dir=self.nltk_data_path
            )
