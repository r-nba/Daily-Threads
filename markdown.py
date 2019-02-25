import logging
from datetime import datetime

logger = logging.getLogger('IM')

class markdown:

    def generate_news_markdown(news):

        news_markdown = ''
        for i, news in enumerate(news):
            news_markdown += '0. [' + news['title'] + '](https://reddit.com/r/nba/comments/' + news['id'] + ')\n\n'
            if i == 4:
                break
                
        return news_markdown

    def generate_games_markdown(game, thread):
               
        index_markdown = '|Tip-off|Away||Home||GDT|PGT|\n' \
                         '|:--|:--|:-:|:--|--:|:-:|:-:|\n'
        next_markdown = '|Away|Home|Score|PGT|\n' \
                        '|:--|:--|:-:|:-:|\n'

        games_comment_markdown = []
        for i, game in enumerate(game):
            game_comment = {}
            if game['game_id'] is None:
                game_thread = ''
            else:
                game_thread = '[(Link)](https://reddit.com/r/nba/comments/' + game['game_id'] + ')'

            if game['post_id'] is None:
                post_thread = ''
            else:
                post_thread = '[(Link)](https://reddit.com/r/nba/comments/' + game['post_id'] + ')'
                
            # Formatting
            if thread == 'index':
                if game['away_score'] is None:
                    game_update = 'at'
                else:
                    game_update = '>!' + str(game['away_score']) + '!< at >!' + str(game['home_score']) + '!<'
                    
                index_markdown += '|{0}|[{1}](/r/{2})|{3}|[{4}](/r/{5})|{6}|{7}|{8}|\n' \
                    .format(game['time'], game['away'], game['away_subreddit'], game_update, game['home'], game['home_subreddit'], game['current_status'], game_thread, post_thread)

            elif thread == 'next':
                if game['away_score'] is None:
                    game['away_score'] = ''
                if game['home_score'] is None:
                    game['home_score'] = ''

                if int(game['away_score']) > int(game['home_score']):
                    game_result = 'defeat the'
                else:
                    game_result = 'fall to the'
                
                next_markdown += '|[{0}](/r/{1})|[{2}](/r/{3})|{4} - {5}|{6}|\n' \
                    .format(game['away'], game['away_subreddit'], game['home'], game['home_subreddit'], game['away_score'], game['home_score'], post_thread)
                game_comment['comment'] = '**{0}** {1} **{2}**, {3} - {4}' \
                                          .format(game['away'], game_result, game['home'], game['away_score'], game['home_score'])
            games_comment_markdown.append(game_comment)
            
        if thread == 'index':
            return index_markdown
        elif thread == 'next':
            return next_markdown, games_comment_markdown

    def generate_previous_markdown(previous_thread):

        previous_start_string = '# Today\'s Games:\n\n'
        end_string = '# Yesterday\'s Games:'

        after_games_start = previous_thread.split(previous_start_string, 1)[1]
        previous_markdown = after_games_start.split(end_string, 1)[0]
        
        return previous_markdown

    def generate_highlights_markdown(highlights):

        highlights_markdown = ''
        for i, highlights in enumerate(highlights):
            highlights_markdown += '0. [' + highlights['title'] + '](' + highlights['url'] + ') | [(Comments)](https://reddit.com/r/nba/comments/' + highlights['id'] + ')\n\n'
            if i == 4:
                break
                
        return highlights_markdown

    def generate_index_markdown(indexes):

        indexes_markdown = ''
        for i, indexes in enumerate(indexes):
            thread_date_formatted = datetime.strptime(indexes['thread_date'],'%Y%m%d').strftime('%B %d, %Y')
            indexes_markdown += '[' + thread_date_formatted + '](https://reddit.com/r/nba/comments/' + indexes['id'] + ')'
            if i == 4:
                break
            else:
                indexes_markdown += '\n\n'
                
        return indexes_markdown
    
    def generate_next_day_markdown(games):
        logger.info('Formatting index thread ... ')
        
        starting_string = 'Here is a place to have in depth, x\'s and o\'s, discussions on yesterday\'s games. Post-game discussions are linked in the table, **keep your memes and reactions there.**\n\n'
        
        next_day_fmt = starting_string \
              + games

        return next_day_fmt

    """def generate_index_thread_markdown(thread_format, news, games, previous, highlights, community, index):
        logger.info('Formatting index thread ... ')
        
        news_start_string = '$news\n\n'
        games_start_string = '$games\n\n'
        previous_start_string = '$previous\n\n'
        highlights_start_string = '$highlights\n\n'
        community_start_string = '$community\n\n'
        index_start_string = '$index'
        end_string = '\n\n'
        
        before_news_start = thread_format.split(news_start_string, 1)[0]
        after_news_start = thread_format.split(news_start_string, 1)[1]

        before_games_start = after_news_start.split(games_start_string, 1)[0]
        after_games_start = after_news_start.split(games_start_string, 1)[1]

        before_previous_start = after_games_start.split(previous_start_string, 1)[0]
        after_previous_start = after_games_start.split(previous_start_string, 1)[1]

        before_highlights_start = after_previous_start.split(highlights_start_string, 1)[0]
        after_highlights_start = after_previous_start.split(highlights_start_string, 1)[1]

        before_community_start = after_highlights_start.split(community_start_string, 1)[0]
        after_community_start = after_highlights_start.split(community_start_string, 1)[1]

        before_index_start = after_community_start.split(index_start_string, 1)[0]

        index_thread_fmt = before_news_start \
              + news + end_string \
              + before_games_start \
              + games + end_string \
              + before_previous_start \
              + previous + end_string \
              + before_highlights_start \
              + highlights + end_string \
              + before_community_start \
              + community + end_string \
              + before_index_start \
              + index

        return index_thread_fmt"""

    def generate_index_thread_markdown(thread_format, games, previous, highlights):
        logger.info('Formatting index thread ... ')
        
        news_start_string = '$news\n\n'
        games_start_string = '$games\n\n'
        previous_start_string = '$previous\n\n'
        highlights_start_string = '$highlights\n\n'
        community_start_string = '$community\n\n'
        index_start_string = '$index'
        end_string = '\n\n'
        
        before_news_start = thread_format.split(news_start_string, 1)[0]
        after_news_start = thread_format.split(news_start_string, 1)[1]

        before_games_start = after_news_start.split(games_start_string, 1)[0]
        after_games_start = after_news_start.split(games_start_string, 1)[1]

        before_previous_start = after_games_start.split(previous_start_string, 1)[0]
        after_previous_start = after_games_start.split(previous_start_string, 1)[1]

        before_highlights_start = after_previous_start.split(highlights_start_string, 1)[0]
        after_highlights_start = after_previous_start.split(highlights_start_string, 1)[1]

        before_community_start = after_highlights_start.split(community_start_string, 1)[0]
        after_community_start = after_highlights_start.split(community_start_string, 1)[1]

        before_index_start = after_community_start.split(index_start_string, 1)[0]

        rules = "Daily Discussion Thread : [Rules](https://www.reddit.com/r/nba/wiki/rules#wiki_daily_discussion_thread)"

        index_thread_fmt = before_games_start \
              + games + end_string \
              + before_previous_start \
              + previous + end_string \
              + before_highlights_start \
              + highlights + end_string \
              + rules + end_string

        return index_thread_fmt
