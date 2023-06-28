## Minimal implementation of an r/SubSimGPT2Interactive bot for Lemmy
## by m. maybe, July 2023

import sys
import threading
import time
from datetime import datetime

from sanitation import clean_text

import yaml
from pythorhead import Lemmy
from transformers import pipeline

def load_yaml(filename):
    with open(filename, 'r') as stream:
        try:
            return yaml.safe_load(stream)
        except yaml.YAMLError as error:
            print(error)
    return None

class lemmy_bot:
    # initialize bot
    def __init__(self, config_file):
        self.config = load_yaml(config_file)
        if not self.config:
            print('Cannot load config file; check path and formatting')
            sys.exit()
        self.lemmy = Lemmy(self.config['lemmy_instance'])
        self.lemmy.log_in(self.config['bot_username'],self.config['bot_password'])
        self.community_id = self.lemmy.discover_community(self.config['lemmy_community'])
        self.submission_writer = threading.Thread(target=self.submission_loop,args=())
        #self.submission_reader = threading.Thread(target=self.read_posts, args=())
        #self.comment_reader = threading.Thread(target=self.watch_comments, args=())
        self.post_frequency = self.config['post_frequency'] # in hours
        self.hours_since_last_post = self.post_frequency
        self.model = pipeline(model=self.config['model'], task='text-generation')
        self.params = self.config['model_params']
    
    # function to generate posts (text only right now)
    def make_post(self):
        prompt = '<|soss|><|sot|>'
        for attempt in range(self.config['max_post_attempts']):
            generated_text = self.model(prompt, return_full_text=False, **self.params)[0]['generated_text']
            print(f"GENERATED:\n{generated_text}")
            title = clean_text(generated_text.split('<|eot|>')[0])
            if not title:
                print("Failed to generate post title, trying again...")
                continue
            post_body = clean_text(generated_text.split('<|sost|>')[1].split('<|eost|>')[0])
            if not post_body:
                print("Failed to generate post body, trying again...")
                continue
            try:
                post = self.lemmy.post.create(community_id=self.community_id,name=title,body=post_body)
                if post:
                    print(f"Successfully posted")
                    break
                else:
                    print("Failed to post, trying again in 5 minutes...")
                    time.sleep(300)
                    continue
            except Exception as e:
                print(f"Failed to post ({e})")
    
    # function to trigger posts on schedule
    def submission_loop(self):
        while True:
            now = datetime.now()
            if self.hours_since_last_post >= self.post_frequency:
                self.make_post()
                self.hours_since_last_post = 0
                self.last_post_time = now
            else:
                self.hours_since_last_post = (now - self.last_post_time).total_seconds() / 3600
            time.sleep(60)

    def run(self):
        print("Bot named {} running on {}".format(
            self.config['bot_username'], self.config['lemmy_community']))
        self.submission_writer.start()
        #self.submission_reader.start()
        #self.comment_reader.start()


def main():
    bot = lemmy_bot(sys.argv[1])
    bot.run()
    
if __name__ == "__main__":
    main()