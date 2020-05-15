'''
Twitter Contest Bot

IN ACTIVE DEVELOPMENT: *NOT STABLE*
'''
from collections import deque
import tweepy
import re
import random
import smtplib
import textwrap
import time

dump_out = open('dump', 'a+')
log_out = open('log', 'a+')

dump_out.write('STARTING BOT @ TIMESTAMP: ' + time.ctime() + '...\n')
log_out.write('STARTING BOT @ TIMESTAMP: ' + time.ctime() + '...\n')

dump_out.write('VERFYING CREDENTIALS...\n')
auth = tweepy.OAuthHandler('REDACTED', 'REDACTED')
auth.set_access_token('REDACTED', 'REDACTED')
api = tweepy.API(auth, wait_on_rate_limit = True, wait_on_rate_limit_notify = True)
api.verify_credentials()

dump_out.write('RETRIEVING DATA FROM FILE...\n')
with open('data', 'r') as fin:
	total_contest_count = int(fin.readline().strip().split()[3])
	total_follow_count = int(fin.readline().strip().split()[3])
	total_retweet_count = int(fin.readline().strip().split()[3])
	followers_list = fin.readline().strip().split()[3:]
	followers = set(followers_list)
	follow_queue = deque(followers_list)
	entered_contests = set(fin.readline().strip().split()[3:])

current_seen_users = set()
current_contest_count = 0
current_follow_count = 0
current_retweet_count = 0

can_retweet = True
can_follow = True

queries = ['giveaway AND (rt OR retweet) -like -comment -reply -dm -mention -tag -sugar -minty -filter:retweets -filter:replies',
'retweet to win -like -comment -reply -dm -mention -tag -sugar -minty -filter:retweets -filter:replies',
'"retweet to win" -like -comment -reply -dm -mention -tag -sugar -minty -filter:retweets -filter:replies',
'"rt to win" -like -comment -reply -dm -mention -tag -sugar -minty -filter:retweets -filter:replies',
'"retweet to win" -like -comment -tag -filter:retweets -filter:replies',
'#giveaway AND retweet -like -comment -reply -tag -filter:retweets -filter:replies',
]
results = ['popular', 'recent']

start = time.time()
last_log = time.time()

dump_out.write('STARTING MAIN LOOP...\n')
while can_retweet and time.time() < start + 12600:
	#print('search')
	try:
		tweets = api.search(q = random.choice(queries), lang = 'en', result_type = random.choice(results), count = '100', tweet_mode = 'extended')
	except Exception as e:
		dump_out.write('ERROR: ' + str(e) + '\n')
		time.sleep(random.randint(60, 120))
		continue

	search_wait = True

	for tweet in tweets:
		#print('iterate')
		if str(tweet.id_str) in entered_contests:
			continue

		search_wait = False

		entered_contests.add(str(tweet.id_str))
		text = tweet.full_text

		if re.search('bot', text, re.IGNORECASE):
			continue
		if tweet.user.screen_name in ['followandrt2win', 'b0ttem', 'retweeejt'] or tweet.user.name in ['Bot Spotting', 'RT Sport']:
			continue
		if tweet.user.screen_name in current_seen_users:
			continue

		current_seen_users.add(tweet.user.screen_name)
		current_contest_count += 1
		total_contest_count += 1

		dump_out.write('--------------------------------------------------\n')
		dump_out.write('HIT: ' + str(total_contest_count) + '\n')
		dump_out.write('\n')
		dump_out.write(text + '\n')
		dump_out.write('\n')

		#print('HIT')
		#print()
		#print(text)
		#print()

		if can_follow and re.search('follow', text, re.IGNORECASE):
			to_follow = [follower[1:].strip(',') for follower in re.findall(r'@\S+', text)]
			to_follow.append(tweet.user.screen_name)

			if current_follow_count + len(to_follow) > 85: #should be 100 
				queries = [query + ' -follow -following' for query in queries]
				can_follow = False
				break

			queue_full = True if len(followers) >= 4850 else False

			for follower_id in to_follow:
				if follower_id not in followers:
					if queue_full:
						remove_id = follow_queue.popleft()
						dump_out.write('UNFOLLOWING ' + remove_id + '...\n')
						api.destroy_friendship(id = remove_id)
						followers.remove(remove_id)
						time.sleep(3)

					dump_out.write('FOLLOWING ' + follower_id + '...\n')
					try:
						api.create_friendship(id = follower_id, follow = True)
						followers.add(follower_id)
						follow_queue.append(follower_id)
						current_follow_count += 1
						total_follow_count += 1
					except Exception as e:
						dump_out.write('ERROR: ' + str(e) + '\n')

					time.sleep(3)

		if can_retweet:
			if current_retweet_count == 375: #should be 400
				can_retweet = False
				break
			dump_out.write('RETWEETING POST...\n')
			try:
				api.retweet(tweet.id_str)
				current_retweet_count += 1
				total_retweet_count += 1
			except Exception as e:
				dump_out.write('ERROR: ' + str(e) + '\n')
				continue

		#print('sleep')
		if can_follow:
			time.sleep(32)
		time.sleep(38)

	if time.time() > last_log + 3600:
		#print('log')
		last_log = time.time()
		dump_out.write('LOGGING DATA...\n')
		log_message = textwrap.dedent("""
		--------------------------------------------------\n
		TIMESTAMP: {ts} \n
		TOTAL CONTEST COUNT: {tcc} \n
		TOTAL FOLLOW COUNT: {tfc} \n
		TOTAL RETWEET COUNT: {trtc} \n
		CURRENT CONTEST COUNT: {ccc} \n
		CURRENT FOLLOW COUNT: {cfc} \n
		CURRENT RETWEET COUNT: {crtc} \n
		CURRENT FOLLOW QUEUE: {cfq} \n
		CURRENT ENTERED CONTESTS: {cec} \n
		--------------------------------------------------\n
		""".format(
			ts = str(time.ctime()), 
			tcc = str(total_contest_count), tfc = str(total_follow_count),
			trtc = str(total_retweet_count), ccc = str(current_contest_count),
			cfc = str(current_follow_count), crtc = str(current_retweet_count),
			cfq = ' '.join([str(x) for x in follow_queue]), cec = ' '.join([str(x) for x in entered_contests])))

		log_out.write(log_message)

		dump_out.write('STARTING GMAIL SMTP SECURE CONNECTION...\n')
		gmail_username = 'REDACTED'
		gmail_password = "REDACTED"

		try:
			gmail_server = smtplib.SMTP_SSL('smtp.gmail.com')
			gmail_server.ehlo()	
			gmail_server.login(gmail_username, gmail_password)
			gmail_server.sendmail('REDACTED', 'REDACTED', log_message)
			gmail_server.close()
			dump_out.write('EMAIL SENT SUCCESSFULLY\n')
		except Exception as e:
			dump_out.write('ERROR: ' + str(e) + '\n')

	if search_wait:
		time.sleep(5)

dump_out.close()
log_out.close()

with open('data', 'w') as fout:
	fout.write('TOTAL CONTEST COUNT: ' + str(total_contest_count) + '\n')
	fout.write('TOTAL FOLLOW COUNT: ' + str(total_follow_count) + '\n')
	fout.write('TOTAL RETWEET COUNT: ' + str(total_retweet_count) + '\n')
	fout.write('FOLLOW QUEUE: ' + ' '.join([str(x) for x in follow_queue]) + '\n')
	fout.write('ENTERED CONTESTS: ' + ' '.join([str(x) for x in entered_contests]) + '\n')