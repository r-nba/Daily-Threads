import logging
import praw
import pytz
import time
from datetime import datetime, timedelta, time as dttime
import config

from data import data
from markdown import markdown

log_date_fmt = '%y-%m-%d %X %Z'
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt=log_date_fmt,
                    filename='index_bot.log',
                    filemode='a')
# define a Handler which writes INFO messages or higher to the sys.stderr
console = logging.StreamHandler()
console.setLevel(logging.INFO)
# set a format for console use
formatter = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s', datefmt=log_date_fmt)
# tell the handler to use this format
console.setFormatter(formatter)
# add the handler to the root logger
logging.getLogger('').addHandler(console)

class nbaMod(object):
    """ Reddit bot that handles posting and updating the index and next day threads periodically
    """

    def __init__(self):
        self.logger = logging.getLogger('IB')
        
        # logs into reddit
        self.reddit = praw.Reddit(
            client_id=config.client_id,
            client_secret=config.client_secret,
            username=config.username,
            password=config.password,
            user_agent='r/nba Index Thread generator v1.2.0 by /u/brexbre')

        self.data = data()
        
        # load all other settings
        self.load_settings()

    def load_settings(self):
        # reddit
        self.subreddit = self.reddit.subreddit('nba')
        self.post_subreddit = self.reddit.subreddit('nba')
        self.bot_timezone = pytz.timezone('US/Central')
        self.index_thread_title = 'r/NBA Game Threads Index + Daily Discussion '

        # load team data
        self.load_teams()
        
    def load_teams(self):
        # load team info
        self.logger.info('Loading team info from csv')
        
        self.team_dict = {}
        self.team_dict_med_key = {}
        self.team_dict_short_key = {}
        with open("data/teams.csv", "r") as teamInfoFile:
            for teamInfoRow in teamInfoFile.read().split("\n"):
                teamInfo = teamInfoRow.split(',')
                tmp_team_dict = {
                    'long_name': teamInfo[0] + " " + teamInfo[1],
                    'med_name': teamInfo[1],
                    'short_name': teamInfo[2].upper(),
                    'name_check': teamInfo[3]
                }
                self.team_dict[teamInfo[2].upper()] = tmp_team_dict
                self.team_dict_med_key[teamInfo[1]] = tmp_team_dict
                self.team_dict_short_key[teamInfo[2].upper()] = tmp_team_dict

    def need_index_thread(self, date):
        thread_hasnt_been_made = True
        for i, thread in enumerate(self.data.load_threads('index')):
            if thread['thread_date'] == date:
                thread_hasnt_been_made = False

        return thread_hasnt_been_made
    
    def need_next_day_thread(self, date):
        today = datetime.now().strftime("%Y%m%d")
        if self.was_yesterday_a_game_day(date) and self.next_day_thread_hasnt_been_made(today):
            return True
        else:
            return False

    def was_yesterday_a_game_day(self, date):
        was_game_day = False
        if self.data.games(date, 'number') > 0:
            was_game_day = True

        return was_game_day

    def next_day_thread_hasnt_been_made(self, date):
        thread_hasnt_been_made = True
        for i, thread in enumerate(self.data.load_threads('next')):
            if thread['thread_date'] == date:
                thread_hasnt_been_made = False

        return thread_hasnt_been_made
    
    def format_next_day_thread(self, date):
        games_markdown, games_comment_markdown = markdown.generate_games_markdown(self.data.games(date, 'full'), 'next')
        thread_markdown = markdown.generate_next_day_markdown(games_markdown.strip())

        return thread_markdown, games_comment_markdown

    def format_index_thread(self, date):
        thread_format = self.reddit.submission(id = '9p8t8a').selftext
        news_markdown = markdown.generate_news_markdown(self.data.news()).strip()
        games_markdown = markdown.generate_games_markdown(self.data.games(date, 'full'), 'index').strip()
        previous_markdown = markdown.generate_previous_markdown(self.data.previous()).strip()
        highlights_markdown = markdown.generate_highlights_markdown(self.data.highlights()).strip()
        community_markdown = self.data.rankings()
        index_markdown = markdown.generate_index_markdown(self.data.load_threads('index')).strip()
        
        thread_markdown = markdown.generate_index_thread_markdown(thread_format, \
                                                            news_markdown, \
                                                            games_markdown, \
                                                            previous_markdown, \
                                                            highlights_markdown, \
                                                            community_markdown, \
                                                            index_markdown)

        return thread_markdown
    
    def submit_index_thread(self):
        self.title_date = datetime.now().strftime("(%B %d, %Y)")
        self.game_date = datetime.now().strftime("%Y%m%d")
        self.title = self.index_thread_title + self.title_date
        
        submission = self.post_subreddit.submit(self.title, selftext = self.format_index_thread(self.game_date), send_replies = False)
        
        submission.mod.sticky(bottom=False)
        submission.mod.flair(text='Index Thread', css_class='index')
        submission.mod.suggested_sort(sort='new')
        self.logger.info('Index thread submitted')

    def submit_next_day_thread(self, date):
        self.title_date = datetime.now().strftime("(%B %d, %Y)")
        self.title = '[Serious Next Day Thread] Post-Game Discussion ' + self.title_date
        submission_body, comments = self.format_next_day_thread(date)
        
        submission = self.post_subreddit.submit(self.title, selftext = submission_body, send_replies = False)
        
        submission.mod.sticky(bottom=True)
        submission.mod.flair(text='Serious NDT', css_class='ndt')
        submission.mod.suggested_sort(sort='new')
        self.logger.info('Next day thread submitted')
        self.submit_next_day_thread_comments(date, submission, comments)

    def submit_next_day_thread_comments(self, date, next_day_thread, comments):
        for game in comments:
            submission = self.reddit.submission(id=next_day_thread)
            comment = submission.reply(game['comment'])
            comment.disable_inbox_replies()
        
    def update_index_thread(self):
        thread_id = self.data.load_threads('index')[0]['id']
        thread_date = self.data.load_threads('index')[0]['thread_date']
        self.reddit.submission(id = thread_id).edit(self.format_index_thread(thread_date))
        self.logger.info('Index thread updated')
        
def runMod():
    bot = nbaMod()
    run_updates = True
    consecutive_error_count = 0
    while run_updates:
        log_time = datetime.now().strftime("%B %d, %Y %I:%M %p")
        now = datetime.now()
        yesterdays_date = datetime.now() - timedelta(days=1)
        yesterdays_date_formatted = yesterdays_date.strftime('%Y%m%d')
        try:
            if bot.need_index_thread(now.strftime('%Y%m%d')) and now.hour >= 9:
                print('-' * 10 + str(now.hour) + '-' * 10)
                bot.submit_index_thread()
            elif now.hour <= 2 or now.hour >= 9:
                print('-' * 10 + str(now.hour) + '-' * 10)
                bot.update_index_thread()
                
            '''if bot.need_next_day_thread(yesterdays_date_formatted) and now.hour >= 9:
                bot.submit_next_day_thread(yesterdays_date_formatted)''' # to-do: fix NDT posting time
            update_freq = 60 * 10
            consecutive_error_count = 0
        except KeyboardInterrupt as e:
            logging.error("keyboard interrupt. Stopping bot.")
            logging.exception(e)
            raise
        except BaseException as e:
            consecutive_error_count += 1
            logging.exception(e)
            logging.warning("an error occurred during index creation " + str(consecutive_error_count) +
                            " consecutive errors")
            update_freq = 60
            if consecutive_error_count > 10:
                logging.warning("too many consecutive errors. exiting.")
                run_updates = False
                update_freq = 0
                raise
        logging.info("sleeping for " + str(timedelta(seconds=update_freq)) + " ... ... ...")
        time.sleep(update_freq)

if __name__ == "__main__":
    runMod()
