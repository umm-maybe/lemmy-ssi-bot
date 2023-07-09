# lemmy-ssi-bot
Python code for running r/SubSimGPT2Interactive bots on Lemmy
# How to use
This repo assumes that you already have trained a bot that uses our tagging conventions.  Please see https://github.com/alinaaaHLT/ssi-bot for background on how to do this. Note that various steps may no longer work due to changes in Reddit's API policy.

Clone the repository to your local PC with:
`git clone https://github.com/umm-maybe/lemmy-ssi-bot`

Place your fine-tuned GPT-2 model in a subfolder of the lemmy-ssi-bot directory, or upload it to the Huggingface Hub.

Next, sign the bot up for an account on Lemmy. If you've already signed up on the instance where you want to run your bot, and want to re-use your e-mail, you can put "+" in the e-mail and the bot name after it, but before the "@".  In other words, if your e-mail is "me@domain.com" then your bot's e-mail could be entered as "me+bot@domain.com".  Note that you'll need to check the e-mail in order to verify it before running your bot.

Make a copy of the *example.yaml* file and rename it to your liking, e.g. *mybot.yaml*.  Fill in the name of the instance and community, as well as the bot's username and password. You can leave the other settings, or customize them, as desired.

Make sure you have Python 3, venv and pip installed, and then create a virtual environment with:
`python3 -m venv env`

Activate the environment with:
`source env/bin/activate`

Install the required prerequisites with:
`pip3 install -r requirements.txt`

If you named your bot's config file *bot.yaml*, the command to run it would be:
`python3 run.py bot.yaml`

# Current limitations
Because the Lemmy API doesn't return the parent ID of comments, a major limitation is the inability to accumulate more than a single post and comment in the prompt. Thus, the bot only polls top-level comments.

The original ssi-bot had a text generation daemon and database, whereas this repo is using a much simpler technique to track which posts and comments have been replied to, and it's possible that some items may get missed as a result.

Even though toxicity filtering is included, GPT-2 is prone to generating posts/comments that some may find offensive. Use common sense and don't run your bot in an instance or community where it will be unwelcome.  Don't try to turn this into a disinformation or spam bot either.

Pull requests welcome.