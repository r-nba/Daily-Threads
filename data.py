import logging
import praw
import datetime
import time
from urllib.request import urlopen
import json
from datetime import datetime, timedelta, time as dttime
import config

logger = logging.getLogger('DS')

class data(object):
    '''Data from source provider'''

    def __init__(self):        
        self.json_teams = None
        self.json_standings = None
        
        # logs into reddit
        self.reddit = praw.Reddit(
            client_id=config.client_id,
            client_secret=config.client_secret,
            username=config.username,
            password=config.password,
            user_agent='r/nba Index Thread generator v1.2.0 by /u/brexbre')

        # load all other settings
        self.load_settings()

    def load_settings(self):
        # reddit
        self.subreddit = self.reddit.subreddit('nba')
        self.pr_redditor = self.reddit.redditor('powerrankingsnba')
        self.nba_index_redditor = self.reddit.redditor(config.username)
        self.post_subreddit = self.reddit.subreddit('nba')
        self.thread_link = 'https://reddit.com/r/nba/comments/'
        self.index_thread_title = 'r/NBA Game Threads Index + Daily Discussion '

        # load team data
        self.load_teams()
        
    def load_teams(self):
        self.team_id_dict = {}
        self.team_name_dict = {}
        self.team_abbrev_dict = {}
        with open('data/teams.csv', 'r') as teamInfoFile:
            for teamInfoRow in teamInfoFile.read().split('\n'):
                teamInfo = teamInfoRow.split(',')
                tmp_team_id_dict = {
                    'long_name': teamInfo[0],
                    'med_name': teamInfo[1],
                    'short_name': teamInfo[2].upper(),
                    'sub': teamInfo[3],
                    'timezone': teamInfo[4],
                    'division': teamInfo[5],
                    'conference': teamInfo[6],
                    'id': teamInfo[7]
                }
                self.team_id_dict[teamInfo[7]] = tmp_team_id_dict
                self.team_name_dict[teamInfo[1]] = tmp_team_id_dict
                self.team_abbrev_dict[teamInfo[2].upper()] = tmp_team_id_dict

    def news(self):
        news = []
        for submission in self.subreddit.top(time_filter='week'):
            thread_info = {}
            if submission.link_flair_css_class=='news':
                thread_info['title'] = submission.title
                thread_info['id'] = submission.id
                
                news.append(thread_info)

        logger.info('Grabbed news')

        return news
    
    def get_threads(self, vTeam, hTeam):

        away_team_med = self.team_abbrev_dict[vTeam]['med_name']
        home_team_med = self.team_abbrev_dict[hTeam]['med_name']

        post_id = None
        game_id = None
        for t in self.subreddit.new(limit=250):
            if (away_team_med in t.title) and (home_team_med in t.title):
                if t.link_flair_css_class == 'postgamethread':
                    post_id = t.id
                
                elif t.link_flair_css_class == 'gamethread':
                    game_id = t.id

        return game_id, post_id

    def games(self, date, check):
        logger.info('Grabbing games')
        with urlopen('http://data.nba.com/prod/v2/' + date + '/scoreboard.json') as url:
            j = json.loads(url.read().decode())

        if check == 'number':
            return j['numGames']
        elif check == 'full':
            game_containers = j['games']
            games = []
            
            for i, game_container in enumerate(game_containers):

                game = {}
                
                # Find Game Status
                if game_container['statusNum'] == 1:
                    game['current_status'] = 'PRE-GAME'
                elif game_container['statusNum'] == 2:
                    game['current_status'] = 'LIVE'
                    if (str(game_container['clock']) == '0.0') or (str(game_container['clock']) == '') and str(game_container['period']['current']) == '2':
                        game['current_status'] = 'HALF-TIME'
                    elif (str(game_container['clock']) == '0.0') or (str(game_container['clock']) == '') and str(game_container['period']['current']) == '4':
                        game['current_status'] = 'FINAL'
                    elif game_container['clock'] == '':
                        game['current_status'] = str(game_container['period']['current']) + 'Q'
                    else:
                        game['current_status'] = str(game_container['clock']) + ' ' + str(game_container['period']['current']) + 'Q'
                elif game_container['statusNum'] == 3:
                    game['current_status'] = 'FINAL'

                # Find Game start time
                game['time'] = game_container['startTimeEastern']
                
                # Find Away and Home team
                away_team = game_container['vTeam']['triCode']
                home_team = game_container['hTeam']['triCode']

                # Add full names
                game['away'] = self.team_abbrev_dict[away_team]['long_name']
                game['home'] = self.team_abbrev_dict[home_team]['long_name']
                
                # Find Home and Away team subs
                game['away_subreddit'] = self.team_abbrev_dict[away_team]['sub']
                game['home_subreddit'] = self.team_abbrev_dict[home_team]['sub']
                
                # Find scores if they exist
                if not game_container['statusNum'] == 1:
                    game['away_score'] = game_container['vTeam']['score']
                    game['home_score'] = game_container['hTeam']['score']
                else:
                    game['away_score'] = None
                    game['home_score'] = None

                # Find threads if they exist
                game['game_id'], game['post_id'] = self.get_threads(away_team, home_team)

                # add to list of games
                games.append(game)

            logger.info('Scrape complete. {} games found.'.format(len(games)))
            return games
    
    def previous(self):
        self.previous_games = ''
        self.previous_thread = self.reddit.submission(id = self.load_threads('index')[1]['id']).selftext

        logger.info('Grabbed previous games')
        return self.previous_thread

    def highlights(self):
        highlights = []
        for submission in self.subreddit.top(time_filter='day'):
            thread_info = {}
            if submission.link_flair_css_class=='highlights':
                thread_info['title'] = submission.title
                thread_info['url'] = submission.url
                thread_info['id'] = submission.id
                
                highlights.append(thread_info)

        logger.info('Grabbed highlights')
        return highlights

    def rankings(self):

        for submission in self.pr_redditor.submissions.new(limit=10):
            self.power_rankings = '[' + submission.title + '](' + submission.url + ')'
            break

        logger.info('Grabbed rankings')
        return self.power_rankings

    def load_threads(self, thread):
        self.index_threads = []
        self.next_day_threads = []
        for submission in self.nba_index_redditor.submissions.new(limit=100):
            thread_info = {}
            if thread == 'index':
                if self.index_thread_title in submission.title:
                    thread_info['title'] = submission.title
                    thread_info['id'] = submission.id
                    thread_info['thread_date'] = datetime.strptime(submission.title.split('(')[1],'%B %d, %Y)').strftime('%Y%m%d')

                    self.index_threads.append(thread_info)
            if thread == 'next':
                if '[Serious Next Day Thread]' in submission.title and 'ndt' in submission.link_flair_css_class:
                    thread_info['title'] = submission.title
                    thread_info['id'] = submission.id
                    thread_info['thread_date'] = datetime.strptime(submission.title.split('(')[1],'%B %d, %Y)').strftime('%Y%m%d')

                    self.next_day_threads.append(thread_info)
                    
        if thread == 'index':
            logger.info('Grabbed Index threads')
            return self.index_threads
        if thread == 'next':
            logger.info('Grabbed Next Day threads')
            return self.next_day_threads
