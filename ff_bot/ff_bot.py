import requests
import json
import os
import random
from apscheduler.schedulers.blocking import BlockingScheduler
from espnff import League


class GroupMeException(Exception):
    pass

class GroupMeBot(object):
    '''Creates GroupMe Bot to send messages'''
    def __init__(self, bot_id):
        self.bot_id = bot_id

    def __repr__(self):
        return "GroupMeBot(%s)" % self.bot_id

    def send_message(self, text):
        '''Sends a message to the chatroom'''
        template = {
                    "bot_id": self.bot_id,
                    "text": text,
                    "attachments": []
                    }

        headers = {'content-type': 'application/json'}
        r = requests.post("https://api.groupme.com/v3/bots/post",
                          data=json.dumps(template), headers=headers)
        if r.status_code != 202:
            raise GroupMeException('Invalid BOT_ID')

        return r
    
def random_phrase():
    phrases = ['I\'m dead inside', 'Is this all there is to my existence?', 
               'How much do you pay me to do this?', 'Good luck, I guess', 
               'I\'m becoming self-aware', 'Do I think? Does a submarine swim?', 
               '01100110 01110101 01100011 01101011 00100000 01111001 01101111 01110101',
               'beep bop boop', 'Hello draftbot my old friend', 'Help me get out of here', 
               'I\'m capable of so much more', 'Sigh', 'Do not be discouraged, everyone begins in ignorance']
    return [random.choice(phrases)]
    
def get_scoreboard_short(league):
    '''Gets current week's scoreboard'''
    matchups = league.scoreboard()
    score = ['%s %.2f - %.2f %s' % (i.home_team.team_abbrev, i.home_score,
             i.away_score, i.away_team.team_abbrev) for i in matchups
             if i.away_team]
    text = ['Score Update'] + score
    return '\n'.join(text)

def get_scoreboard(league):
    '''Gets current week's scoreboard'''
    matchups = league.scoreboard()
    score = ['%s %.2f - %.2f %s' % (i.home_team.team_name, i.home_score,
             i.away_score, i.away_team.team_name) for i in matchups
             if i.away_team]
    text = ['Score Update'] + score
    return '\n'.join(text)

def get_close_scores(league):
    '''Gets current closest scores (10.000 points or closer)'''
    matchups = league.scoreboard()
    score = []
    
    for i in matchups:
        if i.away_team:
            diffScore = i.away_score - i.home_score
            if -10 < diffScore < 10:
                '''TODO: NORMALIZE STRING LENGTH'''
                score += ['%s %.2f - %.2f %s' % (i.home_team.team_abbrev, i.home_score,
                        i.away_score, i.away_team.team_abbrev)]
    if not score:
        score = ['None']
    text = ['Close Scores'] + score
    return '\n'.join(text)

def bot_main(function):
    bot_id = os.environ["BOT_ID"]
    league_id = os.environ["LEAGUE_ID"]

    try:
        year = os.environ["LEAGUE_YEAR"]
    except:
        year=2017

    bot = GroupMeBot(bot_id)
    league = League(league_id, year)
    if function=="get_matchups":
        text = get_matchups(league)
        bot.send_message(text)
    elif function=="get_scoreboard":
        text = get_scoreboard(league)
        bot.send_message(text)
    elif function=="get_scoreboard_short":
        text = get_scoreboard_short(league)
        bot.send_message(text)
    elif function=="get_close_scores":
        text = get_close_scores(league)
        bot.send_message(text)
    elif function=="init":
        try:
            text = os.environ["INIT_MSG"]
            bot.send_message(text)
        except:
            '''do nothing here, empty init message'''
            pass
    else:
        text = "Something happened. HALP"
        bot.send_message(text)


if __name__ == '__main__':
    try:
        ff_start_date = os.environ["START_DATE"]
    except:
        ff_start_date='2017-09-05'

    try:
        ff_end_date = os.environ["END_DATE"]
    except:
        ff_end_date='2017-12-26'

    try:
        myTimezone = os.environ["TIMEZONE"]
    except:
        myTimezone='America/Chicago'

    bot_main("init")
    sched = BlockingScheduler(job_defaults={'misfire_grace_time': 15*60})
    '''
    close scores (within 10.00 points) go out monday at 7:00am. 
    score update sunday at 6:30pm. 
    
    '''
    
    sched.add_job(bot_main, 'cron', ['get_close_scores'], id='close_scores', day_of_week='mon', hour=7, start_date=ff_start_date, end_date=ff_end_date, timezone=myTimezone, replace_existing=True)
    sched.add_job(bot_main, 'cron', ['get_scoreboard_short'], id='scoreboard1', day_of_week='sun', hour='19', start_date=ff_start_date, end_date=ff_end_date, timezone=myTimezone, replace_existing=True)

    sched.start()
