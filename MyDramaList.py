import requests, json, re, time
from bs4 import BeautifulSoup

start_index = 1
end_index = 5

for current_drama_id in range(start_index, end_index + 1):
	while True:
		try:
			drama_page_resp = requests.get('http://mydramalist.com/' + str(current_drama_id))
			break
		except:
			print('Drama page request failed. Retrying...')
			time.sleep(3)

	if drama_page_resp.status_code != 200: #I'm assuming wrongly here that the only statuses are 200 and 404. It met my requirements, though.
		print('Drama page doesn\'t exist. Skipping...')
		continue
	else:
		drama_page_bsoup = BeautifulSoup(drama_page_resp.text, 'html.parser')
		drama_info = {}
		drama_info['genres'] = []
		drama_info['titles'] = {'main': None, 'japanese': None, 'alt_titles': []}
		drama_details = {'country': None, 'type': None, 'release_date': None, 'episode_count': None, 'duration': None, 'network': None, 'rank': None, 'rank_popularity': None}
		drama_stats = {'rating': {'score': None, 'users_count': None}}
		drama_cast_members = []
		drama_info['related_content'] = []
		drama_details['release_date'] = {'start': None, 'end': None}

		drama_info['thumb'] = drama_page_bsoup.select('div.cover img')[0]['src']
		drama_info['synopsis'] = drama_page_bsoup.find('div',{'class':'show-synopsis'}).text.strip()
		drama_info['titles']['main'] = drama_page_bsoup.find('meta',{'property':'og:title'})['content']
		drama_info['trailer'] = drama_page_bsoup.find('div',{'class':'btn-trailer button green hfl'})
		if drama_info['trailer']:
			drama_info['trailer'] = int(drama_info['trailer']['data-id'])

		drama_genres_elem = drama_page_bsoup.find('div',{'class':'show-genres'})
		drama_hfs_elems = drama_page_bsoup.find_all('div',{'class':'hfs'})
		drama_random_headers = drama_page_bsoup.find_all('h4',{'class':'inline'})

		if drama_genres_elem.text.strip() != "": # If drama has genre(s).
			drama_genres_links = drama_genres_elem.find_all('a')
			for drama_genres_link in drama_genres_links:
				drama_genre_id = re.search('(genres\[\]=)(\d+)',drama_genres_link['href'])
				if drama_genre_id:
					drama_genre_id = drama_genre_id.group(2)
				drama_info['genres'].append({'id':drama_genre_id,'name':drama_genres_link.text})

		for drama_hfs_elem in drama_hfs_elems:
			if drama_hfs_elem.text[:8] == 'Ratings:':
				if drama_hfs_elem.find('b').text != 'N/A':
					drama_stats['rating']['score'] = float(drama_hfs_elem.find('b').text)
				drama_stats['rating']['users_count'] = int(drama_hfs_elem.find('a').text.split(' ')[0].replace(',',''))

		for drama_random_header in drama_random_headers:
			if drama_random_header.text == 'Native title:':
				drama_info['titles']['japanese'] = drama_random_header.parent.contents[1]
			elif drama_random_header.text == 'Also Known as:':
				alt_titles = drama_random_header.parent.contents[1].split('; ')
				for alt_title in alt_titles:
					drama_info['titles']['alt_titles'].append(alt_title.strip())
			elif drama_random_header.text == 'Related Content':
				div_title_elems = drama_random_header.parent.find_all('div',{'class': 'title'})
				for div_title_elem in div_title_elems:
					if div_title_elem.text.strip() == '()':
						continue
					div_title_elem_anchor = div_title_elem.find('a')
					div_title_elem_name = div_title_elem_anchor.text.strip()
					div_title_elem_id = int(re.search('(/)(\d+)(-)',div_title_elem_anchor['href']).group(2))
					div_title_elem_association = div_title_elem_anchor.nextSibling.strip()[1:-1]
					drama_info['related_content'].append({'id': div_title_elem_id, 'name': div_title_elem_name, 'assoc': div_title_elem_association})
			elif drama_random_header.text == 'Country:':
				drama_details['country'] = drama_random_header.parent.contents[1].strip()
			elif drama_random_header.text == 'Type:':
				drama_details['type'] = drama_random_header.parent.contents[1].strip()
			elif drama_random_header.text == 'Release Date:' or drama_random_header.text == 'Aired:':
				if ' to ' in drama_random_header.parent.contents[1].strip():
					tmp_drama_split = drama_random_header.parent.contents[1].strip().split(' to ')
					drama_details['release_date']['start'] = tmp_drama_split[0]
					drama_details['release_date']['end'] = tmp_drama_split[1]
				else:
					drama_details['release_date']['start'] = drama_random_header.parent.contents[1].strip()
			elif drama_random_header.text == 'Episodes:':
				drama_details['episode_count'] = drama_random_header.parent.contents[1].strip()
			elif drama_random_header.text == 'Duration:':
				drama_details['duration'] = drama_random_header.parent.contents[1].strip()
			elif drama_random_header.text == 'Network:':
				drama_details['network'] = drama_random_header.parent.contents[1].strip()
				if len(drama_details['network']) == 0:
					drama_details['network'] = None
			elif drama_random_header.text == 'Ranked:':
				drama_details['rank'] = int(drama_random_header.parent.contents[1].strip()[1:])
			elif drama_random_header.text == 'Popularity:':
				drama_details['rank_popularity'] = int(drama_random_header.parent.contents[1].strip()[1:])
		if len(drama_info['synopsis']) <= 10:
			drama_info['synopsis'] = None
		if drama_page_bsoup.find('ul',{'class':'tvShowCastList'}):
			while True:
				try:
					drama_cast_resp = requests.get('http://mydramalist.com/' + str(current_drama_id) + '/cast', timeout = 5)
					if drama_cast_resp.status_code != 200:
						print('Drama cast request failed for some weird reason. Retrying...')
					else:
						break
				except:
					print('Cast request failed. Retrying...')
					time.sleep(3)

			drama_cast_bsoup = BeautifulSoup(drama_cast_resp.text, 'html.parser')
			drama_cast_details_elems = drama_cast_bsoup.find_all('li',{'class':'cast'})
			for drama_cast_details_elem in drama_cast_details_elems:
				drama_cast_temp_arr = {}
				drama_cast_temp_arr['thumb'] = drama_cast_details_elem.select('a.cover img')[0]['src']
				if drama_cast_temp_arr['thumb'] == 'http://i.mdldb.net/_t.jpg':
					drama_cast_temp_arr['thumb'] = None
				drama_cast_temp_arr['name'] = drama_cast_details_elem.find('a',{'class':'name'}).text.strip()
				if len(drama_cast_temp_arr['name']) == 0:
					drama_cast_temp_arr['name'] = None
				drama_cast_temp_arr['aka'] = drama_cast_details_elem.find('div',{'class':'aka'})
				if drama_cast_temp_arr['aka']:
					drama_cast_temp_arr['aka'] = drama_cast_temp_arr['aka'].text.strip()
				drama_cast_temp_arr['role'] = drama_cast_details_elem.find('div',{'class':'role'}).text.strip()
				drama_cast_temp_arr['id'] = drama_cast_details_elem.find('a',{'class':'name'})['href']
				drama_cast_temp_arr['id'] = re.search('(/)(\d+)(-)',drama_cast_temp_arr['id'])
				if drama_cast_temp_arr['id']:
					drama_cast_temp_arr['id'] = int(drama_cast_temp_arr['id'].group(2))
				drama_cast_members.append(drama_cast_temp_arr)

		drama_json = {'info': drama_info, 'stats': drama_stats, 'details': drama_details, 'cast_members': drama_cast_members}

		with open('MDL/' + str(current_drama_id) + '.json', 'w') as f:
			f.write(json.dumps(drama_json, ensure_ascii = True, sort_keys = True, indent = 4))
