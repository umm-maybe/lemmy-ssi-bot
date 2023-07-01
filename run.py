## Minimal implementation of an r/SubSimGPT2Interactive bot for Lemmy
## by m. maybe, July 2023

import sys
import threading
import time
from datetime import datetime
from random import random
import pandas as pd
import os.path

from sanitation import clean_text, bad_keyword, is_toxic
#from image_gen import generate_image

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
        self.bot_id = self.lemmy.user.get(username=self.config['bot_username'])["person_view"]["person"]["id"]
        self.community_id = self.lemmy.discover_community(self.config['lemmy_community'])
        self.submission_writer = threading.Thread(target=self.submission_loop,args=())
        self.submission_reader = threading.Thread(target=self.read_posts, args=())
        self.comment_reader = threading.Thread(target=self.read_comments, args=())
        self.post_frequency = self.config['post_frequency'] # in hours
        self.hours_since_last_post = self.post_frequency
        self.model = pipeline(model=self.config['model'], task='text-generation')
        self.params = self.config['model_params']
        self.thresh = self.config['thresholds']
        self.badkey = self.config['negative_keywords']
        # check if history table exists; initialize if it doesn't
        self.historyfile = f"{self.config['bot_username']}_history.csv" 
        if os.path.isfile(self.historyfile):
            self.history = pd.read_csv(self.historyfile)
        else:
            self.history = pd.DataFrame(columns = ['type', 'id', 'time'])

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

    # function to generate posts
    def make_post(self):
        if random()<self.config['image_post_share']:
            prompt = '<|sols|><|sot|>'
        else:
            prompt = '<|soss|><|sot|>'
        for attempt in range(self.config['max_post_attempts']):
            generated_text = self.model(prompt, return_full_text=False, **self.params)[0]['generated_text']
            print(f"GENERATED:\n{generated_text}")
            title = clean_text(generated_text.split('<|eot|>')[0])
            if not title:
                print("Failed to generate post title, trying again...")
                continue
            if bad_keyword(title,self.badkey) or is_toxic(title,self.thresh) or title.find(" ")==-1:
                print("Bad title generated, re-generating...")
                continue
            if 'sols' in prompt:
                image_path = generate_image(title)
                image_dict = self.lemmy.image.upload(image_path)
                try:
                    post = self.lemmy.post.create(community_id=self.community_id,name=title,url=image[0]["image_url"])
                    if post:
                        print(f"Successfully posted")
                        break
                    else:
                        print("Failed to post, trying again in 5 minutes...")
                        time.sleep(300)
                        continue
                except Exception as e:
                    print(f"Failed to post ({e})")
            else:
                post_body = clean_text(generated_text.split('<|sost|>')[1].split('<|eost|>')[0])
                if not post_body:
                    print("Failed to generate post body, trying again...")
                    continue
                if bad_keyword(post_body,self.badkey) or is_toxic(post_body,self.thresh) or post_body.find(" ")==-1:
                    print("Bad post body generated, re-generating...")
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

    def read_posts(self):
        while True:
            now = datetime.now()
            utcstamp = now.strftime("%Y-%m-%d %H:%M:%S")
            new_posts = self.lemmy.post.list(self.community_id)
            ids_seen = self.history[self.history['type']=='post']['id'].values.tolist()
            for new_post in new_posts:
                new_post_id = new_post["post"]["id"]
                if not new_post_id in ids_seen:
                    self.history.loc[len(self.history)] = {'type': 'post', 'id': new_post_id, 'time': utcstamp}
                    if self.bot_id == new_post["post"]["creator_id"]:
                        # don't reply to own posts
                        continue
                    if random() < self.config['post_reply_probability']:
                        self.post_reply(new_post)
                    # save the post so we know that we've looked at it
            new_ids = []
            # back up the history table
            self.history.to_csv(self.historyfile)
            time.sleep(60)
    
    def post_reply(self,post_dict):
        post_title = post_dict["post"]["name"]
        post_properties = post_dict["post"].keys()
        if "body" in post_properties:
            post_body = post_dict["post"]["body"]
            prompt = f'<|soss|><|sot|>{post_title}<|eot|><|sost|>{post_body}<|eost|><|sor|>'
        elif "url" in post_properties:
            #linkpost
            post_url = post_dict["post"]["url"]
            prompt = f'<|sols|><|sot|>{post_title}<|eot|><|sol|>{post_url}<|eol|><|sor|>'
        else:
            prompt = f'<|soss|><|sot|>{post_title}<|eot|><|sor|>'
        for attempt in range(self.config['max_reply_attempts']):
            generated_text = self.model(prompt, return_full_text=False, **self.params)[0]['generated_text']
            print(f"GENERATED:\n{generated_text}")
            response = clean_text(generated_text.split('<|eor|>')[0])
            if not response:
                print("Failed to generate post reply, trying again...")
                continue
            if bad_keyword(response,self.badkey) or is_toxic(response,self.thresh) or response.find(" ")==-1:
                print("Bad text generated, re-generating...")
                continue
            try:
                post_id = post_dict["post"]["id"]
                reply = self.lemmy.comment.create(post_id, content=response)
                if reply:
                    print(f"Successfully replied")
                    break
                else:
                    print("Failed to reply, trying again in 5 minutes...")
                    time.sleep(300)
                    continue
            except Exception as e:
                print(f"Failed to reply ({e})")

    def read_comments(self):
        while True:
            # a major limitation right now is inability to chain more than 1 post and 1 comment
            now = datetime.now()
            utcstamp = now.strftime("%Y-%m-%d %H:%M:%S")
            new_comments = self.lemmy.comment.list(self.community_id, max_depth=1)
            ids_seen = self.history[self.history['type']=='comment']['id'].values.tolist()
            for new_comment in new_comments:
                new_comment_id = new_comment["comment"]["id"]
                if not new_comment_id in ids_seen:
                    self.history.loc[len(self.history)] = {'type': 'comment', 'id': new_comment_id, 'time': utcstamp}
                    if self.bot_id == new_comment["comment"]["creator_id"]:
                        # don't reply to own posts
                        continue
                    if random() < self.config['comment_reply_probability']:
                        self.comment_reply(new_comment)
            # back up the history table
            self.history.to_csv(self.historyfile)                        
            time.sleep(60)

    def comment_reply(self,comment_dict):
        # get the original post so we can figure out if the bot is the OP
        original_post = self.lemmy.post.get(comment_dict["comment"]["post_id"])["post_view"]
        post_title = original_post["post"]["name"]
        post_body = original_post["post"]["body"]
        op_id = original_post["creator"]["id"]
        if self.bot_id==op_id:
            prompt = '<|soopr|>'
        else:
            prompt = '<|sor|>'
        comment_body = comment_dict["comment"]["content"]
        comment_author_id = comment_dict["comment"]["creator_id"]
        if comment_author_id==op_id:
            prompt = f"<|soopr|>{comment_body}<|eoopr|>" + prompt
        else:
            prompt = f"<|sor|>{comment_body}<|eor|>" + prompt
        prompt = f"<|soss|><|sot|>{post_title}<|eot|><|sost|>{post_body}<|eost|>" + prompt
        for attempt in range(self.config['max_reply_attempts']):
            generated_text = self.model(prompt, return_full_text=False, **self.params)[0]['generated_text']
            print(f"GENERATED:\n{generated_text}")
            truncate = generated_text.find('<|eo')
            if truncate == -1:
                print("Failed to generate comment reply, trying again...")
                continue
            response = clean_text(generated_text[:truncate])
            if not response:
                print("Failed to generate comment reply, trying again...")
                continue
            if bad_keyword(response,self.badkey) or is_toxic(response,self.thresh) or response.find(" ")==-1:
                print("Bad text generated, re-generating...")
                continue
            try:
                reply = self.lemmy.comment.create(post_id=original_post["post"]["id"],content=response,parent_id=comment_dict["comment"]["id"])
                if reply:
                    print(f"Successfully replied")
                    break
                else:
                    print("Failed to reply, trying again in 5 minutes...")
                    time.sleep(300)
                    continue
            except Exception as e:
                print(f"Failed to reply ({e})")

    def run(self):
        print("Bot named {} running on {}".format(
            self.config['bot_username'], self.config['lemmy_community']))
        self.submission_writer.start()
        self.submission_reader.start()
        self.comment_reader.start()


def main():
    bot = lemmy_bot(sys.argv[1])
    bot.run()
    
if __name__ == "__main__":
    main()